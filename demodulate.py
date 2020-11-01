#!/usr/bin/python

'''Defines different demodulators to use in the demodulation step.'''

import math
import numpy 

import util

def envelope_demodulator(samples):
    '''Perform envelope demodulation on a set of samples (i.e., rectify
    the samples).

    Arguments:
    samples -- array of samples to demodulate'''
    return numpy.abs(samples)

def heterodyne_demodulator(samples, sample_rate, carrier_freq):
    
    args = numpy.arange(0, len(samples)) * carrier_freq * 2.0 * math.pi / sample_rate
    return samples*numpy.cos(args)


def quadrature_demodulator(samples, sample_rate, carrier_freq):
    return [samples[n]*numpy.power(numpy.e,2j*numpy.pi*carrier_freq*n/sample_rate) for n in range(len(samples))]
    

