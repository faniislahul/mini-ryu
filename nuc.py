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
from ryu.lib.packet import tcp
from ryu.lib.packet import ether_types
import random
import socket
import time
from threading import Thread
import thread
import json

class nuc(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto.OFP_VERSION]
    inc = 1
    #stats = {"cpu": 0, "mem" : 0, "rtt" : 0}
    #arr = {'10.0.0.1' : stats,'10.0.0.2' : stats,'10.0.0.3' : stats}
    spms = {'10.0.0.1' : 0,'10.0.0.2' : 0,'10.0.0.3' : 0}
    mac_ip = {'10.0.0.1' : '00:00:00:00:00:01' , '10.0.0.2' : '00:00:00:00:00:02','10.0.0.3' : '00:00:00:00:00:03'}
    mac_port = {'00:00:00:00:00:01' : 1, '00:00:00:00:00:02' : 2, '00:00:00:00:00:03' : 3}
    def __init__(self, *args, **kwargs):
        super(nuc, self).__init__(*args, **kwargs)

    def server_check(self, ip):
        global spms
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.settimeout(2)
        #print ip
        try:
            clientsocket.connect((ip,8089))
            clientsocket.send("REQ")
            start = time.time()
            raw = clientsocket.recv(1024)
            data = json.loads(raw)
            end = time.time()
            rtt = end-start
            spm = (data['cpu']+data['mem']+(rtt*50))/3
            self.spms[ip] = spm
            #print str(rtt)
            #print "IP = "+ip+" RTT = "+str(rtt)+" CPU = "+str(data["cpu"])+" MEM = "+str(data["mem"])
            #print "IP = "+ip+" RTT = "+str(arr[ip]['rtt'])+" CPU = "+str(arr[ip]["cpu"])+" MEM = "+str(arr[ip]["mem"])
            clientsocket.close()
        except socket.timeout:
            self.spms[ip] = 1000
            print "IP = "+ip+" REQUEST TIMEOUT"
            clientsocket.close()
        except socket.error:
            self.spms[ip] = 1000
            print "IP = "+ip+" CONNECTION REFUSED"
            clientsocket.close()

    def ctr_check(self, datapath):
        servers = {"10.0.0.1","10.0.0.2","10.0.0.3"}

        #global servers
        global spms
        while True:
            for ip in servers:
                z = Thread(target=self.server_check, args=(ip,))
                z.start()

            time.sleep(2)
            print self.spms.items()
            min_ = 1000
            mac_ = ""
            for ip in servers:
                if self.spms[ip] <= min_ :
                    min_ = self.spms[ip]
                    mac_ = self.mac_ip[ip]
            if min_ == 1000:
                mac_ = '00:00:00:00:00:0'+str(random.randrange(1,4))

            print 'mac is ',mac_
            self.add_lb_flow(datapath, mac_)
            #for ip in arr:
            #    print "IP = "+ip+" RTT = "+str(arr[ip]['rtt'])+" CPU = "+str(arr[ip]["cpu"])+" MEM = "+str(arr[ip]["mem"])
                #print "IP = "+ip+" RTT = "+str(ip['rtt'])+" CPU = "+str(ip["cpu"])+" MEM = "+str(ip["mem"])
                #print ""
            #print "----------------------------------------------"

    def add_lb_flow(self, datapath, mac):
        global inc

        match = datapath.ofproto_parser.OFPMatch(
        in_port = 4,
        eth_type=0x800,
        ip_proto=6,
        ipv4_dst='10.0.0.1',
        eth_dst='00:00:00:00:00:01'
        )
        ip = "10.0.0."+str(self.mac_port[mac])
        eth = "00:00:00:00:00:0"+str(self.mac_port[mac])
        actions = [  ofparser.OFPActionSetField(ipv4_dst=ip),
                    ofparser.OFPActionSetField(eth_dst=eth),
                    ofparser.OFPActionSetField(tcp_dst=80),
                    ofparser.OFPActionOutput(port=self.mac_port[mac])
                    ]
        print "redirected to port ",self.mac_port[mac]

        inst = [ofparser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = ofparser.OFPFlowMod(datapath=datapath, table_id=0,
                                priority=100, match=match, instructions=inst, hard_timeout=2)
        datapath.send_msg(mod)
        print "load balancer flow added"

    def add_flow1(self, datapath, table_id, priority, match, actions):

        inst = [ofparser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = ofparser.OFPFlowMod(datapath=datapath, table_id=table_id,
                                priority=priority, hard_timeout=0,
                                match=match, instructions=inst)
        #print mod
        datapath.send_msg(mod)
        #print datapath
        print "normal flow added"


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        print "thread start"
        z = Thread(target=self.ctr_check, args=(datapath,))
        z.start()
        print "thread block passed"

         #ARP packets flooding
        match = ofparser.OFPMatch(eth_type=0x0806)
        actions = [ofparser.OFPActionOutput(port=ofproto.OFPP_FLOOD)]
        self.add_flow1(datapath=datapath, table_id=0, priority=100,
                        match=match, actions=actions)

        # reverse path flow
        for i in range (1,4):
            ip = "10.0.0."+str(i)
            eth = "00:00:00:00:00:0"+str(i)

            match = ofparser.OFPMatch(in_port=i, eth_type=0x800, ip_proto=6,tcp_src = 80, ipv4_src=ip,eth_src=eth)
            actions = [ofparser.OFPActionSetField(ipv4_src="10.0.0.1"),
                       ofparser.OFPActionSetField(eth_src="00:00:00:00:00:01"),
                       ofparser.OFPActionSetField(tcp_src=80),
                       ofparser.OFPActionOutput(port=4, max_len=0)]
            self.add_flow1(datapath=datapath, table_id=0, priority=100,
                    match=match, actions=actions)

        # reverse ARP path flow

            match_ = ofparser.OFPMatch(in_port=i, eth_type=ether_types.ETH_TYPE_ARP, ipv4_src=ip,eth_src=eth, eth_dst="00:00:00:00:00:04")
            actions_ = [ofparser.OFPActionSetField(ipv4_src="10.0.0.1"),
                       ofparser.OFPActionSetField(eth_src="00:00:00:00:00:01"),
                       ofparser.OFPActionOutput(port=4, max_len=0)]
            self.add_flow1(datapath=datapath, table_id=0, priority=100,
                    match=match_, actions=actions_)

#            match__ = ofparser.OFPMatch(in_port=ofproto.OFPP_CONTROLLER, eth_type=ether_types.ETH_TYPE_ARP, ipv4_src='10.0.0.5',
#                                eth_dst = eth, eth_src='96:21:b0:69:a1:46')
#            actions__ = [ofparser.OFPActionOutput(port=i, max_len=0)]
#            self.add_flow1(datapath=datapath, table_id=0, priority=100,
#                    match=match__, actions=actions__)
#
#            match_ = ofparser.OFPMatch(in_port=ofproto.OFPP_CONTROLLER, tcp_dst=8098, ipv4_dst=ip,
#                                eth_dst = eth, eth_src='96:21:b0:69:a1:46')
#            actions_ = [ofparser.OFPActionOutput(port=i, max_len=0)]
#            self.add_flow1(datapath=datapath, table_id=0, priority=100,
#                    match=match_, actions=actions_)
#
#            #controller routine check reverse flow
#            match___ = ofparser.OFPMatch(in_port = i,tcp_src=8098, ipv4_src=ip, ipv4_dst = '10.0.0.5',
#                eth_src = eth, eth_dst='96:21:b0:69:a1:46')
#            actions___ = [ofparser.OFPActionOutput(port = ofproto.OFPP_CONTROLLER, max_len = 0)]
#            self.add_flow1(datapath=datapath, table_id=0, priority=100,
#                    match=match___, actions=actions___)

            ###############
#            _match__ = ofparser.OFPMatch(ipv4_src='10.0.0.5', eth_type= 0x800,tcp_dst=8098, ipv4_dst = ip,
#                    eth_dst = eth, eth_src='96:21:b0:69:a1:46')
#            _actions__ = [ofparser.OFPActionOutput(port = i, max_len = 0)]
#            self.add_flow1(datapath=datapath, table_id=0, priority=100,
#                    match=_match__, actions=_actions__)


#        for i in range (1,4):
#            ip = "10.0.0."+str(i)
#            eth = "00:00:00:00:00:0"+str(i)
            #controller routine check flow



    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        global mac_port
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto

        pkt = packet.Packet(msg.data)
#        eth = pkt.get_protocol(ethernet.ethernet)
#        _ipv4 = pkt.get_protocol(ipv4.ipv4)
#        _icmp = pkt.get_protocol(icmp.icmp)
#        _tcp = pkt.get_protocol(tcp.tcp)
        #self.logger.info("%r", pkt)
        #sor_ip = ip4.src_ip
        #des_ip = ip4.des_ip
        #des_port = ip4.tcp_src

#        if _icmp:
#            self.logger.info("%r", _icmp)

#        if _ipv4:
#            self.logger.info("%r", _ipv4)
#        if eth:
#            self.logger.info("%r", eth)

#        if _tcp:
#            self.logger.info("%r", _tcp)
        #print pkt
        #print msg.match
        if(pkt.get_protocol(ethernet.ethernet)):
#            if(pkt.get_protocol(ipv4.ipv4)):
            _eth = pkt.get_protocol(ethernet.ethernet)
            if _eth.src in self.mac_port:
                _eth = pkt.get_protocol(ethernet.ethernet)
                match_ = ofparser.OFPMatch(in_port = msg.match['in_port'],
                                            eth_dst = _eth.dst,
                                            eth_src = _eth.src,
                                            )
                actions_ = [ofparser.OFPActionOutput(port=self.mac_port[_eth.dst], max_len=0)]
                self.add_flow1(datapath=datapath, table_id=0, priority=100,
                                    match=match_, actions=actions_)
            else :
                    self.mac_port.update({_eth.src : msg.match['in_port']})

#        if msg.match['in_port'] < 4:
#
#            _match__ = ofparser.OFPMatch(in_port = msg.match['in_port'],ipv4_dst = '10.0.0.5',
#            eth_src = eth.src, eth_dst='96:21:b0:69:a1:46')
#            _actions__ = [ofparser.OFPActionOutput(port = ofproto.OFPP_CONTROLLER, max_len = 0)]
#            self.add_flow1(datapath=datapath, table_id=0, priority=100,
#            match=_match__, actions=_actions__)


        dpid = msg.match['in_port']
