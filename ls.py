import random,sys,math
from optparse import OptionParser
from PS8_netsim import *
import PS8_tests

# Students -- Do not be alarmed by the number of functions in this
# file.  You only need to modify two of them.

class LSRouter(Router):
    INFINITY = sys.maxsize

    def __init__(self,location,address=None):
        # Do not change this function.  You don't need to modify it.
        Router.__init__(self, location, address=address)
        self.LSA = {}
        self.LSA_seqnum = 0

    def send_lsa(self, time):
        # Do not change this function.  You don't need to modify it.
        self.LSA_seqnum += 1
        lsa_info = self.make_ls_advertisement()
        for link in self.links:
            p = self.network.make_packet(self.address, self.peer(link),  'ADVERT', time, color='red', seqnum=self.LSA_seqnum, neighbors=lsa_info)
            link.send(self, p)

    def send_advertisement(self, time):
        # Do not change this function.  You don't need to modify it.
        self.send_lsa(time)
        self.clear_stale_lsa(time)

    def clear_stale_lsa(self, time):
        # Do not change this function.  You don't need to modify it.
        for key,value in self.LSA.items():
            if value[0] < self.LSA_seqnum-1:
                del self.LSA[key]

    def process_advertisement(self, p, link, time):
        # Do not change this function.  You don't need to modify it.
        seq = p.properties['seqnum']
        saved = self.LSA.get(p.source, (-1,))
        if seq > saved[0]:
            if p.properties['neighbors'] is not None:
                self.LSA[p.source] = [seq] + p.properties['neighbors']
            else:
                print(p.properties)
                print('Malformed LSA: No LSA neighbor information in packet.  Exiting...')
                sys.exit(1)
            for link in self.links:
                link.send(self, self.network.duplicate_packet(p))

    def get_all_nodes(self):
        # Do not change this function.  You don't need to modify it.
        nodes = [self.address]
        for u in nodes:
            if self.LSA.get(u) != None:
                lsa_info = self.LSA[u][1:]
                for i in range(len(lsa_info)):
                    v = lsa_info[i][0]
                    if not v in nodes:
                        nodes.append(v)
        return nodes

    def transmit(self, time):
        # Do not change this function.  You don't need to modify it.
        Router.transmit(self, time)
        if (time % self.ADVERT_INTERVAL) == self.ADVERT_INTERVAL/2:
            self.integrate(time)

    def OnClick(self,which):
        # Do not change this function.  You don't need to modify it.
        if which == 'left':
            print(self)
            print('  LSA:')
            for (key,value) in self.LSA.items():
                print('    ',key,': ',value)
        Router.OnClick(self,which)

    def integrate(self, time):
        # Do not change this function.  You don't need to modify
        # it. (the real work is done in run_dijkstra, which you *do*
        # need to modify)
        self.routes.clear()
        self.routes[self.address] = 'Self'
        self.LSA[self.address] = [self.LSA_seqnum] + self.make_ls_advertisement()
        nodes = self.get_all_nodes()
        self.cost_table = {}
        for u in nodes:
            self.cost_table[u] = self.INFINITY
        self.cost_table[self.address] = 0 # path cost to myself is 0
        self.run_dijkstra(nodes)

    def make_ls_advertisement(self):
        # Should return a list of the form [(dest1, cost1), (dest2,
        # cost2) ...].  The variable self.neighbors will be helpful.
        res_list = []
        for neighbor in self.neighbors: #(,adress,cost)
            res_list.append((self.neighbors[neighbor][1],self.neighbors[neighbor][2]))
        return res_list

    def run_dijkstra(self, nodes):
        # Use self.LSA to get the topology information for this
        # network (see the lab write-up for details).  Remember that
        # self.routes maps node addresses to links.  If you need
        # access the link out of this Router to another node, use
        # self.getlink().
        # 1. find your minimum node
        # 2. update the costs of other nodes using that node - self.LSA[min_node]
        while nodes!=[]:
            #print(nodes)
            min_node = None
            min_value = float('inf')
            for node in nodes: 
                if self.cost_table[node]<min_value:
                    min_node = node
                    min_value = self.cost_table[node]
            nodes.remove(min_node)
            min_node_neighbor_list = self.LSA[min_node][1:]
            #router_to_min_node_link = self.getlink(min_node) 
            #print(router_to_min_node_link)
            if min_node!=self.address:
                for (neighbor,cost) in min_node_neighbor_list:
                    if neighbor not in self.cost_table:
                        self.cost_table[neighbor]=min_value+cost
                        self.routes[neighbor]= self.routes[min_node]
                    elif cost+min_value<self.cost_table[neighbor]:
                        self.cost_table[neighbor]=min_value+cost
                        self.routes[neighbor]=self.routes[min_node]
                    elif self.routes[neighbor]==self.routes[min_node]:
                        if cost+min_value!=self.cost_table[neighbor]:
                            self.cost_table[neighbor]=cost+min_value
            elif min_node==self.address:
                for (neighbor,cost) in min_node_neighbor_list:
                    self.cost_table[neighbor]=cost
                    self.routes[neighbor]=self.getlink(neighbor)
                    
        
        




