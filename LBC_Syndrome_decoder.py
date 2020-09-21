import numpy as np
import sys
import math
from channel import ChannelEncoder, ChannelDecoder

'''
A linear block encoder is just one type of channel encoder; we'll look
at another in PS3.
'''
class ChannelEncoder():

    def __init__(self):
        pass

    def encode(self, bits):
        raise NotImplementedError()

class ChannelDecoder():

    def __init__(self):
        pass

    def decode(self, bits):
        raise NotImplementedError()

class BlockEncoder(ChannelEncoder):

    def __init__(self):
        super(BlockEncoder, self).__init__()

    '''
    Here, you should implement the linear encoder. The input, bits,
    will be a numpy array of integers (each integer is 0 or 1).
    '''
    def encode(self, A, bits):
        k, m = A.shape
        k_N = bits.shape[0]
        N = k_N//k
        bits = bits.reshape((N,k))
        #create identity matrix
        I = np.identity(k)
        G = np.concatenate((I,A), axis=1)
        new_arr =  np.matmul(bits,G)
        modu = lambda t: t%2
        vfunc = np.vectorize(modu)
        temp_result_array = vfunc(new_arr)
        result_array = temp_result_array.ravel()
        return result_array

def syndrome_dictionary_maker(H):
    #we will consider m+k+1 different type of vectors shifting exactly one 1 and one vector will be of all zeros
    m, kplusm = H.shape
    syndrome_dictionary = {}
    t = ()
    for i in range(kplusm):
        t+=(0,)
    for i in range(kplusm):
        temp_tup = t[:i]+(1,)+t[i+1:]
        list1 = list(temp_tup)
        arr = np.array(list1)
        n = arr.shape[0]
        arr = arr.reshape((n,1))
        res = np.matmul(H,arr)
        syndrome_dictionary[tuple(map(tuple,res))]=i
    zer = np.zeros((kplusm,1))
    syndrome_dictionary[tuple(map(tuple,zer))]='no change'
    return syndrome_dictionary
def flip(bit):
    if bit==1:
        return 0
    if bit==0:
        return 1

class SyndromeDecoder(ChannelDecoder):

    def __init__(self):
        super(ChannelDecoder, self).__init__()

    '''
    Here you should implement the syndrome decoder.
    
    Please set up the syndrome table before you perform the decoding
    (feel free to set up a different function to do this).  This will
    result in a more organized design, and also a more efficient
    decoding procedure (because you won't be recalculating the
    syndrome table for each codeword).
    '''

    def decode(self, A, bits):
        k, m = A.shape
        A_T = np.transpose(A)
        I_m = np.identity(m)
        H = np.concatenate((A_T,I_m),axis=1)
        k_N = bits.shape[0]
        N = k_N//(k+m)
        bits = bits.reshape((N,k+m))
        res = np.matmul(H,np.transpose(bits))
        res_T = np.transpose(res)
        modu = lambda t: t%2
        vfunc = np.vectorize(modu)
        res_T = vfunc(res_T)
        res_T_list = res_T.tolist()
        final_result_list = bits[:,:k]
        syndrome_dictionary = syndrome_dictionary_maker(H)
        for i in range(len(res_T_list)):
            l_np = np.array(res_T_list[i])
            n = l_np.shape[0]
            l_np = l_np.reshape((n,1))
            if not np.array_equal(l_np,np.zeros((n,1))):
                col_num = syndrome_dictionary[tuple(map(tuple,l_np))]
                if col_num<=k-1:
                    final_result_list[i,col_num] = flip(final_result_list[i,col_num])
        
        return final_result_list.ravel()



