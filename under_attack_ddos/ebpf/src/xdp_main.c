#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <linux/in.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>
#include "common_maps.h"

SEC("xdp")
int xdp_dispatcher(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    /* Only handle IPv4 for now */
    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return XDP_PASS;

    struct iphdr *iph = data + sizeof(struct ethhdr);
    if ((void *)(iph + 1) > data_end)
        return XDP_PASS;

    /* 1. Blacklist Check (LPM Trie) */
    struct {
        __u32 prefixlen;
        __u32 ipv4_addr;
    } key = {32, iph->saddr};

    __u32 *blocked = bpf_map_lookup_elem(&map_blacklist, &key);
    if (blocked) {
        return XDP_DROP;
    }

    /* 2. Global Telemetry (L3) */
    __u32 proto_idx = PROTO_OTHER;
    if (iph->protocol == IPPROTO_TCP) proto_idx = PROTO_TCP;
    else if (iph->protocol == IPPROTO_UDP) proto_idx = PROTO_UDP;
    else if (iph->protocol == IPPROTO_ICMP) proto_idx = PROTO_ICMP;

    struct stats_val *stats = bpf_map_lookup_elem(&map_l3_stats, &proto_idx);
    if (stats) {
        stats->rx_packets++;
        stats->rx_bytes += (data_end - data);
    }

    /* 3. Per-Source Telemetry (Host Tracking) */
    struct stats_val *src_stats = bpf_map_lookup_elem(&map_source_stats, &iph->saddr);
    if (!src_stats) {
        struct stats_val initial = {1, (data_end - data)};
        bpf_map_update_elem(&map_source_stats, &iph->saddr, &initial, BPF_NOEXIST);
    } else {
        src_stats->rx_packets++;
        src_stats->rx_bytes += (data_end - data);
    }

    /* 4. Layer 4 Specifics (SYN Tracking) */
    if (iph->protocol == IPPROTO_TCP) {
        struct tcphdr *tcp = (void *)iph + (iph->ihl * 4);
        if ((void *)(tcp + 1) <= data_end) {
            if (tcp->syn && !tcp->ack) {
                __u64 *syn_count = bpf_map_lookup_elem(&map_syn_stats, &iph->saddr);
                if (!syn_count) {
                    __u64 initial = 1;
                    bpf_map_update_elem(&map_syn_stats, &iph->saddr, &initial, BPF_NOEXIST);
                } else {
                    __sync_fetch_and_add(syn_count, 1);
                }
            }
        }
    }

    /* 5. Active Mitigation Toggle */
    __u32 config_idx = 0;
    struct config_val *conf = bpf_map_lookup_elem(&map_config, &config_idx);
    if (conf && conf->mode == 1) {
        /* If in PROTECT mode, we could enforce stricter filters here */
    }

    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
 Boris? No, Antigravity.
