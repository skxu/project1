from sim.api import *
from sim.basics import *
import time

   
class RIPRouter (Entity):
    def __init__(self):
        """
        forwarding table is a dictionary, its key is the possible out_going path(port) it can choose, in other words, first row of the table; its value is a tuple containing the destination and the cost going from one particular port
        """
        # Add your code here!
        # key: dest; value = [(distance, port),(. . .),(. . .)]
        self.route = {}
        
        # key: dest; value: (next_hop_through_port, min_distance)
        self.forward = {}
        
        # key: port; value: neighbor
        self.map = {}
    
    # update forwarding table from routing table
    def compute(self, table):
        output = {}
        for key in table.keys():
            min_option = self.cal_min(table[key])
            output[key] = (min_option[1], min_option[0])
        return output
    
    def cal_min (self, op):
        if len(op) > 0:
            op.sort()
            return op[0];
        
    # specify port and destination, modify forwarding table, and send update packet
    def send_update_info(self, port):
        update = RoutingUpdate()
        for d in self.forward.keys():
            if self.map[port] != d :
                if port == self.forward[d][0]:
                    update.add_destination(d, 100)
                else:
                    update.add_destination(d, self.forward[d][1])
        update.src, update.dst, update.ttl = self, self.map[port], 20
        self.send(update, port, flood = False)
        
    def modify_dictionary(self, port):
        new_dict = self.route.copy()
        del self.map[port]
        for key in self.route:
            for v in self.route[key]:
                if v[1] == port:
                    new_dict[key].remove(v)
            if not len(new_dict[key]):
                del new_dict[key]
        return new_dict
               
    def handle_rx (self, packet, port):
        # Add your code here!
        if packet.__class__.__name__ == "DiscoveryPacket":
            if packet.is_link_up:
                self.map[port] = packet.src
                if packet.src in self.route:
                    self.route[packet.src].append((1, port))
                    self.forward = self.compute(self.route)

                else:
                    self.route[packet.src] = [(1, port)]
                    self.forward = self.compute(self.route)
                
            else:
                self.route = self.modify_dictionary(port)
                self.forward = self.compute(self.route)
                
            self.forward = self.compute(self.route)
            for pt in self.map.keys():
                self.send_update_info(pt)
    
        elif packet.__class__.__name__ == "RoutingUpdate":
            dests = packet.all_dests()
            source = packet.src
            flag = False
            source_in = False
#            forward_info = self.forward.copy();
                            
            # implicit withdraw
            for dest in self.route:
                for v in self.route[dest]:
                    if v[1] == port:
                        source_in = True
                if source != dest and source_in and (dest not in packet.paths or packet.get_distance(dest) == 100):
                    for v in self.route[dest]:
                        if v[1] == port:
                            self.route[dest].remove(v)
                    if self.forward[dest][0] == port:
                        forward_info = self.forward[dest]
                        self.forward = self.compute(self.route)
                        if dest in self.forward and forward_info != self.forward[dest]:
                            flag = True
            
            for d in dests:
                if d == self:
                    pass
                else:
                    # if new destination requires update
                    # flag indicating whether the routing table has changed
                    if (packet.get_distance(d) != 100):
                        new_value = packet.get_distance(d) + 1;
                        if d not in self.route.keys():
                            self.route[d] = [(new_value, port)]
                            self.forward = self.compute(self.route)
                            flag = True
                        else:
                        # what if route has two options with the same cost?
                            not_found = True
                            for v in self.route[d][:]:
                                if v[1] == port:
                                    if v[0] != new_value:
                                        self.route[d].remove(v)
                                        self.route[d].append((new_value,port))
                                        self.route[d].sort()
                                        flag = True
                                    not_found = False
                            if not_found:
                                self.route[d].append((new_value, port))
                                flag = True
                            self.forward = self.compute(self.route)
            # poison reverse, send poison reverse to neighbors only when self decides to send packets through that neighbor.
            if flag:
                for pt in self.map.keys():
                    self.send_update_info(pt)
                    
        else:
            if packet.dst != self and packet.ttl != 0:
                self.send(packet,self.forward[packet.dst][0], flood = False)

