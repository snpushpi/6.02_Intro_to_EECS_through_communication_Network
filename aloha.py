import random
import numpy
# Feel free to add any imports you might need, and note that you might
# not need to use either of the ones we've provided.

from PS7_wsim import *

class AlohaNode(WirelessNode):
    def __init__(self,location,network,retry):
        WirelessNode.__init__(self,location,network,retry)
        # Initialize local probability of transmission
        self.p = float(self.network.pmax)
        self.pmin = float(self.network.pmin)
        self.pmax = float(self.network.pmax)
        # Set any additional state or variables here if you need them.

    def channel_access(self, current_time, packet_size):
        # TODO: Your code here.  Return true if the node should send a
        # packet in this timeslot (false otherwise).
        return random.random()<=self.p

    def on_collision(self, packet):
       
        self.p = max(self.p/2,self.pmin)

    def on_success(self, packet):
        
        self.p = min(2*self.p,self.pmax)

