import re
import sys
from mininet.log import setLogLevel, info, error
from mininet.topo import Topo
from mininet.link import Intf
from mininet.util import quietRun

class SimpleTopo(Topo):


    def __init__(self):
        Topo.__init__(self)

        h1 = self.addHost('h1', mac = '00:00:00:00:00:01')
        h2 = self.addHost('h2', mac = '00:00:00:00:00:02')
        h3 = self.addHost('h3', mac = '00:00:00:00:00:03')
        h4 = self.addHost('h4', mac = '00:00:00:00:00:04')
        switch = self.addSwitch('s1', protocols=["OpenFlow13"] )

        #inetfname = 'vboxnet0'
        #checkIntf(inetfname)
        #_inetf = Intf(inetfname,node=switch)

        #add links
        self.addLink(h1,switch)
        self.addLink(h2,switch)
        self.addLink(h3,switch)
        self.addLink(h4,switch)


topos = {'simpletopo': (lambda:SimpleTopo())}
