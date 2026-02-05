#ifndef __XDP_BLOCKLIST_MAP_H__
#define __XDP_BLOCKLIST_MAP_H__

#include "../xdp_common.h"

// The Blocklist Map
// Shared between all XDP programs and user space
// Key: Source IP (u32)
// Value: Action (u32) + Timestamp (u64)

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_BLOCKLIST_ENTRIES);
    __type(key, struct blocklist_key);
    __type(value, struct blocklist_value);
} blocklist_map SEC(".maps");

// Global Stats Map (Drops/Passes)
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 2); // 0=Pass, 1=Drop
    __type(key, __u32);
    __type(value, __u64);
} xdp_stats_map SEC(".maps");

#endif // __XDP_BLOCKLIST_MAP_H__
