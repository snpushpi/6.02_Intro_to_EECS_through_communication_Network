import random,sys

from PS9_netsim import *
from PS9_util import *

class ReliableSenderNode(AbstractReliableSenderNode):

    def __init__(self,location,qsize,window,address=None,):
        self.network = None # This variable will be set by the following initialization methods
        AbstractReliableSenderNode.__init__(self,location,qsize,window,address=address)

    def reset(self):
        Router.reset(self)
        self.srtt = None
        self.rttdev = None
        self.timeout = 20 
        self.alpha = 0.5
        self.beta = 0.5
        self.seqnum = 1
        self.ack_received = False
        self.tracker = 20
        # arbitrary initial value
        # TODO: Your initialization code here, if you need any.  We've
        # already initialized self.srtt, self.rttdev, self.timeout
        # above.

    # Called every timeslot.  Decides whether to send a new packet, to
    # retransmit, or to do nothing.  If you need to send a packet in
    # this timeslot, use the send_packet() function.
    def reliable_send(self):
    
        if self.tracker==0:
            self.tracker = self.timeout
            self.send_packet(self.seqnum,self.network.time)            
            self.ack_received = False
        else:
            if self.ack_received==False:
                self.tracker-=1
            else:
                self.send_packet(self.seqnum,self.network.time)
                self.ack_received = False
            #self.timeout-=1

    # Invoked whenever an ACK arrives
    def process_ack(self, acknum, sender_timestamp):
        self.seqnum+=1
        self.ack_received=True
        self.calc_timeout(sender_timestamp) 
    # Don't delete this!

    # Called whenever an ACK arrives.  Should update the value of
    # self.timeout, as well as the values of self.srtt (smoothed
    # round-trip-time) and self.rttdev (mean linear RTT deviation).

    def calc_timeout(self, packet_timestamp):
        rtt = self.network.time - packet_timestamp
        if self.srtt:
            self.srtt = self.alpha*rtt+(1-self.alpha)*self.srtt
        else:
            self.srtt = rtt
        dev = abs(rtt-self.srtt)
        if self.rttdev:
            self.rttdev = self.beta*dev+(1-self.beta)*self.rttdev
        else:
            self.rttdev = dev
        self.timeout = self.srtt+4*self.rttdev
        self.tracker = self.timeout

    # Send a packet at the current time, with specified seqnum,
    # timestamp.  You do not need to edit this method.
    def send_packet(self, seqnum, pkt_timestamp):
        time = self.network.time
        xmit_packet = self.network.make_packet(
            self.address, self.stream_destination, 'DATA', time, 
            seqnum=seqnum, timestamp=pkt_timestamp)
        self.forward(xmit_packet)
        xmit_packet.start = time
        return xmit_packet

# ReliableReceiverNode extends Router to implement reliable
# receiver functionality with path vector routing.
class ReliableReceiverNode(AbstractReliableReceiverNode):
    def __init__(self,location,qsize,window,address=None):
        AbstractReliableReceiverNode.__init__(self, location, qsize, window,address=address)
        self.reset()

    def reset(self):
        AbstractReliableReceiverNode.reset(self)
        #TODO: Your code for initializing the receiver, if you need
        #any, should go here

    # Invoked every time the receiver receivers a data packet from the
    # receiver.  Sends an ACK back, and does the rest of the necessary
    # processing.  Use self.send_ack() to send an ACK packet, and
    # self.app_receive() to send a data packet to the receiving
    # application. (self.app_receive() is defined in
    # AbstractReliableSenderNode, though you shouldn't need to know
    # anything about its internals.).  self.app_seqnum will tell you
    # the last sequence number that the receiving application received.
    def reliable_recv(self, sender, seqnum, packet_timestamp):
        if seqnum==self.app_seqnum+1:
            self.send_ack(sender,seqnum, packet_timestamp)
            self.app_receive(seqnum)
        else:
            self.send_ack(sender,seqnum, packet_timestamp)
        
    # Send an ACK packet.  You do not need to modify this method.
    def send_ack(self, sender, seqnum, pkt_timestamp):
        time = self.network.time
        ack = self.network.make_packet(self.address, sender, 'ACK', time,
                                       seqnum=seqnum, timestamp=pkt_timestamp)
        self.forward(ack)
