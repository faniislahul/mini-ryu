from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3 as ofproto
import ryu.ofproto.ofproto_v1_3_parser as ofparser
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import icmp
from ryu.lib.packet import ether_types
import random
import socket
import time

class RRLB(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto.OFP_VERSION]
    inc = 1
    interval = 2
    def __init__(self, *args, **kwargs):
        super(RRLB, self).__init__(*args, **kwargs)


    def add_flow(self, datapath, table_id, priority, match, actions):
        global inc
        inst = [ofparser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = ofparser.OFPFlowMod(datapath=datapath, table_id=table_id,
                                priority=priority, match=match, instructions=inst, idle_timeout=self.interval)
        datapath.send_msg(mod)
        print "load balancer flow added"

    def add_flow1(self, datapath, table_id, priority, match, actions):
        inst = [ofparser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = ofparser.OFPFlowMod(datapath=datapath, table_id=table_id,
                                priority=priority, match=match, instructions=inst)
        datapath.send_msg(mod)
        print "normal flow added"

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath

         #ARP packets flooding
        match = ofparser.OFPMatch(eth_type=0x0806)
        actions = [ofparser.OFPActionOutput(port=ofproto.OFPP_FLOOD)]
        self.add_flow1(datapath=datapath, table_id=0, priority=100,
                        match=match, actions=actions)

        # reverse path flow
        for i in range (1,4):
            ip = "10.0.0."+str(i)
            eth = "00:00:00:00:00:0"+str(i)
            match = ofparser.OFPMatch(in_port=i, eth_type=0x800, ip_proto=6, ipv4_src=ip,eth_src=eth)
            actions = [ofparser.OFPActionSetField(ipv4_src="10.0.0.1"),
                       ofparser.OFPActionSetField(eth_src="00:00:00:00:00:01"),
                       ofparser.OFPActionSetField(tcp_src=80),
                       ofparser.OFPActionOutput(port=4, max_len=0)]
            self.add_flow1(datapath=datapath, table_id=0, priority=100,
                    match=match, actions=actions)

        # reverse ARP path flow
        for i in range (1,4):
            ip = "10.0.0."+str(i)
            eth = "00:00:00:00:00:0"+str(i)
            match = ofparser.OFPMatch(in_port=i, eth_type=ether_types.ETH_TYPE_ARP, ipv4_src=ip,eth_src=eth)
            actions = [ofparser.OFPActionSetField(ipv4_src="10.0.0.1"),
                       ofparser.OFPActionSetField(eth_src="00:00:00:00:00:01"),
                       ofparser.OFPActionOutput(port=4, max_len=0)]
            self.add_flow1(datapath=datapath, table_id=0, priority=100,
                    match=match, actions=actions)

        # controller routine flow
        for i in range (1,4):
            ip = "10.0.0."+str(i)
            eth = "00:00:00:00:00:0"+str(i)
            match = ofparser.OFPMatch(in_port=ofproto.OFPP_CONTROLLER,ipv4_src = "10.0.0.5" ,
            ipv4_dst=ip,eth_dst=eth)
            actions = [ofparser.OFPActionOutput(port=i, max_len=0)]
            self.add_flow1(datapath=datapath, table_id=0, priority=100,
                    match=match, actions=actions)

        # reverse controller routine flow
        for i in range (1,4):
            ip = "10.0.0."+str(i)
            eth = "00:00:00:00:00:0"+str(i)
            match = ofparser.OFPMatch(in_port=i, ipv4_src=ip,eth_src=eth, ipv4_dst = "10.0.0.5")
            actions = [ofparser.OFPActionOutput(port=ofproto.OFPP_CONTROLLER, max_len=0)]
            self.add_flow1(datapath=datapath, table_id=0, priority=100,
                    match=match, actions=actions)



    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        global inc
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        _ipv4 = pkt.get_protocol(ipv4.ipv4)
        _icmp = pkt.get_protocol(icmp.icmp)

        if _icmp:
            self.logger.info("%r", _icmp)

        if _ipv4:
            self.logger.info("%r", _ipv4)

        if eth:
            self.logger.info("%r", eth)

        dpid = msg.match['in_port']
        #self.mac_to_port.setdefault(dpid,{})
        #self.logger.info(pkt)
        if dpid == 4:

            match = datapath.ofproto_parser.OFPMatch(
            in_port = dpid,
            eth_type=0x800,
            ip_proto=6,
            tcp_dst =80,
            ipv4_dst='10.0.0.1',
            eth_dst='00:00:00:00:00:01'
            )
            inc = self.inc
            ip = "10.0.0."+str(inc)
            eth = "00:00:00:00:00:0"+str(inc)
            actions = [  ofparser.OFPActionSetField(ipv4_dst=ip),
                        ofparser.OFPActionSetField(eth_dst=eth),
                        ofparser.OFPActionSetField(tcp_dst=80),
                        ofparser.OFPActionOutput(port=inc)
                        ]
            self.add_flow(datapath=datapath, table_id=0, priority=100,
                    match=match, actions=actions)
            print "redirected to port ",inc
            self.inc= (inc%3)+1
            #self.logger.info("client request initiated")

    servers = {"10.0.0.1","10.0.0.2","10.0.0.3"}
    n=0
    while True:

        for ip in servers:
            #print "Attempting connection to "+ip+" at port 8098"
            clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            clientsocket.connect((ip, 8089))
            clientsocket.send("HELLO")
            data = clientsocket.recv(1024)
            print "IP = "+ip+" SEQ = "+str(n)+" "+data

            clientsocket.close()
        n+=1
        time.sleep(2)
