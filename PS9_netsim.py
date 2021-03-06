import random, sys,  math, time

################################################################################
#
# Node -- a network node
#
# Node.reset()        -- reset node's state at start of simulation
# Node.add_packet(p)  -- add packet to node's transmit queue
# Node.receive(p)     -- called to process packet sent to this node
# Node.transmit(time) -- allow node to send packets at current time
# Node.forward(p)     -- lookup route for pkt p and send it on appropriate link
# Node.arrived_on(p)  -- returns link that packet p just arrived on
#
################################################################################

class Node:
    def __init__(self,location,address=None):
        self.location = location
        if address is None: self.address = location
        else: self.address = address
        self.links = []  # links that connect to this node
        self.packets = []  # packets to be processed this timestep
        self.transmit_queue = []  # packets to be transmitted from this node
        self.receive_queue = []  # packets received by this node
        self.properties = {}
        self.network = None  # will be filled in later
        self.nsize = 0       # filled in by draw method

    def __repr__(self):
        return 'Node<%s>' % str(self.address)

    def address(self):
        return self.address

    # reset to initial state
    def reset(self):
        for l in self.links: l.reset()
        self.transmit_queue = []   # nothing to transmit
        self.receive_queue = []    # nothing received
        self.queue_length_sum = 0  # reset queue statistics
        self.queue_length_max = 0
#	self.neighbors.clear()
#        self.routes.clear()
        self.routes[self.address] = 'Self'
        self.properties.clear()

    # keep track of links that connect to this node
    def add_link(self,l):
        self.links.append(l)

    # add a packet to be transmitted from this node.  Transmit queue
    # is kept ordered by packet start time.
    def add_packet(self,p):
        index = 0
        for pp in self.transmit_queue:
            if p.start < pp.start:
                self.transmit_queue.insert(index,p)
                break
            else: index += 1
        else: self.transmit_queue.append(p)

    # first phase of simulation timestep: collect one packet from
    # each incoming link
    def phase1(self):
        self.packets = [link.receive(self) for link in self.links]

    # second phase of simulation timestep: process arriving packets    
    def phase2(self,time):
        # process each arriving packet
        for link_p in self.packets:
            if link_p is not None: self.process(link_p[1],link_p[0],time)
        self.packets = []

        # give this node a chance to transmit some packets
        self.transmit(time)

        # compute number of packets this node has queued up on its
        # outgoing links.  So we can compute queue length stats, keep
        # track of max and sum.
        pending = 0
        for link in self.links: pending += link.queue_length(self)
        self.queue_length_sum += pending
        self.queue_length_max = max(self.queue_length_max,pending)

        # report total number of packets that need processing
        return pending + len(self.transmit_queue)

    # default processing for packets addressed to this node -- just
    # keep a list of them
    def receive(self,p,link,time):
        self.receive_queue.append(p)

    # called each simulation cycle to give this node a chance to send
    # some packets.  Default behavior: source packets from a transmit
    # queue based on packets' specified start time.
    def transmit(self,time):
        # look for packets on this node's transmit queue whose time has come
        while len(self.transmit_queue) > 0:
            if self.transmit_queue[0].start <= time:
                self.process(self.transmit_queue.pop(0),None,time)
            else: break

    # OVERRIDE: forward packet onto proper outgoing link.  Default behavior
    # is to pick a link at random!
    def forward(self,p):
        link = random.choice(self.links)
        link.send(self,p)

    # deal with each packet arriving at or sent from this node
    def process(self,p,link,time):
        if p.destination == self.address:
            # it's for us!  Just note time of arrival and pass it receive
            p.finish = time
            self.receive(p,link,time)
        else:
            p.add_hop(self,time)
            self.forward(p)

    #########################################################
    # support for graphical simulation interface
    #########################################################

    # convert our location to screen coordinates
    def net2screen(self,transform):
        return net2screen(self.location,transform)

    # if pos is near us, return status string
    def nearby(self,pos):
        dx = self.location[0] - pos[0]
        dy = self.location[1] - pos[1]
        if abs(dx) < .1 and abs(dy) < .1:
            return self.status()
        elif len(self.transmit_queue) > 0:
            if (dx > .1 and dx < .2) and (dy > .1 and dy < .2):
                return 'Unsent '+self.transmit_queue[0].status()
        else:
            return None

    def click(self,pos,which):
        dx = self.location[0] - pos[0]
        dy = self.location[1] - pos[1]
        if abs(dx) < .1 and abs(dy) < .1:
            self.OnClick(which)
            return True
        else:
            return False

    def OnClick(self,which):
        pass
        
    # status report to appear in status bar when pointer is nearby
    def status(self):
        return self.__repr__()

