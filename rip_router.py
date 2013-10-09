from sim.api import *
from sim.basics import *
import copy

'''
Create your RIP router in this file.
'''
class RIPRouter (Entity):
    INFINITY = 100
    
    DEBUG = False
    
    
    """
    IMPORTANT
    
    From Piazza
    -Please don't advertise a neighbor to himself, i.e. if A is connected to B, please don't include B in A's update to B.
    -You should send RoutingUpdates whenever your routing table changes.
    -If your router does not have a route for a particular destination -- Drop that packet!
    """
    
    def __init__(self):

        #dictionary that maps from:
        #    K: destination
        #    to
        #    V: port to send it out to
        self.forwardingTable = {}
        
        #dictionary that maps from: 
        #    K: destination 
        #    to 
        #    V: min hop path distance in forwarding table
        self.paths = {}
        
        #dictionary that maps from: 
        #    K: neighbor  
        #    to 
        #    V: a DICTIONARY of destinations reachable by that port
        self.neighbors_distances = {}
        
    def handle_rx (self, packet, port):
        # Add your code here!
        if isinstance( packet , DiscoveryPacket):
            if self.DEBUG:
                debugLinkUp = "LINK_UP" if packet.is_link_up else "LINK DOWN" 
                print "######## Received a %s DiscoveryPacket thru PORT: %i from SRC: %s #######" % (debugLinkUp, port, packet.src.name) 
            
            #link up case
            if packet.is_link_up:
                #add as a neighbor in forwarding table
                self.paths[packet.src] = 1
                self.forwardingTable[packet.src] = port
                self.neighbors_distances[packet.src] = {}
                # I wouldn't have to update any other distances.  (Right?)
                # RoutingUpdates case should take care of it for me
                
            #link down case
            else:
                del(self.neighbors_distances[packet.src])
                del(self.paths[packet.src])
                del(self.forwardingTable[packet.src])    
                # Find new min distance and proper port
                # We need to recalculate everything from what we have.  
                # This is why we need RoutingUpdates' information stored
            
            # Send routing update IF THE ROUTING TABLE CHANGED
            if self.recalculateMinDist():
                if self.DEBUG:
                    print "||||| SENDING RoutingUpdates for DiscoveryPacket from %s |||||" % (packet.src)
                self.send_RoutingUpdates()

        elif isinstance(packet, RoutingUpdate):
            #TODO: handle Split horizon with poisoned reverse
            tempMap = {}
            for dest in packet.all_dests():
                tempMap[dest] = packet.get_distance(dest)
            
            if self.DEBUG:
                print "######## Received a RoutingUpdate %s from SRC: %s" % (tempMap, packet.src)
            
            self.neighbors_distances[packet.src] = tempMap 
            
            # Send routing update IF THE ROUTING TABLE CHANGED
            if self.recalculateMinDist():
                if self.DEBUG:
                    print "||||| SENDING RoutingUpdates for RoutingUpdate from %s |||||" % (packet.src)
                self.send_RoutingUpdates()
        else:
            # FORWARD THE PACKET CORRECTLY
            
            if packet.dst in self.forwardingTable:
                self.send(packet, self.forwardingTable[packet.dst])
            else:
                if self.DEBUG:
                    print "Dropping packet from %s" % packet.src
                pass
                
            """
            # If your router does not have a route for a particular destination -- Drop that packet!
            try:
                for fwdport in sorted(self.forwardingTable[packet.dst].keys()):  #sort so that tie broken by lowest port number
                    if self.forwardingTable[packet.dst][port] == self.min_dist_table[packet.dst]:
                        self.send(packet, fwdport)
            except KeyError:
                pass
            """
    
    # Updates and determines if we need to send
    # Returns TRUE if we NEED TO SEND ROUTING UPDATE
    # FALSE OTHERWISE
    def recalculateMinDist(self):
        new_paths = {}
        new_forwardingTable = {}
                
        # For each RoutingUpdate:
        for neighbor in self.neighbors_distances.keys():
            new_paths[neighbor] = 1
            new_forwardingTable[neighbor] = self.forwardingTable[neighbor]
            
            if self.neighbors_distances[neighbor] == {}:
                pass
            else:
                # For each entry in the RoutingUpdate:
                for dest in self.neighbors_distances[neighbor].keys():
                    hop_count = self.neighbors_distances[neighbor][dest]
                    distFromSelf = hop_count + 1
                    
                    # If we haven't entered it yet OR the current value is SMALLER:
                    if not (dest in new_paths.keys()) or distFromSelf < new_paths[dest]:
                        # Update
                        new_paths[dest] = distFromSelf
                        # The best path to DEST is THRU NEIGHBOR
                        new_forwardingTable[dest] = self.forwardingTable[neighbor]
                    elif distFromSelf == self.paths[dest]:
                        # IS IT A TIE?  BREAK BY LOWER PORT ID
                        current_port = new_forwardingTable[dest]
                        new_port = self.forwardingTable[neighbor]
                        
                        new_forwardingTable[dest] = min(current_port, new_port)
                    else:
                        # Otherwise, no need to update
                        pass
        
        """            
        for neighbor in self.neighbors_distances.keys():
            for dest in self.neighbors_distances[neighbor].keys():
                hop_count = self.neighbors_distances[neighbor][dest]
                distFromSelf = hop_count + 1
                if not (dest in self.paths.keys()) or distFromSelf < self.paths[dest]:
                    # ^ getting a key error above means it's not updated when it should have
                    self.paths[dest] = distFromSelf
                    self.forwardingTable[dest] = self.forwardingTable[neighbor]       
                elif distFromSelf == self.paths[dest]:
                    # Break ties by lower port ID
                    current_port = self.forwardingTable[dest]
                    new_port = self.forwardingTable[neighbor]
                    self.forwardingTable[dest] = min(current_port, new_port)
        """
        
        # IF ANYTHING CHANGED, WE NEED TO RETURN TRUE
        
        if self.DEBUG:
            print "__________________________________________________________"
            print "NEW paths: %s" % (new_paths)
            print "NEW forwardingTable: %s" % (new_forwardingTable)
            print "__________________________________________________________"
        
        
        output = not (new_paths == self.paths and new_forwardingTable == self.forwardingTable) 
        
        self.paths = new_paths
        self.forwardingTable = new_forwardingTable
        
        return output
        
    
    
    # Send routing updates to neighbors (a list of neighbors, NOT PORTS)
    # NOTE: Please don't advertise a neighbor to himself, 
    # i.e. if A is connected to B, please don't include B in A's update to B.
    def send_RoutingUpdates(self):
        # Because of the above constraint, we need to make each a routing update for
        # POISON REVERSE:
        # IF BEST ROUTE TO X IS THROUGH N
        # ADVERTISE X:100 TO N
        for neighbor in self.neighbors_distances.keys():
            newRoutingUpdate = RoutingUpdate()                
            for dest in self.paths.keys():
                # DO NOT ADVERTISE NEIGHBOR TO ITSELF
                if dest != neighbor:
                    
                    if self.DEBUG:
                        if not dest in self.forwardingTable.keys():
                            print "dest: %s" % (dest)
                        if not neighbor in self.forwardingTable.keys():
                            print "neighbor: %s" % (neighbor)
                        
                    if self.forwardingTable[dest] == self.forwardingTable[neighbor]:   
                        newRoutingUpdate.add_destination(dest, 100)
                    else:
                        newRoutingUpdate.add_destination(dest, self.paths[dest])
        
            if self.DEBUG:
                print "#~#~#~#~# Sending RoutingUpdates to %s" % neighbor
                print "thru port: %s #~#~#~#~#" % self.forwardingTable[neighbor]
            
            self.send(newRoutingUpdate, self.forwardingTable[neighbor])

        
        
        
        