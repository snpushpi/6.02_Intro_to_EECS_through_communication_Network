#!/usr/bin/python

'''Defines different filters to use in the filtering step.'''

import math
import numpy

def averaging_filter(samples, window):
    '''Pass samples through an averaging filter.

    Arguments:
    samples -- samples to average
    window -- window size to use for averaging

    Returns: an array r that is the same size as samples.  r[x] =
    average of samples[x-window] to samples[x], inclusive.  When x <
    window, the averaging window is truncated.
    '''
    x = [0.0]*len(samples)
    for i in range(len(samples)):
        if i-window+1 < 0: # Beginning of the array
            x[i] = numpy.mean(samples[0:i+1])
        else:
            x[i] = numpy.mean(samples[i-window+1:i+1])
    return numpy.array(x)

def low_pass_filter(samples, channel_gap, sample_rate, L=50):
    args1 = numpy.arange(-L, 0) * channel_gap * 2.0 * math.pi / sample_rate
    args2 = numpy.arange(1, L+1) * channel_gap * 2.0 * math.pi / sample_rate
    h_response = numpy.zeros(2*L+1)
    h_response[:L] = numpy.sin(args1)/(math.pi*numpy.arange(-L,0))
    h_response[L]= channel_gap * 2.0 / sample_rate
    h_response[L+1:]=numpy.sin(args2)/(math.pi*numpy.arange(1,L+1))
    return numpy.convolve(h_response,samples)