################################################################################
#
# Link -- a communication link between two network nodes
#
# Link.queue_length(n) -- count undelivered packets sent by specified node
# Link.other_end(n)    -- return node at other end of link
# Link.receive(n)      -- return one packet destined for specified node (or None)
# Link.send(n,p)       -- send packet to other end of link
#
################################################################################
class Link:
    def __init__(self,n1,n2):
        self.end1 = n1   # node at one end of the link
        self.end2 = n2   # node at the other end
        self.q12 = []    # queue of packets to be delivered to end2
        self.q21 = []    # queue of packets to be delivered to end1
        self.cost = 1    # by default, cost is 1
        self.costrepr = str(self.cost) # representing cost in GUI
        self.rate = 1      # number of pkts/slot (same in each direction)
        self.pending = []  # packets that have yet to be sent on link
        self.credits = 0.0 # deficit round robin to send pkts at "rate"
        self.network = None     # will be filled in later
        n1.add_link(self)
        n2.add_link(self)
        self.broken = False

    def __repr__(self):
        return 'link(%s<-->%s) (%.1f)' % (self.end1,self.end2, self.cost)

    def reset(self):
        self.q12 = []    # reset packet queues
        self.q21 = []
        self.credits = 0.0

    # return count of undelivered packets sent by specified node
    def queue_length(self,n):
        if n == self.end1: return len(self.q12)
        elif n == self.end2: return len(self.q21)
        else: raise Exception('bad node in Link.queue_length')

    # return (link, packet) destined for specified node (or None)
    def receive(self,n):
        if n == self.end1:
            if len(self.q21) == 0: self.credits21 = 0.0
            else: self.credits21 = self.credits21 + self.rate
            if len(self.q21) > 0 and self.credits21 >= 1.0: 
                self.credits21 = self.credits21 - 1 # we shipped a packet
                return (self, self.q21.pop(0))
            else: return None
        elif n == self.end2:
            if len(self.q12) == 0: self.credits12 = 0.0
            else: self.credits12 = self.credits12 + self.rate
            if len(self.q12) > 0 and self.credits12 >= 1.0: 
                self.credits12 = self.credits12 - 1 # we shipped a packet
                return (self, self.q12.pop(0))
            else: return None
        else: raise Exception('bad node in Link.receive')

    # send one packet from specified node
    def send(self,n,p):
        if self.broken: return
        if n == self.end1: self.q12.append(p)
        elif n == self.end2: self.q21.append(p)
        else: raise Exception('bad node in Link.send')

    def set_rate(self,rate):
        self.rate = rate

    #########################################################
    # support for graphical simulation interface
    #########################################################

    def draw(self,dc,transform):
        self.nsize = transform[0]/16
        n1 = self.end1.net2screen(transform)
        n2 = self.end2.net2screen(transform)

    def nearby(self,pos):
        # check for packet icons
        msg = None
        if len(self.q21) > 0:
            msg = self.q21[0].nearby(pos,self.end1.location,self.end2.location)
        if msg is None and len(self.q12) > 0:
            msg = self.q12[0].nearby(pos,self.end2.location,self.end1.location)
        return msg

    def click(self,pos,which):
        if nearby(pos,self.end1.location,self.end2.location,.1):
            self.broken = not self.broken
            if self.broken:
                self.reset()
            return True
        return False

######################################################################
"""A link with cost (higher cost means worse link)
"""
######################################################################
class CostLink(Link):
    def __init__(self,n1,n2):
        Link.__init__(self,n1,n2)
        self.nsize = 0                # filled in by draw method
        loc1 = n1.location
        loc2 = n2.location
        dx2 = (loc1[0] - loc2[0])*(loc1[0] - loc2[0])
        dy2 = (loc1[1] - loc2[1])*(loc1[1] - loc2[1])
        self.cost = math.sqrt(dx2 + dy2)
        if (int(self.cost) == self.cost): 
            self.costrepr = str(self.cost)
        else:
            self.costrepr = "sqrt(" + str(dx2+dy2) + ")"

