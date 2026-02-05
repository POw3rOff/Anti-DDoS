#ifndef __XDP_COMMON_H__
#define __XDP_COMMON_H__

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/in.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

// Action Codes
#define ACTION_PASS 0
#define ACTION_DROP 1

// Helper to check map limit safety
#ifndef MAX_BLOCKLIST_ENTRIES
#define MAX_BLOCKLIST_ENTRIES 100000
#endif

// Structs for maps
struct blocklist_key {
    __u32 ip;
};

struct blocklist_value {
    __u32 action;
    __u64 timestamp; // When added, for expiration logic (userspace cleanup)
};

#endif // __XDP_COMMON_H__
