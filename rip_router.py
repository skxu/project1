from sim.api import *
from sim.basics import *
from collections import defaultdict
'''
Create your RIP router in this file.
'''
class RIPRouter(Entity):
    def __init__(self):
        # Add your code here!
        self.forwardingTable = defaultdict(lambda: defaultdict(lambda:99999999.9))
        self.portTable = {}
        self.minDistances = defaultdict(lambda : 99999999.9)
        self.nextHop = {}
        

    def handle_rx(self, packet, port):
        # Handle packet types: Dicovery, RoutingUpdate, other
        if isinstance(packet, DiscoveryPacket):
            self.discoveryHandler(packet, port)
        elif isinstance(packet,RoutingUpdate):
            self.updateHandler(packet, port)
        else:
            if packet.dst in self.forwardingTable:
                self.send(packet, self.nextHop[packet.dst])


        
    def discoveryHandler(self, packet, port):
        print packet, "packet is this"
        if packet.is_link_up:
            self.forwardingTable[packet.src][port] = 1
            self.portTable[port] = packet.src
            if (self.updateHelper(1,packet.src,port)):
                self.updateRouter()
            else:
                for i in self.forwardingTable.keys():
                    self.forwardingTable[i][port] = 99999999.9 #large number
                portTable.pop(port)


    def updateHandler(self, packet, port):
        for i, j in packet.paths.iteritems():
            distance = self.forwardingTable[src][port]
            if self.forwardingTable[i][port] == 99999999.9 or (self.forwardingTable[i][port] > j + distance):
                self.forwardingTable[i][port] = j + distance
                if self.updateHelper(j+distance,i,port):
                    self.updateRouter()



    def updateHelper(self, d, src, port):
        if d < self.minDistances[src]:
            self.minDistances[src] = d
            self.nextHop[src] = port
            return True
        elif self.minDistances[src] == d:
            if self.nextHop[src] > port: #check for null error
                self.nextHop[src] = port
        return False

    def updateRouter(self):
        for port, dest in self.portTable.iteritems():
            print port, "this is port"
            print dest, "this is dest"
            routerUpdate = RoutingUpdate()
            print routerUpdate, "this is routerUpdate"
            for i, dist in self.minDistances.iteritems():
                if i not in [self,dest]:
                    routerUpdate.add_destination(i,dist)
            print routerUpdate, "this is routerUpdate 2"
            self.send(port,routerUpdate)



'''
    def calcMinDistances(self):
         for i in self.forwardingTable.keys()
            if i in self.minDistances:
                minDist = self.minDistances[i].values()[0]
            else:
                minDist = 100
            for j in self.forwardingTable[i].keys():
                if self.forwardingTable[i][j] < minDist:
                    self.update = True
                    minDist = self.forwardingTable[i][j]
                    self.minDistances[i] = {j:minDist}
                elif self.forwardingTable[i][j] == minDist and minDist < 100:
                    if self.portTable[j] < self.portTable[self.minDistances[i].keys()[0]]:
                        self.update = True
                        minDist = self.forwardingTable[i][j]
                        self.minDistances[i]={j:minDist}
'''




