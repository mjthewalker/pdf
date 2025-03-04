
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController
from mininet.cli import CLI

class SDNTopo(Topo):
    def build(self):
        switch = self.addSwitch('s1')
        for h in range(1, 5):
            host = self.addHost(f'h{h}')
            self.addLink(host, switch)

if __name__ == '__main__':
    topo = SDNTopo()
    net = Mininet(topo=topo, controller=RemoteController)
    net.start()
    print("Testing connectivity...")
    net.pingAll()
    CLI(net)
    net.stop()
