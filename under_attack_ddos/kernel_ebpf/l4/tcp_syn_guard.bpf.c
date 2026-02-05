#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>
#include "../common/maps.h"
#include "../common/events.h"

#define SYN_PPS_THRESHOLD 500

SEC("xdp")
int xdp_syn_guard(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) return XDP_PASS;

    if (eth->h_proto != bpf_htons(ETH_P_IP)) return XDP_PASS;

    struct iphdr *iph = (void *)(eth + 1);
    if ((void *)(iph + 1) > data_end) return XDP_PASS;

    if (iph->protocol == IPPROTO_TCP) {
        struct tcphdr *tcp = (void *)(iph + 1);
        if ((void *)(tcp + 1) > data_end) return XDP_PASS;

        // Check for SYN flag (and no ACK)
        if (tcp->syn && !tcp->ack) {
            __u32 src_ip = iph->saddr;
            __u64 *count = bpf_map_lookup_elem(&tcp_syn_counters, &src_ip);

            if (count) {
                __sync_fetch_and_add(count, 1);

                if (*count > SYN_PPS_THRESHOLD && (*count % 50 == 0)) {
                    struct detection_event_t *e;
                    e = bpf_ringbuf_reserve(&event_ringbuf, sizeof(*e), 0);
                    if (e) {
                        e->src_ip = src_ip;
                        e->pps = *count;
                        e->event_type = EVENT_TYPE_SYN_FLOOD;
                        e->confidence = 90;
                        e->dst_port = bpf_ntohs(tcp->dest);
                        bpf_ringbuf_submit(e, 0);
                    }
                }
            } else {
                __u64 init_val = 1;
                bpf_map_update_elem(&tcp_syn_counters, &src_ip, &init_val, BPF_NOEXIST);
            }
        }
    }

    return XDP_PASS;
}

char LICENSE[] SEC("license") = "GPL";
