import numpy

from collections import defaultdict

from channel import ChannelEncoder, ChannelDecoder

class ConvolutionalEncoder(ChannelEncoder):

    def __init__(self, G):
        super(ChannelEncoder, self).__init__()
        self.G = G
        self.r, self.K = G.shape
    def multiplier(self,i, received_voltages):
        window = []
        if i<=self.K-2:
            window =[ 0 for j in range(self.K-i-1)] + received_voltages[0:i+1]
            window.reverse()
            window = numpy.array(window)
            tr = numpy.matmul(self.G,window)
            modu = lambda t: t%2
            vfunc = numpy.vectorize(modu)
            temp_result_array = vfunc(tr)
            tr = list(temp_result_array)
        
        else:
            window = received_voltages[i-self.K+1:i+1]
            window.reverse()
            window = numpy.array(window)
            tr = numpy.matmul(self.G, window)
            modu = lambda t: t%2
            vfunc = numpy.vectorize(modu)
            temp_result_array = vfunc(tr)
            tr = list(temp_result_array)
        return tr

    def encode(self, received_voltages):
        N = len(received_voltages)
        result = []
        for i in range(N):
           result+= self.multiplier(i, received_voltages)
        return result

class ViterbiDecoder(ChannelDecoder):

    def __init__(self, G):
        super(ChannelDecoder, self).__init__()
        self.G = G
        self.r, self.K = G.shape
        self.n_states = 2**(self.K-1)      # number of states
        self.states = range(self.n_states) # the states themselves

        # States are kept as integers, not binary strings or arrays.
        # For instance, the state "10" would be kept as "2", "11" as
        # 3, etc.

        # self.predecessor_states[s] = (s1, s2), where s1 and s2 are
        # the two predecessor states for state s (i.e., the two states
        # that have edges into s in the trellis).
        self.predecessor_states = [((2*s+0) % self.n_states, (2*s+1) % self.n_states) for s in self.states]

        # self.expected_parity[s1][s2] = the parity when transitioning
        # from s1 to s2 ('None' if there is no transition from s1 to
        # s2).  This is set up as a dictionary in init, for
        # efficiency.  For inefficiency, you could call
        # calculate_expected_parity() each time.
        self.expected_parity = defaultdict(lambda:defaultdict(float))
        for (s1, s2) in [(s1, s2) for s1 in self.states for s2 in self.states]:
            self.expected_parity[s1][s2] = self.calculate_expected_parity(s1, s2) if s1 in self.predecessor_states[s2] else None

        
        self.PM = None
        self.Predecessor = None

    def calculate_expected_parity(self, from_state, to_state):

        # x[n] comes from to_state
        # x[n-1] ... x[n-k-1] comes from from_state
        x = ((to_state >> (self.K-2)) << (self.K-1)) + from_state

        # Turn the state integer into an array of bits, so that we can
        # xor (essentially) with G

        z = ViterbiDecoder.int_to_bit_array(x, self.K)
        return self.G.dot(z) % 2

    # Converts integers to bit arrays.  Useful if you find it
    # difficult to operate with states that are named as integers
    # rather than bit sequences.  You will likely not need to call
    # this function at all.
    @staticmethod
    def int_to_bit_array(i, length):
        return numpy.array([int(q) for q in (length-len(bin(i)[2:]))*'0'+bin(i)[2:]])

    def viterbi_step(self, n, received_voltages):
        for s in self.states:
            (s1, s2) = self.predecessor_states[s]
            expected1 = self.expected_parity[s1][s]
            expected2 = self.expected_parity[s2][s]
            bm1 = self.branch_metric(expected1, received_voltages)
            bm2 = self.branch_metric(expected2,received_voltages)
            if self.PM[s1,n-1]+bm1 < self.PM[s2,n-1]+bm2:
                self.PM[s,n] = self.PM[s1,n-1]+bm1
                self.Predecessor[s,n]=s1
            else:
                self.PM[s,n] = self.PM[s2,n-1]+bm2
                self.Predecessor[s,n]=s2

    def branch_metric(self, expected, received, soft_decoding=False):
        l = len(expected)
        if not soft_decoding:
            transform = []
            for elt in received:
                if elt>0.5:
                    transform.append(1)
                else:
                    transform.append(0)
            #now find the hamming distance 
            hd = 0
            for i in range(l):
                if transform[i]!= expected[i]:
                    hd+=1
            return hd
        else:
            sum = 0
            for i in range(l):
                sum+= (received[i]-expected[i])**2
            return sum

    def most_likely_state(self, n):
        best_state = list(self.states)[0]
        for s in self.states:
            if self.PM[s,n]<self.PM[best_state,n]:
                best_state = s
        return best_state
    def traceback(self,s,n):
        result = []
        for i in range(n,0,-1):
            prev_state = self.Predecessor[s,i]
            # extracting bits from integers
            temp = prev_state >> 1
            if temp==s:
                result.append(0)
            else:
                result.append(1)
            s = prev_state
        result.reverse()
        result = numpy.array(result)
        return result
        
    def decode(self, received_voltages):

        max_n = (len(received_voltages) // self.r) + 1

        # self.PM is the trellis itself; rows are states, columns are
        # time.  self.PM[s,n] is the metric for the most-likely path
        # through the trellis arriving at state s at time n.
        self.PM = numpy.zeros((self.n_states, max_n))

        # at time 0, the starting state is the most likely, the other
        # states are "infinitely" worse.
        self.PM[1:self.n_states,0] = 1000000

        # self.Predecessor[s,n] = predecessor state for s at time n.
        self.Predecessor = numpy.zeros((self.n_states,max_n), dtype=numpy.int)

        # Viterbi Algorithm:
        n = 0
        for i in range(0, len(received_voltages), self.r):
            n += 1
            # Fill in the next columns of PM, Predecessor based
            # on info in the next r incoming parity bits
            self.viterbi_step(n, received_voltages[i:i+self.r])

        # Find the most-likely ending state, and traceback to
        # reconstruct the message.
        s = self.most_likely_state(n)
        result = self.traceback(s,n)
        return result

