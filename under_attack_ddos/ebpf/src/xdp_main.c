#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/in.h>
#include <bpf/bpf_helpers.h>
#include "common_maps.h"

SEC("xdp")
int xdp_dispatcher(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return XDP_PASS;

    struct iphdr *iph = data + sizeof(struct ethhdr);
    if ((void *)(iph + 1) > data_end)
        return XDP_PASS;

    /* 1. Blacklist Check */
    struct {
        __u32 prefixlen;
        __u32 ipv4_addr;
    } key = {32, iph->saddr};

    __u32 *blocked = bpf_map_lookup_elem(&map_blacklist, &key);
    if (blocked) {
        return XDP_DROP;
    }

    /* 2. Telemetry / Stats */
    __u32 proto_idx = PROTO_OTHER;
    if (iph->protocol == IPPROTO_TCP) proto_idx = PROTO_TCP;
    else if (iph->protocol == IPPROTO_UDP) proto_idx = PROTO_UDP;
    else if (iph->protocol == IPPROTO_ICMP) proto_idx = PROTO_ICMP;

    struct stats_val *stats = bpf_map_lookup_elem(&map_l3_stats, &proto_idx);
    if (stats) {
        stats->rx_packets++;
        stats->rx_bytes += (data_end - data);
    }

    /* 3. Per-Source Stats */
    struct stats_val *src_stats = bpf_map_lookup_elem(&map_source_stats, &iph->saddr);
    if (!src_stats) {
        struct stats_val initial = {1, (data_end - data)};
        bpf_map_update_elem(&map_source_stats, &iph->saddr, &initial, BPF_ANY);
    } else {
        src_stats->rx_packets++;
        src_stats->rx_bytes += (data_end - data);
    }

    /* 4. Layer 4 SYN Tracking */
    if (iph->protocol == IPPROTO_TCP) {
        struct tcphdr *tcp = (void *)iph + (iph->ihl * 4);
        if ((void *)(tcp + 1) <= data_end) {
            if (tcp->syn && !tcp->ack) {
                __u64 *syn_count = bpf_map_lookup_elem(&map_syn_stats, &iph->saddr);
                if (!syn_count) {
                    __u64 initial = 1;
                    bpf_map_update_elem(&map_syn_stats, &iph->saddr, &initial, BPF_ANY);
                } else {
                    (*syn_count)++;
                }
            }
        }
    }

    /* 5. Global Config Check (Optional active mitigation) */
    __u32 index = 0;
    struct config_val *conf = bpf_map_lookup_elem(&map_config, &index);
    if (conf && conf->mode == 1) {
        /* Future: Implement more complex XDP logic here (e.g. proto filtering) */
    }

    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
