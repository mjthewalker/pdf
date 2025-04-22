from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController
from mininet.cli import CLI
import time
import re
import json


class SingleTopo(Topo):
    def build(self):
        switch = self.addSwitch('s1')
        for h in range(1, 17):
            host = self.addHost(f'h{h}')
            self.addLink(host, switch)
class LinearTopo(Topo):
    def build(self):
        prev = None
        for i in range(1,17):
            host = self.addHost(f'h{i}')
            switch = self.addSwitch(f's{i}')
            self.addLink(host,switch)
            if prev:
                self.addLink(switch,prev)
            prev=switch
class TreeTopo(Topo):
    def build(self):
        core_switch = self.addSwitch('s1')
        agg_switches = []
        for i in range(4):
            agg = self.addSwitch(f's{i+2}')
            agg_switches.append(agg)
            self.addLink(core_switch,agg)
        hId = 1
        for agg in agg_switches:
            for _ in range(4):
                host = self.addHost(f'h{hId}')
                self.addLink(host,agg)
                hId += 1
def get_rtt(output):
    rtt_line = re.search(r'rtt min/avg/max/mdev = ([\d\.]+)/[\d\.]+/([\d\.]+)/', output)
    if rtt_line:
        return float(rtt_line.group(1)), float(rtt_line.group(2))
    return None, None
def measure_ptr(h1, h2, packet_count):
    h2.cmd('iperf -s -u -p 5001 &')
    time.sleep(1)
    start = time.time()
    h1.cmd(f'iperf -c {h2.IP()} -u -p 5001 -b 10M -l 1400 -t {packet_count//5}') 
    end = time.time()
    return round((end - start) * 1000, 2) 

def measure_rtt(h1, h2, count):
    output = h1.cmd(f'ping -c {count} {h2.IP()}')
    return get_rtt(output)
    
def measure_bandwidth(net):
    hosts = [net.get(f'h{i}') for i in range(1, 17)]
    bandwidths = []
    ptr_results = []
    rtt_min_list = []
    rtt_max_list = []
    
    for i in range(len(hosts)):
        for j in range(i + 1, len(hosts)):
            h1, h2 = hosts[i], hosts[j]
            h2.cmd('iperf -s &')
            output = h1.cmd(f'iperf -c {h2.IP()} -n 2G')
            h2.cmd('kill %iperf')
            match = re.search(r'(\d+\.?\d*)\s+(Gbits|Mbits)/sec', output)
            if match:
                bw = float(match.group(1))
                if match.group(2) == "Mbits":
                    bw /= 1000
                bandwidths.append(bw)

    h1, h2 = hosts[0], hosts[15]
    packet_counts = [5, 10, 20, 30, 50, 100]
    
    for count in packet_counts:
        ptr = measure_ptr(h1, h2, count)
        ptr_results.append(ptr)
        
        min_rtt, max_rtt = measure_rtt(h1, h2, count)
        rtt_min_list.append(min_rtt)
        rtt_max_list.append(max_rtt)
    
    return {
        "max_bandwidth": max(bandwidths) if bandwidths else 0,
        "min_bandwidth": min(bandwidths) if bandwidths else 0,
        "ptr": ptr_results,
        "rtt_min": rtt_min_list,
        "rtt_max": rtt_max_list
    }

      
                
                

def main():
    print("\n Choose a Mininet Topology:")
    print("1. Single Topology")
    print("2. Linear Topology")
    print("3. Tree Topology")
    choice = input("Enter your choice(1/2/3): ").strip()

    if choice == '1':
        topo = SingleTopo()
        topo_name = "Single Topology"
    elif choice == '2':
        topo = LinearTopo()
        topo_name = "Linear Topology"
    elif choice == '3':
        topo = TreeTopo()
        topo_name = "Tree Topology"
    else:
        print("Invalid choice! Exiting.")
        return

    net = Mininet(topo=topo, controller=RemoteController)
    net.start()
    print("\n Network is established")

    results = measure_bandwidth(net)
    results['topology'] = topo_name

    with open(f"{topo_name.replace(' ', '_').lower()}_results.json", "w") as f:
        json.dump(results, f, indent=2)

    CLI(net)
    net.stop()
if _name_ == '_main_':
    main()
