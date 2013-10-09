from sim.api import *
from sim.basics import *

'''
Create your RIP router in this file.
'''
class RIPRouter (Entity):
    def __init__(self):
        # Add your code here!
        self.forwardingTable = {}
        self.routingTable = {}
        

    def handle_rx (self, packet, port):
        # Add your code here!
        if isinstance(packet, DiscoveryPacket):
        	discoveryHandler(self, packet, port)
        elif isinstance(packet,RoutingUpdate):
        	updateHandler(self, packet, port)
        else:
        	if packet.dst in self.forwardingTable:
        		self.send(packet, self.forwardingTable[packet.dst])


        raise NotImplementedError
	def discoveryHandler (self, packet, port):
		if packet.is_link_up:
			self.forwardingTable[packet.src] = {}
			self.forwardingTable[packet.src][packet.src] = (port, 1)
		elif packet.src in table:
			del(self.table[packet.src])


	def updateHandler (self, packet,port):



