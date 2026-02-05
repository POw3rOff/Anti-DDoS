#include "xdp_common.h"
#include "maps/xdp_blocklist_map.h"

// Forward declarations for modular logic (could be separate files linked,
// but including directly is simpler for this prototype structure)
// In a real build system, these might be separate objs.
// For now, we implement the core logic here to avoid complex Makefiles.

static __always_inline int check_blocklist(__u32 src_ip) {
    struct blocklist_key key = { .ip = src_ip };
    struct blocklist_value *val;

    val = bpf_map_lookup_elem(&blocklist_map, &key);
    if (val) {
        if (val->action == ACTION_DROP) {
            return XDP_DROP;
        }
    }
    return XDP_PASS;
}

static __always_inline void update_stats(int action) {
    __u32 key = action; // 0 or 1
    __u64 *count = bpf_map_lookup_elem(&xdp_stats_map, &key);
    if (count) {
        __sync_fetch_and_add(count, 1);
    }
}

SEC("xdp")
int xdp_prog_main(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;
    struct ethhdr *eth = data;

    // Bounds check
    if ((void *)(eth + 1) > data_end) return XDP_PASS;

    // Check IP
    if (eth->h_proto != bpf_htons(ETH_P_IP)) return XDP_PASS;

    struct iphdr *iph = (void *)(eth + 1);
    if ((void *)(iph + 1) > data_end) return XDP_PASS;

    // 1. Blocklist Check (Highest Priority)
    int action = check_blocklist(iph->saddr);

    // 2. Protocol Specific Checks (if not already dropped)
    // (Here we could call UDP/Game specific logic if we wanted filtering
    // rules beyond simple IP blocking, but the requirement focuses on
    // blocklist enforcement)

    // Update Stats
    update_stats(action);

    return action;
}

char LICENSE[] SEC("license") = "GPL";
