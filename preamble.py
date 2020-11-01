import math
import numpy
import util

from receiver import Receiver

class Preamble:
    '''
    This class defines the preamble that appears at the beginning of
    every transmission.  The preamble is comprised of a known bit
    sequence, possibly preappended with some samples of silence.
    '''

    def __init__(self, config):
        '''
        config contains the config options for this system.  Preamble
        gets the number of silent samples, if any, from this.
        '''
#        self.data = [1,0,1,1,0,1,1,1,0,0,0,1,1,1,1,1,0,0,1,1,0,1,0,1]
        self.data = [1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1]
        if config is None:
            self.silence = 0
        else:
            self.silence = config.n_silent_samples
            if config.skip_preamble:
                self.data = []
        self.preamble = numpy.append([0]*self.silence, self.data)

    def preamble_data_len(self):
        '''
        Returns the length of the preamble data bits
        '''
        return len(self.data)

    def detect(self, demodulated_samples, receiver, offset_hint, zero, one):
        '''
        Detects the preamble in an array of demodulated samples.

        Arguments:
        demodulated_samples = numpy.array of demodulated samples

        receiver = Receiver associated with the reception of the
        demodulated samples.  Used to access the samples per bit,
        sample rate, and carrier frequency of this data.

        offset_hint = our best guess as to where the first 1 bit in
        the samples begins

        zero = best guess for V_0 for these samples
        one = best guess for V_1 for these samples

        Returns:
        The index (as an int) into demodulated_samples where the
        preamble is most likely to start.
        '''

        preamble_samples = util.bits_to_samples(self.data, receiver.spb, zero, one)
        modulated_samples = util.modulate(receiver.fc, preamble_samples, receiver.sample_rate)
        digitized_data = receiver.demodulate_and_filter(modulated_samples)
        return offset_hint + self.correlate(digitized_data,demodulated_samples[offset_hint:])

    def correlate(self, x, y):
        '''
        Calculate correlation between two arrays.
        
        Arguments:
        x, y: numpy arrays to be correlated

        Returns:
        - If len(x) == 0 or len(x) > len(y), returns 0
        - Else, returns the index into y representing the most-likely
          place where x begins.  "most-likely" is defined using the
          normalized dot product between x and y
        '''
        
        if len(x) > len(y) or len(x) == 0:
            return 0
        return max(range(len(y)-len(x)+1), key = lambda i: numpy.dot(y[i:i+len(x)],x)/numpy.linalg.norm(y[i:i+len(x)]))
