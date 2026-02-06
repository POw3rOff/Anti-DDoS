#ifndef __COMMON_MAPS_H
#define __COMMON_MAPS_H

#include <linux/types.h>

/* Protocol types for stats */
enum proto_type {
    PROTO_TCP = 0,
    PROTO_UDP,
    PROTO_ICMP,
    PROTO_OTHER,
    PROTO_MAX
};

/* Stats structure */
struct stats_val {
    __u64 rx_packets;
    __u64 rx_bytes;
};

/* Config structure */
struct config_val {
    __u32 mode;       /* 0: NORMAL, 1: PROTECT */
    __u32 log_level;
};

/* 
 * BPF Map Definitions
 */

/* L3 Stats: Per-CPU array of stats_val */
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, PROTO_MAX);
    __type(key, __u32);
    __type(value, struct stats_val);
} map_l3_stats SEC(".maps");

/* Per-Source IP Stats (L3/L4 Flood detection) */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 65536);
    __type(key, __u32);            /* Source IPv4 */
    __type(value, struct stats_val);
} map_source_stats SEC(".maps");

/* Blacklist: LPM Trie for IP blocking */
struct {
    __uint(type, BPF_MAP_TYPE_LPM_TRIE);
    __uint(max_entries, 16384);
    __type(key, struct bpf_lpm_trie_key); 
    __type(value, __u32);                 
    __uint(map_flags, BPF_F_NO_PREALLOC);
} map_blacklist SEC(".maps");

/* Per-Source SYN Stats (L4 SYN Flood) */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 65536);
    __type(key, __u32);            /* Source IPv4 */
    __type(value, __u64);          /* SYN count */
} map_syn_stats SEC(".maps");

/* Global Configuration */
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, struct config_val);
} map_config SEC(".maps");

#endif
