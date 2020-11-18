import random,sys,math

from PS8_netsim import *
import PS8_tests

class DVRouter(Router):
    INFINITY = 32

    def send_advertisement(self, time):
        # Do not change this function.  You do not need to modify it.
        adv = self.make_dv_advertisement()
        for link in self.links:
            p = self.network.make_packet(self.address, self.peer(link), 'ADVERT', time, color='red', ad=adv)
            link.send(self, p)        

    def process_advertisement(self, p, link, time):
        # Do not change this function.  You do not need to modify it.
        self.integrate(link, p.properties['ad'])

    def make_dv_advertisement(self):
        # TODO: Your code here
        # Should return a list of the form [(dest1, cost1), (dest2, cost2) ...]
        result_table = []
        for elt in self.cost_table:
            result_table.append((elt,self.cost_table[elt]))
        return result_table

    def link_failed(self, dead_link):
        # Take the appropriate action given that dead_link has failed.
        # The appropriate action will depend on how you design your
        # protocol.
        #
        # If you need to set a cost fo infinity, use self.INFINITY,
        # not INFINITY.
        for dest in self.routes:
            if self.routes[dest]==dead_link:
                self.cost_table[dest]= self.INFINITY
                self.routes[dest]=None
                

    def integrate(self, link, advertisement):
        # At the end of this
        # function, the variables self.cost_table and self.routes
        # should reflect the current shortest paths.
        # 
        # Recall that self.routes maps addresses to instances of the
        # Link class, and self.cost_table maps addresses to the
        # shortest path cost to that node.
        #
        # link is the link that delivered advertisement.  Use
        # link.cost to determine its cost.
        for (dest,cost) in advertisement:
            if dest not in self.cost_table:
                self.cost_table[dest]=cost+link.cost
                self.routes[dest]=link
            elif cost+link.cost<self.cost_table[dest]:
                self.cost_table[dest]=cost+link.cost
                self.routes[dest]=link
            elif self.routes[dest]==link: #when a link's cost changed
                if cost+link.cost!=self.cost_table[dest]:
                    self.cost_table[dest]=cost+link.cost
