import matplotlib.pyplot as plt
import numpy as np
import sys
import time


datafile = sys.argv[1]
fftsize = int(sys.argv[2]) # 
samp_rate = float(sys.argv[3]) # MSamples/s, i.e. bandwidth is half in MHz.
cfreq = float(sys.argv[4])
outfile = sys.argv[5]

def stack_FFT_file(infile):
    # Load FFT segments as memory mapped file in case it is large
    signal = np.memmap(infile, mode = 'r', dtype=np.float32)
    # Find out number of loops needed for this file
    nsegs = int(signal.size/fftsize)
    # Initialize empty array for storing stacked spectrum
    spec = np.zeros(fftsize, dtype = np.float32)
    for seg in range(nsegs):
        # Read segment of large memory mapped file
        spec += np.array(signal[fftsize*seg:fftsize*(seg+1)])
    del signal
    # Normalise power spectrum to be invariant of
    # integration time
    spec = spec/(1.0*nsegs)
    return spec

halffft = int(0.5*fftsize)
spec = stack_FFT_file(datafile)
freqs = 0.5*samp_rate*np.array(range(-halffft,halffft))/(halffft)
f = open(outfile, 'w')
a = np.array([spec, samp_rate, fftsize, cfreq])
np.save(f, a)

