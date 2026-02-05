#ifndef __MAPS_H__
#define __MAPS_H__

#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

// Define map structure helpers for libbpf (BTF-defined maps)
// Note: This requires a modern environment with BTF support.
// If compiling on older systems, legacy map definitions might be needed.

#define MAX_TRACKED_IPS 10000
#define MAX_GAME_PORTS 64

// 1. Packet Counters (Source IP -> PPS)
// LRU Hash ensures we don't OOM, dropping least used entries.
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, MAX_TRACKED_IPS);
    __type(key, __u32);   // Source IP
    __type(value, __u64); // Packet Count (reset periodically by userspace or timestamp bucket)
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
// High-performance queue for sending structs to user space
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024); // 256KB
} event_ringbuf SEC(".maps");

// 5. Game Port Config Map (Port -> Protocol Type)
// User space populates this to tell kernel which ports to watch
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_GAME_PORTS);
    __type(key, __u16); // Port
    __type(value, __u32); // Protocol/Game ID
} game_ports SEC(".maps");

#endif // __MAPS_H__
