#ifndef __MAPS_H__
#define __MAPS_H__

#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

#define MAX_TRACKED_IPS 10000
#define MAX_GAME_PORTS 64

// 1. Packet Counters (Source IP -> PPS)
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, MAX_TRACKED_IPS);
    __type(key, __u32);   // Source IP
    __type(value, __u64); // Packet Count
} src_ip_counters SEC(".maps");

// 2. SYN Counters (Source IP -> SYN PPS)
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, MAX_TRACKED_IPS);
    __type(key, __u32);
    __type(value, __u64);
} tcp_syn_counters SEC(".maps");

// 3. UDP Counters (Source IP -> UDP PPS)
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, MAX_TRACKED_IPS);
    __type(key, __u32);
    __type(value, __u64);
} udp_counters SEC(".maps");

// 4. Events Ring Buffer
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024); // 256KB
} event_ringbuf SEC(".maps");

// 5. Game Port Config Map (Port -> Protocol Type)
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_GAME_PORTS);
    __type(key, __u16); // Port
    __type(value, __u32); // Protocol/Game ID
} game_ports SEC(".maps");

// 6. Dynamic Configuration Map (Array Index -> Value)
// Index 0: ICMP PPS Threshold
// Index 1: SYN PPS Threshold
// Index 2: UDP PPS Threshold
// Index 3: Game PPS Threshold
#define CONFIG_IDX_ICMP 0
#define CONFIG_IDX_SYN  1
#define CONFIG_IDX_UDP  2
#define CONFIG_IDX_GAME 3

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 16);
    __type(key, __u32);
    __type(value, __u32);
} config_map SEC(".maps");

#endif // __MAPS_H__
