#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/icmp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>
#include "../common/maps.h"
#include "../common/events.h"

// Fallback default
#define DEFAULT_ICMP_THRESHOLD 1000

static __always_inline __u32 get_threshold(__u32 idx, __u32 default_val) {
    __u32 *val = bpf_map_lookup_elem(&config_map, &idx);
    if (val && *val > 0) return *val;
    return default_val;
}

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

        __u32 src_ip = iph->saddr;
        __u64 *count = bpf_map_lookup_elem(&src_ip_counters, &src_ip);

        if (count) {
            __sync_fetch_and_add(count, 1);

            __u32 limit = get_threshold(CONFIG_IDX_ICMP, DEFAULT_ICMP_THRESHOLD);

            if (*count > limit && (*count % 100 == 0)) {
                struct detection_event_t *e;
                e = bpf_ringbuf_reserve(&event_ringbuf, sizeof(*e), 0);
                if (e) {
                    e->src_ip = src_ip;
                    e->pps = *count;
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

    return XDP_PASS;
}

char LICENSE[] SEC("license") = "GPL";