class LossyLink(Link):
    def __init__(self,n1,n2,lossprob):
        Link.__init__(self,n1,n2)
        self.lossprob = lossprob # probability packet gets dropped
        self.linkloss = 0        # number of packets dropped on link

    # send one packet from specified node
    # but drop a few along the way!
    def send(self,n,p):
        # we lose packets with probability self.lossprob
        # to make life easy on ourselves, let's pretend we only lose
        # DATA or ACK packets
        if (p.type!='DATA' and p.type!='ACK') or \
                random.random() > self.lossprob:
            Link.send(self,n,p)
        else:
            self.linkloss = self.linkloss + 1
            if self.network.verbose == True:
                print('Dropping packet %s: seqnum=%s'% (p,str(p.properties.get('seqnum','???'))))

################################################################################
#
# Packet -- data to be sent from one network node to another
#
# Packet.arrived_from() -- return node this packet just arrived from
#
################################################################################
class Packet:
    def __init__(self, src, dest, type, start, **props):
        self.source = src     # address of node that originated packet
        self.destination = dest  # address of node that should receive packet
        self.type = type
        self.start = start # simulation time at which packet was transmitted
        self.finish = None # simulation time at which packet was received
        self.route = []    # list of nodes this packet has visited
        self.network = None     # will be filled in later
        self.properties = props.copy()

        try:
            self.seqnum = self.properties.get("seqnum", None)
        except:
            pass
        
        try:
            self.timestamp = self.properties.get("timestamp", None)
        except:
            pass

    def __repr__(self):
        return 'Packet<%s to %s> type %s %s' % (self.source,self.destination,self.type, self.properties)

    # keep track of where we've been
    def add_hop(self,n,time):
        self.route.append((n,time))

    def nearby(self,pos,n1,n2):
        px = n1[0] + 0.2*(n2[0] - n1[0])
        py = n1[1] + 0.2*(n2[1] - n1[1])
        dx = px - pos[0]
        dy = py - pos[1]
        if abs(dx) < .1 and abs(dy) < .1:
            return self.status()
        else: return None

    def status(self):
        return self.__repr__()        

