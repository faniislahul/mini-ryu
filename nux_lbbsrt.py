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
#from ryu.lib.packet import icmp
from ryu.lib.packet import tcp
from ryu.lib.packet import ether_types
import random
import socket
import time
from threading import Thread
import thread
import json
import urllib, httplib
import csv

class nuc(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto.OFP_VERSION]
    interval = 2
    adj = 100/interval
    seq = 0
    res = open("result/control_side.csv", "wb")
    writer = csv.writer(res, delimiter=',')

    spms = {'10.0.0.1' : 0,'10.0.0.2' : 0,'10.0.0.3' : 0}
    mac_ip = {'10.0.0.1' : '00:00:00:00:00:01' , '10.0.0.2' : '00:00:00:00:00:02','10.0.0.3' : '00:00:00:00:00:03'}
    mac_port = {'00:00:00:00:00:01' : 1, '00:00:00:00:00:02' : 2, '00:00:00:00:00:03' : 3}
    def __init__(self, *args, **kwargs):
        super(nuc, self).__init__(*args, **kwargs)


    #method for server checking
    def server_check(self, ip):
        global spms
        global seq
        global interval
        global adj
        global writer

        conn = httplib.HTTPConnection(ip+':80', timeout=self.interval)
        try:
            params = urllib.urlencode({'seq': self.seq})
            headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
            conn.request('POST','/control',params,headers)
            start = time.time()
            response = conn.getresponse()
                data = json.load(response.read())
                if(response.status == 200):
                end = time.time()
                rtt = end-start
                clc = data['clc']
                spm = rtt
                line = [self.seq,mem,cpu,rtt,clc, spm]
                self.writer.writerow(line)
                self.spms[ip] = spm
                self.seq = self.seq+self.interval
            else:
                self.spms[ip] = self.interval
                line = [self.seq,100,100,100,0,self.interval]
                self.writer.writerow(line)
                self.seq = self.seq+self.interval
                print "IP = "+ip+" BAD REQUEST"
        except:
                self.spms[ip] = self.interval
                line = [self.seq,100,100,100,0,self.interval]
                self.writer.writerow(line)
                self.seq = self.seq+self.interval
                print "IP = "+ip+" REQUEST TIMEOUT"


    #this method creates 3 threat that check each server status with interval
    def ctr_check(self, datapath):
        servers = {"10.0.0.1","10.0.0.2","10.0.0.3"}
        global spms
        global interval
        while True:
            for ip in servers:
                z = Thread(target=self.server_check, args=(ip,))
                z.start()

            time.sleep(self.interval)
            print self.spms.items()
            min_ = 1000
            mac_ = ""
            for ip in servers:
                if self.spms[ip] <= min_ :
                    min_ = self.spms[ip]
                    mac_ = self.mac_ip[ip]
            if min_ == self.interval:
                mac_ = '00:00:00:00:00:0'+str(random.randrange(1,4))

            #print 'mac is ',mac_
            self.add_lb_flow(datapath, mac_)

            print "----------------------------------------------"

    #this method do the openflow protocol to create new flows
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
        #print "load balancer flow added"

    #this method creates initial flows for whole packet in networks
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
        #print "thread block passed"

         #ARP packets flooding
        match = ofparser.OFPMatch(eth_type=0x0806)
        actions = [ofparser.OFPActionOutput(port=ofproto.OFPP_FLOOD)]
        self.add_flow1(datapath=datapath, table_id=0, priority=100,
                        match=match, actions=actions)

        # reverse path flow
        for i in range (1,4):
            ip = "10.0.0."+str(i)
            eth = "00:00:00:00:00:0"+str(i)

            match = ofparser.OFPMatch(in_port=i, eth_type=0x800, ip_proto=6,tcp_src = 80, ipv4_src=ip,eth_src=eth,ipv4_dst='10.0.0.4')
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



    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        global mac_port
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        pkt = packet.Packet(msg.data)

        #this part create path between controller and servers
        if msg.match['in_port'] != 4:
            if(pkt.get_protocol(ethernet.ethernet)):
    #            if(pkt.get_protocol(ipv4.ipv4)):
                _eth = pkt.get_protocol(ethernet.ethernet)
                try :
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
                except:
                    pass

        else:
            print pkt
