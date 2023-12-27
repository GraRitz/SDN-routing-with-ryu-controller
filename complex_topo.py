from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.link import TCLink


class Network:

    def run(self):

        # defining net
        net = Mininet(controller=RemoteController, link=TCLink)

        # adding hosts
        #each host has its own IP address and MAC address
        h1 = net.addHost("h1", ip="192.168.1.2", mac="00:00:00:00:00:01")
        h2 = net.addHost("h2", ip="192.168.1.3", mac="00:00:00:00:00:02")
        h3 = net.addHost("h3", ip="192.168.1.4", mac="00:00:00:00:00:03")
        h4 = net.addHost("h4", ip="192.168.1.5", mac="00:00:00:00:00:04")
        h5 = net.addHost("h5", ip="192.168.1.6", mac="00:00:00:00:00:05")
        h6 = net.addHost("h6", ip="192.168.1.7", mac="00:00:00:00:00:06")
        h7 = net.addHost("h7", ip="192.168.1.8", mac="00:00:00:00:00:07")
        h8 = net.addHost("h8", ip="192.168.1.9", mac="00:00:00:00:00:08")
        h9 = net.addHost("h9", ip="192.168.1.10", mac="00:00:00:00:00:09")
        h10 = net.addHost("h10", ip="192.168.1.11", mac="00:00:00:00:00:10")
        h11 = net.addHost("h11", ip="192.168.1.12", mac="00:00:00:00:00:11")
        h12 = net.addHost("h12", ip="192.168.1.13", mac="00:00:00:00:00:12")
        h13 = net.addHost("h13", ip="192.168.1.14", mac="00:00:00:00:00:13")
        h14 = net.addHost("h14", ip="192.168.1.15", mac="00:00:00:00:00:14")
        h15 = net.addHost("h15", ip="192.168.1.16", mac="00:00:00:00:00:15")
        h16 = net.addHost("h16", ip="192.168.1.17", mac="00:00:00:00:00:16")

        # adding switches
        s1 = net.addSwitch("s1")
        s2 = net.addSwitch("s2")
        s3 = net.addSwitch("s3")
        s4 = net.addSwitch("s4")
        s5 = net.addSwitch("s5")
        s6 = net.addSwitch("s6")
        s7 = net.addSwitch("s7")
        s8 = net.addSwitch("s8")
        s9 = net.addSwitch("s9")
        s10 = net.addSwitch("s10")
        s11 = net.addSwitch("s11")
        s12 = net.addSwitch("s12")
        s13 = net.addSwitch("s13")
        s14 = net.addSwitch("s14")
        s15 = net.addSwitch("s15")
        s16 = net.addSwitch("s16")
        

        # adding controller with IP address and port
        net.addController("C0", controller=RemoteController, ip="127.0.0.1", port=6633)

        # defining link options (used for delay and bandwidth detection on the links)
        hostlink = dict (bw = 1000, delay='0ms', cls=TCLink) #0 ms for links between hosts and their switches
        base_link = dict(bw = 1000, delay='4ms', cls=TCLink) #4 ms used for low congestion links
        mid_link = dict(bw = 570, delay='7ms', cls=TCLink) #7 ms used for mid congestion links
        busy_link = dict(bw = 400, delay='10ms', cls=TCLink) #10 ms used for high congestion links

        # ADDING LINKS 
        
        #s1
        net.addLink(h1, s1, **hostlink)
        net.addLink(s1, s2, **base_link)
        net.addLink(s1, s3, **base_link)
        net.addLink(s1, s12, **busy_link)
  
        #s2
        net.addLink(h2, s2, **hostlink)
        net.addLink(s2, s3, **base_link)
        net.addLink(s2, s4, **base_link)
        net.addLink(s2, s5, **base_link)
        net.addLink(s2, s14, **mid_link)

        #s3
        net.addLink(h3, s3, **hostlink)
        net.addLink(s3, s5, **base_link)
        net.addLink(s3, s10, **busy_link)
        net.addLink(s3, s12, **busy_link)

        #s4
        net.addLink(h4, s4, **hostlink)
        net.addLink(s4, s5, **base_link)
        net.addLink(s4, s6, **mid_link)
        net.addLink(s4, s14, **mid_link)
        net.addLink(s4, s15, **base_link)

        #s5
        net.addLink(h5, s5, **hostlink)
        net.addLink(s5, s6, **mid_link)
        net.addLink(s5, s7, **mid_link)
        net.addLink(s5, s10, **busy_link)

        #s6
        net.addLink(h6, s6, **hostlink)
        net.addLink(s6, s7, **busy_link)
        net.addLink(s6, s8, **busy_link)
        net.addLink(s6, s15, **base_link)

        #s7
        net.addLink(h7, s7, **hostlink)
        net.addLink(s7, s8, **busy_link)
        net.addLink(s7, s9, **mid_link)

        #s8
        net.addLink(h8, s8, **hostlink)
        net.addLink(s8, s9, **mid_link)

        #s9
        net.addLink(h9, s9, **hostlink)
        net.addLink(s9, s10, **base_link)
        net.addLink(s9, s11, **base_link)
  
        #s10
        net.addLink(h10, s10, **hostlink)
        net.addLink(s10, s11, **base_link)
        net.addLink(s10, s12, **busy_link)

        #s11
        net.addLink(h11, s11, **hostlink)
        net.addLink(s11, s13, **mid_link)

        #s12
        net.addLink(h12, s12, **hostlink)
        net.addLink(s12, s13, **mid_link)

        #s13
        net.addLink(h13, s13, **hostlink)

        #s14
        net.addLink(h14, s14, **hostlink)
        net.addLink(s14, s15, **base_link)
        net.addLink(s14, s16, **base_link)

        #s15
        net.addLink(h15, s15, **hostlink)
        net.addLink(s15, s16, **base_link)

        #s16
        net.addLink(h16, s16, **hostlink)

        # running network
        net.start()
        
        # starting cli
        CLI(net)

        # stopping network
        net.stop()


if __name__ == "__main__":
    network = Network()
    network.run()