################################################################################
#
# Network -- a collection of network nodes, links and packets
#
# Network.make_node(loc,address=None)  -- make a new network node
# Network.add_node(x,y,address=None)   -- add a new node at specified location
# Network.find_node(x,y)               -- return node at given location
# Network.map_node(f,default=0)        -- see below
# Network.make_link(n1,n2)             -- make a new link between n1 and n2
# Network.add_link(x1,y2,x2,y2)        -- add link between specified nodes
#
# Network.make_packet(src,dst,type,start,**props)  -- make a new packet
# Network.duplicate_packet(p)          -- duplicate a packet
#
# Network.reset()                      -- initialize network state
# Network.step(count=1)                -- simulate count timesteps
#
################################################################################
class Network:
    def __init__(self,simtime):
        self.nodes = {}
        self.addresses = {}
        self.nlist = []
        self.links = []
        self.time = 0
        self.pending = 0
        self.packets = []
        self.npackets = 0
        self.max_x = 0
        self.max_y = 0
        self.simtime = simtime
        self.playstep = 1.0     # 1 second play step by default

        self.numnodes = 0       # TBD

    # override to make your own type of node
    def make_node(self,loc,address=None):
        return Node(loc,address=address)

    # add a node to the network
    def add_node(self,x,y,address=None):
        n = self.find_node(x,y)
        if n is None:
            n = self.make_node((x,y),address=address)
            n.network = self
            if address is not None:
                self.addresses[address] = n
            self.nlist.append(n)
            ynodes = self.nodes.get(x,{})
            ynodes[y] = n
            self.nodes[x] = ynodes
            self.max_x = max(self.max_x,x)
            self.max_y = max(self.max_y,y)
        return n

    def set_nodes(self,n):
        self.numnodes = n

    # locate a node given its location
    def find_node(self,x,y):
        ynodes = self.nodes.get(x,None)
        if ynodes is not None:
            return ynodes.get(y,None)
        return None

    # apply f to each network node in top-to-bottom, left-to-right
    # order.  Returns list of return values (default value is used
    # if a particular grid point doesn't contain a node).  Useful
    # for gathering statistical data that can be processed by Matlab.
    def map_node(self,f,default=0):
        result = []
        for row in range(self.max_y+1):
            for col in range(self.max_x+1):
                node = self.find_node(row,col)
                if node: result.append(f(node))
                else: result.append(default)
        return result

    # override to make your own type of link
    def make_link(self,n1,n2):
        return Link(n1,n2)

    # add a link between nodes at the specified locations
    def add_link(self,x1,y1,x2,y2):
        n1 = self.find_node(x1,y1)
        n2 = self.find_node(x2,y2)
        if n1 is not None and n2 is not None:
            link = self.make_link(n1,n2)
            link.network = self
            self.links.append(link)

    # override to make your own type of packet
    def make_packet(self,src,dest,type,start,**props):
        p = Packet(src,dest,type,start,**props)
        p.network = self
        p.start = start
        self.packets.append(p)
        self.npackets += 1
        return p

    # duplicate existing packet
    def duplicate_packet(self,old):
        return self.make_packet(old.source,old.destination,old.type,self.time,
                                **old.properties)

    # compute manhattan distance between two nodes
    def manhattan_distance(self,n1,n2):
        dx = n1[0] - n2[0]
        dy = n1[1] - n2[1]
        return abs(dx) + abs(dy)

    # return network to initial state
    def reset(self):
        for n in self.nlist: n.reset()
        self.time = 0
        self.pending = 0
        self.packets = []
        self.npackets = 0
        self.pending = 1    # ensure at least simulation step

    # simulate network one timestep at a time.  At each timestep
    # each node processes one packet from each of its incoming links
    def step(self,count=1):
        stop_time = self.time + count
        while self.time < stop_time and self.pending > 0:
            # phase 1: nodes collect one packet from each link
            for n in self.nlist: n.phase1()
            # phase 2: nodes process collected packets, perhaps sending
            # some to outgoing links.  Also nodes can originate packets
            # of their own.
            self.pending = 0
            for n in self.nlist: self.pending += n.phase2(self.time)

            # increment time
            self.time += 1
        return self.pending

    #########################################################
    # support for graphical simulation interface
    #########################################################

    def draw(self,dc,transform):
        # draw links
        for link in self.links:
            link.draw(dc,transform)

        # draw nodes
        for node in self.nlist:
            node.draw(dc,transform)

    def click(self,pos,which):
        for node in self.nlist:
            if node.click(pos,which):
                return True
        else:
            for link in self.links:
                if link.click(pos,which):
                    return True
        return False

    def status(self,statusbar,pos):
        for node in self.nlist:
            msg = node.nearby(pos)
            if msg: break
        else:
            for link in self.links:
                msg = link.nearby(pos)
                if msg: break
            else:
                msg = ''
        statusbar.SetFieldsCount(4)
        statusbar.SetStatusWidths([80,80,80,-1])
        statusbar.SetStatusText('Time: %d' % self.time, 0)
        statusbar.SetStatusText('Pending: %s' % self.pending, 1)
        statusbar.SetStatusText('Total: %s' % self.npackets, 2)
        statusbar.SetStatusText('Status: %s' % msg, 3)

grid_node_names = ['alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot',
             'golf', 'hotel', 'india', 'juliet', 'kilo', 'lima', 'mike',
             'november', 'oscar', 'papa', 'quebec', 'romeo', 'sierra',
             'tango', 'uniform', 'victor', 'whiskey', 'xray', 'yankee',
             'zulu']

class GridNetwork(Network):
    # make a grid network of specified size
    def __init__(self,nrows,ncols):
        Network.__init__(self)

        # make a manhattan grid of nodes
        for r in range(nrows):
            for c in range(ncols):
                index = r*ncols + c
                addr = grid_node_names[index % len(grid_node_names)]
                if index >= len(grid_node_names):
                    addr += str(index / len(grid_node_names))
                self.add_node(r,c,address=addr)

        for r in range(nrows):
            # horizontal links first
            for c in range(ncols):
                if c > 0: self.add_link(r,c,r,c-1)
            # then vertical links
            for c in range(ncols):
                if r > 0: self.add_link(r,c,r-1,c)

