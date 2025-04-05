from mininet.net import Mininet
from mininet.topo import SingleSwitchTopo
from mininet.node import RemoteController
from mininet.link import TCLink
import re
import time

def get_bandwidth(output):
    match = re.search(r'(\d+\.\d+)\s+Gbits/sec', output)
    return float(match.group(1)) if match else 0.0

def get_rtt(output):
    rtt_line = re.search(r'rtt min/avg/max/mdev = ([\d\.]+)/[\d\.]+/([\d\.]+)/', output)
    if rtt_line:
        return float(rtt_line.group(1)), float(rtt_line.group(2))
    return None, None

def measure_ptr(h1, h2, packet_count):
    h2.cmd('iperf -s -u -p 5001 &')
    time.sleep(1)
    start = time.time()
    h1.cmd(f'iperf -c {h2.IP()} -u -p 5001 -b 10M -l 1400 -t {packet_count//5}')  # Duration roughly proportional
    end = time.time()
    return round((end - start) * 1000, 2)  # in ms

def measure_rtt(h1, h2, count):
    output = h1.cmd(f'ping -c {count} {h2.IP()}')
    return get_rtt(output)

if __name__ == '__main__':
    net = Mininet(topo=SingleSwitchTopo(k=16), controller=RemoteController, link=TCLink)
    net.start()
    hosts = net.hosts

    min_bw = float('inf')
    min_pair = ()

    # Start iperf servers
    for h in hosts:
        h.cmd('iperf -s -p 5001 &')

    print("📶 Measuring Bandwidth between all host pairs...")
    for i in range(len(hosts)):
        for j in range(i+1, len(hosts)):
            h1, h2 = hosts[i], hosts[j]
            output = h1.cmd(f'iperf -c {h2.IP()} -p 5001 -t 3')
            bw = get_bandwidth(output)
            print(f'{h1.name} -> {h2.name}: {bw:.2f} Gbps')
            if bw < min_bw:
                min_bw = bw
                min_pair = (h1.name, h2.name)

    print(f'\n🔻 Minimum Bandwidth: {min_bw:.2f} Gbps between {min_pair[0]} and {min_pair[1]}')

    # Measure PTR and RTT for a fixed pair (e.g., h1 -> h2)
    h1, h2 = hosts[0], hosts[1]
    packet_counts = [5, 10, 20, 30, 50, 100]

    print("\n📦 Measuring Packet Transmission Rate (PTR):")
    for count in packet_counts:
        duration = measure_ptr(h1, h2, count)
        print(f'{count} packets: {duration} ms')

    print("\n⏱️ Measuring Round Trip Time (RTT):")
    for count in packet_counts:
        min_rtt, max_rtt = measure_rtt(h1, h2, count)
        print(f'{count} pings: Min RTT = {min_rtt} ms | Max RTT = {max_rtt} ms')

    net.stop()
