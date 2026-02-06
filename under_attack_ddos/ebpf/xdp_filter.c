
#include <linux/if_ether.h>
#include <linux/in.h>
#include <linux/ip.h>
#include <uapi/linux/bpf.h>


// BPF Map for blocked IPs (Key: u32 IP, Value: u32 packet_count)
BPF_TABLE("hash", u32, u32, blacklist, 10240);

// BPF Map for stats (Key: 0=dropped, 1=passed, Value: count)
BPF_TABLE("array", u32, long, stats, 2);

int xdp_filter(struct xdp_md *ctx) {
  void *data = (void *)(long)ctx->data;
  void *data_end = (void *)(long)ctx->data_end;

  struct ethhdr *eth = data;
  if ((void *)(eth + 1) > data_end)
    return XDP_PASS;

  // Only handle IPv4
  if (eth->h_proto != htons(ETH_P_IP))
    return XDP_PASS;

  struct iphdr *ip = (void *)(eth + 1);
  if ((void *)(ip + 1) > data_end)
    return XDP_PASS;

  u32 src_ip = ip->saddr;

  // Check if IP is in blacklist
  u32 *count = blacklist.lookup(&src_ip);
  if (count) {
    // Increment drop counter for this IP
    lock_xadd(count, 1);

    // Update global drop stats
    u32 drop_key = 0;
    long *dropped = stats.lookup(&drop_key);
    if (dropped)
      lock_xadd(dropped, 1);

    return XDP_DROP;
  }

  // Update global pass stats
  u32 pass_key = 1;
  long *passed = stats.lookup(&pass_key);
  if (passed)
    lock_xadd(passed, 1);

  return XDP_PASS;
}
