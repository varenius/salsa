import matplotlib.pyplot as plt
import numpy as np
import sys
import time


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
    return spec

plt.figure()
datafile = sys.argv[1]
reffile = sys.argv[2]
fftsize = int(sys.argv[3]) # 
plt.title(datafile+ '-' +reffile )
print datafile
halffft = int(0.5*fftsize)
spec = stack_FFT_file(datafile) - stack_FFT_file(reffile)
samp_rate = float(sys.argv[4]) # MSamples/s, i.e. bandwidth is half in MHz.
freqs = 0.5*samp_rate*np.array(range(-halffft,halffft))/(halffft)
plt.plot(freqs,spec)
plt.xlabel('relative to center [Mhz]')

plt.tight_layout()
plt.show()
