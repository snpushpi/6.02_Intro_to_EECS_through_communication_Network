import random
import numpy
# Feel free to add any imports you might need, and note that you might
# not need to use either of the ones we've provided.

from PS7_wsim import *

class TDMANode(WirelessNode):
    def __init__(self,location, network, retry):
        WirelessNode.__init__(self,location,network,retry)
        self.n_nodes = self.network.n_nodes
        # Set any additional state or variables here if you need them.
        # Note: Calling self.get_id() from __init__ will result in an
        # error, because the node is not officially added to the
        # network until after __init__ returns.

    def channel_access(self, current_time, packet_size):
        # TODO: Your code here.  Return true if the node should send a
        # packet in this timeslot (false otherwise).  Use self.n_nodes
        # to get the number of nodes in the network, self.get_id() to
        # get this node's unique ID.
        ID = self.get_id()
        n = self.n_nodes
        return current_time % (packet_size*n) == (ID*packet_size)

    def on_success(self, packet):
        # You don't need to implement this method, but don't delete it!
        pass

    def on_collision(self, packet):
        # You don't need to implement this method, but don't delete it!
        pass

