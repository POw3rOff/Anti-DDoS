#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/icmp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>
#include "../common/maps.h"
#include "../common/events.h"

// Thresholds (Simulated consts, real world would use map for config)
#define ICMP_PPS_THRESHOLD 1000

SEC("xdp")
int xdp_icmp_guard(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) return XDP_PASS;

    if (eth->h_proto != bpf_htons(ETH_P_IP)) return XDP_PASS;

    struct iphdr *iph = (void *)(eth + 1);
    if ((void *)(iph + 1) > data_end) return XDP_PASS;

    if (iph->protocol == IPPROTO_ICMP) {
        struct icmphdr *icmp = (void *)(iph + 1);
        if ((void *)(icmp + 1) > data_end) return XDP_PASS;

        // Count packets per Source IP
        __u32 src_ip = iph->saddr;
        __u64 *count = bpf_map_lookup_elem(&src_ip_counters, &src_ip);

        if (count) {
            __sync_fetch_and_add(count, 1);

            // Sampling / Throttling events
            // Only emit event every 100 packets after threshold
            if (*count > ICMP_PPS_THRESHOLD && (*count % 100 == 0)) {
                struct detection_event_t *e;
                e = bpf_ringbuf_reserve(&event_ringbuf, sizeof(*e), 0);
                if (e) {
                    e->src_ip = src_ip;
                    e->pps = *count; // Approximation
                    e->event_type = EVENT_TYPE_ICMP_FLOOD;
                    e->confidence = 80;
                    e->dst_port = 0;
                    bpf_ringbuf_submit(e, 0);
                }
            }
        } else {
            __u64 init_val = 1;
            bpf_map_update_elem(&src_ip_counters, &src_ip, &init_val, BPF_NOEXIST);
        }
    }

    return XDP_PASS; // Always pass, decision is advisory
}

char LICENSE[] SEC("license") = "GPL";