################################################################################
#
# NetSim -- a graphical front end for network simulations
#
################################################################################

# convert from network to screen coords
# transform = (scale,(xoffset,yoffset))
def net2screen(loc,transform):
    return (transform[1][0]+loc[0]*transform[0],
            transform[1][1]+loc[1]*transform[0])

# convert from screen to network coords
# transform = (scale,(xoffset,yoffset))
def screen2net(loc,transform):
    return (float(loc[0]-transform[1][0])/transform[0],
            float(loc[1]-transform[1][1])/transform[0])

# is pt within distance of line between end1 and end2?
def nearby(pt,end1,end2,distance):
    if end1[0] == end2[0]:    # vertical wire
        if abs(pt[0] - end1[0]) > distance:
            return False
        y1 = min(end1[1],end2[1])
        y2 = max(end1[1],end2[1])
        return pt[1] >= y1 - distance and pt[1] <= y2 + distance
    elif end1[1] == end2[1]:  # horizontal wire
        if abs(pt[1] - end1[1]) > distance:
            return False
        x1 = min(end1[0],end2[0])
        x2 = max(end1[0],end2[0])
        return pt[0] >= x1 - distance and pt[0] <= x2 + distance
    else:  # non-manhattan wire
        # slope and intercept for line between end1 and end2
        slope1 = float(end1[1] - end2[1])/(end1[0] - end2[0])
        intercept1 = float(end1[1]) - slope1*end1[0]
        # slope and intercept for perpendicular line passing through pt
        slope2 = -1/slope1
        intercept2 = float(pt[1]) - slope2*pt[0]
        # x coordinate of intersection of those two lines
        xi = (intercept2 - intercept1)/(slope1 - slope2)
        if xi < min(end1[0],end2[0]) or xi > max(end1[0],end2[0]):
            return False
        dx = pt[0] - xi;
        dy = pt[1] - (slope2*xi + intercept2)
        return (dx*dx) + (dy*dy) <= distance*distance        



"""Skeleton for link-state routing lab in 6.082
"""
# use our own node class derived from the node class of network10.py
# so we can override routing behavior
class Router(Node):
    HELLO_INTERVAL = 5   # time between HELLO packets
    ADVERT_INTERVAL = 50  # time between route advertisements
        
    def __init__(self,location,qsize,address=None):
        Node.__init__(self, location, address=address)
        # additional instance variables
        self.neighbors = {}     # Link -> (timestamp, address, linkcost)
        self.routes = {}        # address -> Link
        self.routes[self.address] = 'Self'
        self.spcost = {}        # address -> shortest path cost to node
        self.spcost[self.address] = 0
        if qsize == 0:
            self.qsize = self.INFINITY
        else:
            self.qsize = qsize
        self.qdrop = 0

    def reset(self):
        Node.reset(self)
        self.properties = {}
        self.spcost[self.address] = 0

    def __repr__(self):
        return 'Router<%s>' % str(self.address)

    # return the link corresponding to a given neighbor, nbhr
    def getlink(self, nbhr):
        if self.address == nbhr: return None
        for l in self.links: 
            if l.end2.address == nbhr or l.end1.address == nbhr:
                return l
        return None

    def peer(self, link):
        if link.end1.address == self.address: return link.end2.address
        if link.end2.address == self.address: return link.end1.address

    # use routing table to forward packet along appropriate outgoing link
    def forward(self,p):
        link = self.routes.get(p.destination, None)
        if link is None:
            print('No route for ',p,' at node ',self)
        else:
            # drop packet if the queue is already full
            if link.queue_length(self) >= self.qsize: 
                if self.network.verbose:
                    print("time ", self.network.time, ": ", self, " queue full (dropping pkt)")
                self.qdrop = self.qdrop + 1
                return
            link.send(self, p)   

    def process(self,p,link,time):
        Node.process(self, p, link, time)

    def transmit(self, time):
        return

    def OnClick(self,which):
        if which == 'left':
            #print whatever debugging information you want to print
            print(self)
            print('  neighbors:',self.neighbors.values())
            print('  routes:')
            for (key,value) in self.routes.items():
                print('    ',key,': ',value)

