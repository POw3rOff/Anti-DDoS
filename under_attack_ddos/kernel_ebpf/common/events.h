#ifndef __EVENTS_H__
#define __EVENTS_H__

// Event Types
enum event_type {
    EVENT_TYPE_SYN_FLOOD = 1,
    EVENT_TYPE_UDP_FLOOD = 2,
    EVENT_TYPE_ICMP_FLOOD = 3,
    EVENT_TYPE_GAME_ANOMALY = 4
};

// Structure of events sent to user space
struct detection_event_t {
    __u32 src_ip;
    __u32 pps;
    __u32 event_type;
    __u32 confidence; // 0-100
    __u16 dst_port;
    __u16 padding;
};

#endif // __EVENTS_H__
