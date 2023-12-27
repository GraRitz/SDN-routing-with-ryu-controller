from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import arp
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv6,ipv4
from ryu.topology import event
from ryu.ofproto.ofproto_v1_2 import OFPG_ANY

from collections import defaultdict

import random, time

idle_time = 3000


class ProjectController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ProjectController, self).__init__(*args, **kwargs)
        self.topology_api_app = self
        self.datapath_list = {}
        self.arp_table = {}
        self.switches = []
        self.hosts = {}
        self.multipath_group_ids = {}
        self.group_ids = []
        self.adjacency = defaultdict(lambda:defaultdict(lambda:None))
        self.switches_count = 0
        self.links = []
        self.en_clear_flow_entry = False
        self.datapaths = {}
        self.disable_packet_in = False
        self.pkt_count=0


    def get_path (self, src, dst):
        # executing Dijkstra's algorithm
        #The shortest path will be obtained by considering
        #the path having the lowest total delay
        print("Delay-based shortest path research using Dijkstra's algorithm.")
        print("The source node is", src,"and the destination node is", dst)
    
        # defining dictionaries for saving each node's distance and its previous node in the path from first node to that node
        distance = {}
        previous = {}

        # setting initial distance of every node to infinity
        for dpid in self.switches:
            distance[dpid] = float('Inf')
            previous[dpid] = None

        # setting distance of the source to 0
        distance[src] = 0

        # creating a set of all nodes
        Q = set(self.switches)

        # checking for all undiscovered nodes whether there is a path that goes 
        # through them to their adjacent nodes which will make its adjacent nodes closer to src
        while len(Q) > 0:
            # getting the closest node to src among undiscovered nodes
            u = self.minimum_distance(distance, Q)
            # removing the node from Q
            Q.remove(u)
            # calculate minimum distance for all adjacent nodes to u
            for p in self.switches:
                # if u and other switches are adjacent
                if self.adjacency[u][p] != None:
                    w = self.get_link_cost(u, p) #gets the cost of the link in terms of delay 
                    #print("Link from", u,"to", p,"delay is", w, "ms")
                    # if the path via u to p has lower cost then make the cost equal to this new path's cost
                    if distance[u] + w < distance[p]:
                        distance[p] = distance[u] + w
                        previous[p] = u

        # creating a list of switches between src and dst which are in the shortest path obtained by Dijkstra's algorithm reversely
        r = []
        p = dst
        r.append(p)
        # set q to the last node before dst 
        q = previous[p]
        while q is not None:
            if q == src:
                r.append(q)
                break
            p = q
            r.append(p)
            q = previous[p]

        # reversing r as it was from dst to src
        r.reverse()

        # setting path 
        if src == dst:
            return[src] #the dst is in the src node
        else:
            path=r

        return path #the final ordered path

    # getting the node with lowest distance in Q
    def minimum_distance(self, distance, Q):
        min = float('Inf')
        node = 0
        for v in Q:
            if distance[v] < min:
                min = distance[v]
                node = v
        return node

    def get_link_cost(self, s1, s2): #Link cost between two generic switches s1 and s2

        if (self.switches_count<10): #used to understand how complex the network is 
            factor = 2
        else:
            factor = 4
        
        delay = float(0)
        value = float((s1+s2)/factor) #index evaluating depending on the scaling factor
        
        if(value < 2.5 or value > 6.9):
            delay = 4
        elif(value > 4.5 and value <5.5):
            delay = 4
        elif(value > 3 and value <4):
            delay = 10
        elif(value >5.4 and value <6):
            delay = 10
        else:
            delay= 7
        
        return delay #elaborated delay between s1 and s2
        

    def get_path_cost(self, path): #total cost of the path 
        cost = 0
        for i in range(len(path) - 1):
            cost += self.get_link_cost(path[i], path[i+1])
        return cost

    def generate_openflow_gid(self): #generate a random OpenFlow group ID
        
        n = random.randint(0, 2**32)
        while n in self.group_ids:
            n = random.randint(0, 2**32)
        return n

    def add_ports_to_path(self, path, dst, first_port, last_port): #Add the connection ports to the path
        
        p = []
        in_port = first_port
        for s1, s2 in zip(path[:-1], path[1:]):
            out_port = self.adjacency[s1][s2]
            p.append((s1, in_port, out_port))
            in_port = self.adjacency[s2][s1]
        p.append((dst, in_port, last_port))
        return p


    def install_path(self, src, first_port, dst, last_port, ip_src, ip_dst): #This installs the path in terms of openflow rules 
        computation_start = time.time()
        path = self.get_path(src, dst)
        pw = self.get_path_cost(path)
        print ("Shortest path is", path, "with delay", pw, "ms.")
        path_with_ports = self.add_ports_to_path(path, dst, first_port, last_port)


        for node in path_with_ports:

            dp = self.datapath_list[int(node[0])]
            ofp = dp.ofproto
            ofp_parser = dp.ofproto_parser

            ports = defaultdict(list)
            actions = []

            
            in_port = node[1]
            out_port = node[2]
            if (out_port, pw) not in ports[in_port]:
                ports[in_port].append((out_port, pw))
                

            for in_port in ports:

                match_ip = ofp_parser.OFPMatch(
                    eth_type=0x0800, 
                    ipv4_src=ip_src, 
                    ipv4_dst=ip_dst
                )
                match_arp = ofp_parser.OFPMatch(
                    eth_type=0x0806, 
                    arp_spa=ip_src, 
                    arp_tpa=ip_dst
                )

                out_ports = ports[in_port]

                if len(out_ports) > 1:
                    group_id = None
                    group_new = False

                    if (node, src, dst) not in self.multipath_group_ids:
                        group_new = True
                        self.multipath_group_ids[
                            node, src, dst] = self.generate_openflow_gid()
                    group_id = self.multipath_group_ids[node, src, dst]

                    buckets = []
                    for port, weight in out_ports:
                        bucket_weight = int(round((1 - weight/pw) * 10))
                        bucket_action = [ofp_parser.OFPActionOutput(port)]
                        buckets.append(
                            ofp_parser.OFPBucket(
                                weight=bucket_weight,
                                watch_port=port,
                                watch_group=ofp.OFPG_ANY,
                                actions=bucket_action
                            )
                        )

                    if group_new:
                        req = ofp_parser.OFPGroupMod(
                            dp, ofp.OFPGC_ADD, ofp.OFPGT_SELECT, group_id,
                            buckets
                        )
                        dp.send_msg(req)
                        
                    else:
                        req = ofp_parser.OFPGroupMod(
                            dp, ofp.OFPGC_MODIFY, ofp.OFPGT_SELECT,
                            group_id, buckets)
                        dp.send_msg(req)

                    actions = [ofp_parser.OFPActionGroup(group_id)]
                    self.en_clear_flow_entry = True

                    self.add_flow(dp, 32768, match_ip, actions)
                    self.add_flow(dp, 1, match_arp, actions)

                elif len(out_ports) == 1:
                    actions = [ofp_parser.OFPActionOutput(out_ports[0][0])]
                    self.en_clear_flow_entry = True

                    self.add_flow(dp, 32768, match_ip, actions)
                    self.add_flow(dp, 1, match_arp, actions)
        print ("Path installation from", src, "to", dst, "finished.")
        exec_time=round((time.time() - computation_start)*1000, 2)
        print ("Total execution time:",exec_time,"ms.")
        print("The total control packet amount is:", self.pkt_count)
        print("")
        self.pkt_count=0
        return path_with_ports[0][1]

    def add_flow(self, datapath, priority, match, actions, buffer_id=None): #Add the flow in the openflow table

        ofproto = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        inst = [ofp_parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            if(self.en_clear_flow_entry):
                mod = ofp_parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,idle_timeout=idle_time,
                                    instructions=inst)
            else:
                mod = ofp_parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            if(self.en_clear_flow_entry):
                mod = ofp_parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, idle_timeout=idle_time,
                                    instructions=inst)
            else:
                mod = ofp_parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match,instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER) #General switch behaviour definition
    def _switch_features_handler(self, ev): 
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        match = ofp_parser.OFPMatch()
        actions = [ofp_parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        self.match_miss_flow_entry = match
        self.actions_miss_flow_entry = actions

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER) #Behaviour when a packet arrives in a generic switch 
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        ofp_parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        arp_pkt = pkt.get_protocol(arp.arp)

        # avoid broadcast from LLDP
        if eth.ethertype == 35020:
            return
        if self.disable_packet_in :
            return

        #this avoids ipv4 duplicates
        if pkt.get_protocol(ipv4.ipv4):  
            match = ofp_parser.OFPMatch(eth_type=eth.ethertype)
            src_ip = pkt.get_protocol(ipv4.ipv4).src
            dst_ip = pkt.get_protocol(ipv4.ipv4).dst
            
            dst = eth.dst       
            src = eth.src
            dpid = datapath.id
            self.arp_table[src_ip] = src
            h1 = self.hosts[src]        
            h2 = self.hosts[dst]   
            out_port = self.install_path(h1[0], h1[1], h2[0], h2[1], src_ip, dst_ip)
            out_port = self.install_path(h2[0], h2[1], h1[0], h1[1], dst_ip, src_ip)
            print("")  
            return

        if pkt.get_protocol(ipv6.ipv6):  # Drop the IPV6 Packets.
            match = ofp_parser.OFPMatch(eth_type=eth.ethertype)
            actions = []
            self.en_clear_flow_entry = False
            self.add_flow(datapath, 1, match, actions)
            return None

        dst = eth.dst
        src = eth.src
        dpid = datapath.id

        if src not in self.hosts:
            self.hosts[src] = (dpid, in_port)

        out_port = ofproto.OFPP_FLOOD

        if arp_pkt:
            self.pkt_count+=1
            src_ip = arp_pkt.src_ip
            dst_ip = arp_pkt.dst_ip
            if arp_pkt.opcode == arp.ARP_REPLY:
                self.arp_table[src_ip] = src
                h1 = self.hosts[src]
                h2 = self.hosts[dst]
                out_port = self.install_path(h1[0], h1[1], h2[0], h2[1], src_ip, dst_ip)
                self.install_path(h2[0], h2[1], h1[0], h1[1], dst_ip, src_ip) # reverse
                
            elif arp_pkt.opcode == arp.ARP_REQUEST:
                if dst_ip in self.arp_table:
                    self.arp_table[src_ip] = src
                    dst_mac = self.arp_table[dst_ip]
                    h1 = self.hosts[src]
                    h2 = self.hosts[dst_mac]
                    out_port = self.install_path(h1[0], h1[1], h2[0], h2[1], src_ip, dst_ip)
                    self.install_path(h2[0], h2[1], h1[0], h1[1], dst_ip, src_ip) # reverse


        actions = [ofp_parser.OFPActionOutput(out_port)]

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = ofp_parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,
            actions=actions, data=data)
        datapath.send_msg(out)

    @set_ev_cls(event.EventSwitchEnter) #Behaviour of the network when a switch enters it 
    def switch_enter_handler(self, ev):
        switch = ev.switch.dp
        print("The switch", switch.id, "entered the network.")
        self.switches_count += 1

        if switch.id not in self.switches:
            self.switches.append(switch.id)
            self.datapath_list[switch.id] = switch

        self.pkt_count = 0

    @set_ev_cls(event.EventSwitchLeave, MAIN_DISPATCHER) #Behaviour of the network when a switch leaves it 
    def switch_leave_handler(self, ev):
        print (ev)
        switch = ev.switch.dp.id
        if switch in self.switches:
            self.switches.remove(switch)
            self.switches_count -= 1
            del self.datapath_list[switch]
            del self.adjacency[switch]

    @set_ev_cls(event.EventLinkAdd, MAIN_DISPATCHER) #Behaviour of the network when a link is added
    def link_add_handler(self, ev):
        s1 = ev.link.src
        s2 = ev.link.dst
        if s1 not in self.links:
            self.links.append(s1)
            self.adjacency[s1.dpid][s2.dpid] = s1.port_no
        if s2 not in self.links:
            self.links.append(s2)
            self.adjacency[s2.dpid][s1.dpid] = s2.port_no

    @set_ev_cls(event.EventLinkDelete, MAIN_DISPATCHER) #Behaviour of the network when a link is removed 
    def link_delete_handler(self, ev):
        s1 = ev.link.src
        s2 = ev.link.dst
        #Exception handling if the switch is already deleted
        try:
            del self.adjacency[s1.dpid][s2.dpid]
            self.links.remove(s1)
            del self.adjacency[s2.dpid][s1.dpid]
            self.links.remove(s2)
        except KeyError:
            pass
        print("The link from s",s1.dpid,"to s",s2.dpid,"has failed.")
        #once the link is down the neighbours got the miss flow entries
        self.send_miss_flow_entry_again(s1.dpid, s2.dpid)
        
    #this allows to save all datapath in the OpenFlow tables of the hosts taken in exam
    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]  
                
    #this allow to send to send the messages containing the missing flow entry 
    def send_miss_flow_entry_again(self, s1, s2): 
            for datapath in self.datapaths.values():
                if (datapath.id == s1 or datapath.id == s2):
                    self.remove_flows(datapath, 0)
            for datapath in self.datapaths.values():
                if (datapath.id == s1 or datapath.id == s2):
                    self.en_clear_flow_entry =  False
                    self.add_flow(datapath, 0, self.match_miss_flow_entry, self.actions_miss_flow_entry)
                 
    #through this the old flows are removed                
    def remove_flows(self, datapath, table_id):
        ofp_parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        empty_match = ofp_parser.OFPMatch()
        instructions = []
        flow_mod = self.remove_table_flows(datapath, table_id, empty_match, instructions)
        print ("All flow entries contained in table ", table_id,"are removed")
        datapath.send_msg(flow_mod)
    
    #this function creates OFP flow mod messages in order to remove flows from the table
    def remove_table_flows(self, datapath, table_id, match, instructions):
        ofproto = datapath.ofproto
        flow_mod = datapath.ofproto_parser.OFPFlowMod(datapath, 0, 0, table_id,
                                                      ofproto.OFPFC_DELETE, 0, 0,
                                                      1,
                                                      ofproto.OFPCML_NO_BUFFER,
                                                      ofproto.OFPP_ANY,
                                                      OFPG_ANY, 0,
                                                      match, instructions)
        return flow_mod