class CrossTrafficNode(Router):
    def __init__(self,location,qsize,address,xrate,dest):
        self.dest = dest
        self.xrate = xrate
        self.total_cross = 0
        Router.__init__(self,location,qsize,address)
        print(self.address)

    def __repr__(self):
        return 'CrossTrafficNode<%s>' % str(self.address)

    def transmit(self, time):
        if random.random() <= self.xrate:
            # time to send!
            self.total_cross = self.total_cross + 1
            xmit_pkt = self.network.make_packet(self.address, self.dest, 
                                                'DATA', time, 
                                                timestamp=time)
            self.forward(xmit_pkt)

# Network with link costs.  By default, the cost of a link is the 
# Euclidean distance between the nodes at the ends of the link
class RouterNetwork(Network):
    def __init__(self,SIMTIME,NODES,LINKS):
        Network.__init__(self,SIMTIME)

        for n,r,c in NODES:
            self.add_node(r,c,address=n)
        for a1,a2 in LINKS:
            n1 = self.addresses[a1]
            n2 = self.addresses[a2]
            self.add_link(n1.location[0],n1.location[1],
                          n2.location[0],n2.location[1])
    
    # nodes should be an instance of LSNode (defined above)
    def make_node(self,loc,address=None):
        return Router(loc,address=address)

    def make_link(self,n1,n2):
        return CostLink(n1,n2)

    def add_cost_link(self,x1,y1,x2,y2):
        n1 = self.find_node(x1,y1)
        n2 = self.find_node(x2,y2)
        if n1 is not None and n2 is not None:
            link = self.make_cost_link(n1,n2)
            link.network = self
            self.links.append(link)

"""Random graph generator
"""

class RandomGraph:
    def __init__(self,numnodes=12):
        self.numnodes = numnodes
        if self.numnodes > 26:
            print("Maximum number of nodes = 26")
            self.numnodes = 26
        elif self.numnodes < 12:
            print("Minimum number of nodes = 12")
            self.numnodes = 12
        
        self.names = ['S', 
                      'A', 'B', 'C', 'D', 'E',
                      'F', 'G', 'H', 'I', 'J',
                      'R',
                      'K', 'L', 'M', 'N', 'O',
                      'P', 'Q', 'T',
                      'U', 'V', 'W', 'X', 'Y', 'Z']
        self.maxRows = math.ceil(math.sqrt(self.numnodes))
        self.maxCols = math.ceil(math.sqrt(self.numnodes))

    def getCoord(self, i):
        x= i % self.maxCols
        y = math.floor(i/self.maxCols)
        return (x,y)
    
    def getIndex(self, x, y):
        if x<0 or y < 0 or x>=self.maxCols or y>=self.maxRows:
            return -1
        ind = y*self.maxCols + x    
        if ind < self.numnodes:
            return ind
        else:
            return -1
        
    def getAllNgbrs(self, i):
        (x,y) = self.getCoord(i)
        ngbrs = []
        ngbrsX = [x-1, x, x+1]
        ngbrsY = [y-1, y, y+1]
        for nx in ngbrsX:
            for ny in ngbrsY:
                if not (nx==x and ny == y):
                    ind = self.getIndex(nx, ny)
                    if ind>=0:
                        ngbrs.append(ind)
        return ngbrs
    
    def checkLinkExists(self, links, a, b):
        for (c,d) in links:
            if a==c and b==d:
                return True
            if a==d and b==c:
                return True
        return False
    
    def genGraph(self):
        NODES = []
        LINKS = []
        
        for i in range(self.numnodes):
            (x,y) = self.getCoord(i)
            name = self.names[i]
            NODES.append((name,x,y))
        
        for i in range(self.numnodes):
            ngbrs = self.getAllNgbrs(i)
            outdeg = int(random.random()*len(ngbrs)) + 1
            sampleNgbrs = random.sample(ngbrs, outdeg)
            for n1 in sampleNgbrs:
                n = int(n1)
                if not self.checkLinkExists(LINKS, self.names[i], self.names[n]):
                    LINKS.append((self.names[i], self.names[n]))

        return (NODES, LINKS)

