from sim.api import *
from sim.basics import *
from collections import defaultdict

'''
Create your RIP router in this file.
'''
class RIPRouter (Entity):
    
    def __init__(self):
        #initiate data structures
        #dst:{neighbor,total distance}
        self.forwardingTable = {} 
        
        #srcneighbors:{destination:distance}
        self.pathTable = {} 
        
        #src:{src:ports}
        self.portTable = {}
        
    def handle_rx (self, packet, port):
        #route to handlers by packet type
        if isinstance(packet , DiscoveryPacket):
            self.discoveryHandler(packet, port)
        elif isinstance(packet, RoutingUpdate):
            self.routingUpdateHandler(packet, port)
        else:
            #print packet.src.name
            if packet.dst in self.forwardingTable:
                self.send(packet, self.portTable[self.forwardingTable[packet.dst][0]])
            else: #destination not in table
                pass
    
    def discoveryHandler(self, packet, port):
        print ("Discovery", packet.src.name)
        if packet.is_link_up: #link up, add port to table
            self.portTable[packet.src] = port
            if packet.src not in self.pathTable:
                self.pathTable[packet.src] = {}
        else: #link down, remove port from table
            self.pathTable.pop(packet.src, None)
            self.portTable.pop(packet.src, None)
        #new entity or removed entity -> recalculate optimal routes/distances    
        if self.calcMinDist() == True: #if true, send routing update
            self.sendUpdate()

    def routingUpdateHandler(self, packet, port):
        if packet.src not in self.pathTable:
            return
        self.pathTable[packet.src] = {}
        for dst in packet.all_dests():
            self.pathTable[packet.src][dst] = packet.get_distance(dst)
        if self.calcMinDist() == True: #if true, send routing update
            self.sendUpdate()


    #helper function to calculate minimum distances to destinations
    #returns True if forwarding table or path distance changes
    def calcMinDist(self):
        #print "recalcing Distance"
        updatedPathDist = {}
        updatedTable = {}
        for src in self.pathTable.keys(): #each entity
            updatedPathDist[src] = 1
            for dst in self.pathTable[src].keys():
                distance = self.pathTable[src][dst] + 1
                if self.pathTable[src][dst] < 100: 
                    if ((not updatedTable.has_key(dst)) or distance < updatedTable[dst][1]): 
                        updatedTable[dst] = (src, distance)
                elif updatedTable.has_key(dst) and self.pathTable.has_key(src) and distance == updatedTable[dst][1]: #equal distance, use smaller port
                    if updatedTable.has_key(dst) and self.portTable[updatedTable[dst][0]] < self.portTable[src]:
                        updatedTable[dst] = (updatedTable[dst][0], distance)
                else:
                    pass
        if self.forwardingTable != updatedTable:
            self.forwardingTable = updatedTable
            return True
        else:
            self.fowardingTable = updatedTable
            return False

    #inform entities of routing update
    def sendUpdate(self):
        for src in self.pathTable.keys():
            packet = RoutingUpdate()              
            for dst in self.forwardingTable:
                if self.forwardingTable[dst][0] == src:
                    packet.add_destination(dst, 100)
                    pass
                        
                else:
                        #print "not poison"
                    packet.add_destination(dst, self.forwardingTable[dst][1])
            self.send(packet, self.portTable[src])
