import random
import numpy
# Feel free to add any imports you might need, and note that you might
# not need to use either of the ones we've provided.

from PS7_wsim import *

class CSMACWNode(WirelessNode):
    def __init__(self,location,network,retry):
        WirelessNode.__init__(self,location,network,retry)
        self.cw = self.network.cwmin # Initialize to cwmin
        self.cwmin = self.network.cwmin
        self.cwmax = self.network.cwmax
        # Set any additional state or variables here if you need them.

        self.wait_time = 0

    def channel_access(self, current_time, packet_size):
        # TODO: Your code here.  Return true if the node should send a
        # packet in this timeslot (false otherwise).  You can tell if
        # the channel is busy by using the self.network.channel_busy()
        # function.
        if not self.network.channel_busy():
            if self.wait_time>0:
                self.wait_time-=1
            if self.wait_time==0:
                return True   
        return False
        
    def on_collision(self, packet): 
        self.cw = min(2*self.cw,self.cwmax)
        t = random.randint(1,self.cw)
        self.wait_time=t
        
    def on_success(self, packet):
        self.cw = max(self.cw/2,self.cwmin)
        t = random.randint(1,self.cw)
        self.wait_time=t
        
