import random
import numpy
# Feel free to add any imports you might need, and note that you might
# not need to use either of the ones we've provided.

from PS7_wsim import *

class CSMANode(WirelessNode):
    def __init__(self,location,network,retry):
        WirelessNode.__init__(self,location,network,retry)
        # Initialize local probability of transmission
        self.p = float(self.network.pmax)
        self.pmax = float(self.network.pmax)
        self.pmin = float(self.network.pmin)
        # Set any additional state or variables here if you need them.

    def channel_access(self, current_time, packet_size):
        # TODO: Your code here.  Return true if the node should send a
        # packet in this timeslot (false otherwise).  You can tell if
        # the channel is busy by using the self.network.channel_busy()
        # function.
        if not self.network.channel_busy():
            return random.random()<=self.p
        return False
        
    def on_collision(self, packet):
        # TODO: Your code here.  No return value.
        self.p = max(self.p/2,self.pmin)

    def on_success(self, packet):
        # TODO: Your code here.  No return value.
        self.p = min(2*self.p,self.pmax)

