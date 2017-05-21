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

class RRLB(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto.OFP_VERSION]
    inc = 1
    def __init__(self, *args, **kwargs):
        super(RRLB, self).__init__(*args, **kwargs)


    def add_flow(self, datapath, table_id, priority, match, actions):
        global inc
        inst = [ofparser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = ofparser.OFPFlowMod(datapath=datapath, table_id=table_id,
                                priority=priority, match=match, instructions=inst, hard_timeout=3)
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

        #sor_ip = ip4.src_ip
        #des_ip = ip4.des_ip
        #des_port = ip4.tcp_src
        if _icmp:
            self.logger.info("%r", _icmp)

        if _ipv4:
            self.logger.info("%r", _ipv4)

        if eth:
            self.logger.info("%r", eth)

        dpid = msg.match['in_port']
        #self.mac_to_port.setdefault(dpid,{})
        #self.logger.info("packet in %s from %s to %s ", dpid, des_ip, sor_ip)
        if dpid == 4:
            #match = datapath.ofproto_parser.OFPMatch(
            #in_port = dpid,
            #)
            #action = [  ofparser.OFPActionOutput(4),
                        #ofp.OFPActionSetField(ipv4_src="10.0.0.1"),
                        #ofp.OFPActionSetField(eth_dst="00:00:00:00:00:04")
            #            ]
            #self.add_flow(datapath,match,action)
            #self.logger.info("server response initiated")
        #else:
        #    if (eth.ethertype == ether_types.ETH_TYPE_ARP):
        #        print eth.get_packet_type
        #        match = ofparser.OFPMatch(in_port = dpid,
        #        eth_type=0x0806, eth_src= '00:00:00:00:00:04' )
        #        actions = [ofparser.OFPActionOutput(port= ofproto.OFPP_FLOOD),
        #                    ofparser.OFPActionSetField(ipv4_dst="10.0.0.1"),
        #                    ofparser.OFPActionSetField(eth_dst="00:00:00:00:00:01"),
        #                  ]
        #        inst = [ofparser.OFPInstructionActions(
        #                ofproto.OFPIT_APPLY_ACTIONS, actions)]
        #        mod = ofparser.OFPFlowMod(datapath=datapath, table_id=99,
        #                                priority=100, match=match, instructions=inst)
        #        datapath.send_msg(mod)
        #        print "got it"
        #    else:
                match = datapath.ofproto_parser.OFPMatch(
                in_port = dpid,
                eth_type=0x800,
                ip_proto=6,
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
                #exec('n=(n+1)%3', globals())

                #self.logger.info("client request initiated")
