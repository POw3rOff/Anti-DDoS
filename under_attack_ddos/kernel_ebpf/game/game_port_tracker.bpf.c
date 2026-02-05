#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>
#include "../common/maps.h"
#include "../common/events.h"

// Check if destination port is a monitored game port
// If so, emit stats aggressively

SEC("xdp")
int xdp_game_tracker(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) return XDP_PASS;
    if (eth->h_proto != bpf_htons(ETH_P_IP)) return XDP_PASS;

    struct iphdr *iph = (void *)(eth + 1);
    if ((void *)(iph + 1) > data_end) return XDP_PASS;

    __u16 dst_port = 0;

    if (iph->protocol == IPPROTO_TCP) {
        struct tcphdr *tcp = (void *)(iph + 1);
        if ((void *)(tcp + 1) > data_end) return XDP_PASS;
        dst_port = bpf_ntohs(tcp->dest);
    } else if (iph->protocol == IPPROTO_UDP) {
        struct udphdr *udp = (void *)(iph + 1);
        if ((void *)(udp + 1) > data_end) return XDP_PASS;
        dst_port = bpf_ntohs(udp->dest);
    } else {
        return XDP_PASS;
    }

    // Check if port is in game map
    __u32 *game_id = bpf_map_lookup_elem(&game_ports, &dst_port);
    if (game_id) {
        // It's a game packet.
        // In a real implementation, we would have complex logic here.
        // For prototype, we just count and randomly sample for 'Anomaly'

        __u32 src_ip = iph->saddr;
        // Re-using udp_counters for simplicity in this prototype,
        // normally would have specific game counters.

        // Random sampling (1 in 1000) to signal potential anomaly for analysis
        if (bpf_get_prandom_u32() % 1000 == 0) {
            struct detection_event_t *e;
            e = bpf_ringbuf_reserve(&event_ringbuf, sizeof(*e), 0);
            if (e) {
                e->src_ip = src_ip;
                e->pps = 0; // Unknown in this context
                e->event_type = EVENT_TYPE_GAME_ANOMALY;
                e->confidence = 50;
                e->dst_port = dst_port;
                bpf_ringbuf_submit(e, 0);
            }
        }
    }

    return XDP_PASS;
}

char LICENSE[] SEC("license") = "GPL";
