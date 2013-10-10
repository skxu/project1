from sim.api import *
from sim.basics import *
from collections import defaultdict

'''
Create your RIP router in this file.
'''
class RIPRouter (Entity):
    
    def __init__(self):
        #dst:port of next hop
        self.forwardingTable = {}

        #dst:hop distance
        self.minPathDist = {}

        #src:{destination,distance}
        self.pathTable = defaultdict(lambda: dict)
        
    def handle_rx (self, packet, port):
        #route to handlers by packet type
        if isinstance(packet , DiscoveryPacket):
            self.discoveryHandler(packet, port)

        elif isinstance(packet, RoutingUpdate):
            self.routingUpdateHandler(packet, port)
        
        else:
            if packet.dst in self.forwardingTable:
                self.send(packet, self.forwardingTable[packet.dst])
            else:
                pass
    
    def discoveryHandler(self, packet, port):
        if packet.is_link_up: #link up
            self.minPathDist[packet.src] = 1
            self.forwardingTable[packet.src] = port
            self.pathTable[packet.src] = {}
        else: #link down
            self.pathTable.pop(packet.src, None)
            self.minPathDist.pop(packet.src, None)
            self.forwardingTable.pop(packet.src, None)    
        if self.calcMinDist() == True: #if true, send routing update
            self.updateRouting()

    def routingUpdateHandler(self, packet, port):
        updatedPathTable = {}
        for dst in packet.all_dests():
            updatedPathTable[dst] = packet.get_distance(dst) 
        self.pathTable[packet.src] = updatedPathTable 
        if self.calcMinDist() == True: #if true need to update routing
            self.updateRouting()


    #helper function to calculate minimum distances to destinations
    #returns true if forwarding table or path distance changes
    def calcMinDist(self):
        updatedPathDist = {}
        updatedTable = {}
        for src in self.pathTable.keys(): #each entity
            updatedPathDist[src] = 1
            if self.forwardingTable.has_key(src):
                updatedTable[src] = self.forwardingTable[src]
            else:
                print "key error"
            if self.pathTable[src] == {}:
                pass
            else:
                for dst in self.pathTable[src].keys():
                    distance = self.pathTable[src][dst] + 1
                    if (not updatedPathDist.has_key(dst)) or distance < updatedPathDist[dst]: 
                        updatedPathDist[dst] = distance
                        updatedTable[dst] = self.forwardingTable[src]
                    elif distance == self.minPathDist[dst]: #equal distance, use smaller port
                        if self.forwardingTable[src] < updatedTable[dst]:
                            updatedTable[dst] = self.forwardingTable[src]
                    else:
                        pass
        if self.minPathDist != updatedPathDist or self.forwardingTable != updatedTable:
            self.minPathDist = updatedPathDist
            self.forwardingTable = updatedTable
            return False
        else:
            self.minPathDist = updatedPathDist
            self.forwardingTable = updatedTable
            return True


    def updateRouting(self):
        for src in self.pathTable.keys():
            packet = RoutingUpdate()                
            for dst in self.minPathDist.keys():
                if dst != src:
                    if self.forwardingTable[dst] == self.forwardingTable[src]:   
                        packet.add_destination(dst, 100)
                    else:
                        packet.add_destination(dst, self.minPathDist[dst])
            
            self.send(packet, self.forwardingTable[src])

        
        
        
        