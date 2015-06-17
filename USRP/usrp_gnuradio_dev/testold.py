import matplotlib.pyplot as plt
import numpy as np
import sys
import time
import scipy.interpolate as ip

infile = sys.argv[1]
indata = np.load(infile)
spec = indata[0]
samp_rate = indata[1]
fftsize = indata[2]
center_freq = 1419.4 # MHz

halffft = int(0.5*fftsize)
freqs = 0.5*samp_rate*np.array(range(-halffft,halffft))/(halffft)
#plt.plot(spec)
delta_nu = samp_rate/fftsize
plt.plot(freqs,spec)
plt.xlabel('relative to center [Mhz]')

RFI = [[1419.4-0.210, 0.02], 
       #[1419.4-1.937, 0.015], 
       #[1419.4-4.4, 0.015], 
       #[1419.4+3.0, 0.01], 
       #[center_freq, 8*delta_nu] # remove dip in the center of band, always about 4 fft points wide. Use 8, else errors
       ]
#plt.figure()
#plt.plot(spec)
# DEFINE FLAGS in HZ
for item in RFI:
    print item
    RFI_freq = item[0]
    RFI_width = item[1]
    ch0_freq = center_freq - 0.5*samp_rate
    ind_low = int(np.floor((RFI_freq-0.5*RFI_width - ch0_freq)/delta_nu))
    ind_high = int(np.ceil((RFI_freq+0.5*RFI_width - ch0_freq)/delta_nu))
    margin = min((ind_high-ind_low), ind_low, len(spec)-ind_high)
    RFI_org = np.array([spec[ind_low-margin:ind_low], spec[ind_high:ind_high+margin]])
    RFI_part = RFI_org.flatten()
    xdata = range(ind_low-margin, ind_low) + range(ind_high, ind_high+margin)
    print np.size(xdata), np.size(RFI_part)
    spl = ip.UnivariateSpline(xdata,RFI_part, k=1, s=0)
    interpdata = spl(range(ind_low, ind_high))
    print interpdata
    spec[ind_low:ind_high] = interpdata[:]
    plt.figure()
    plt.plot(RFI_part)
    plt.plot(interpdata)

#plt.figure()
#plt.plot(freqs, spec)
#for flag in flags:
#    
    
# Calculate flag indices
# For each flag, interpolate flagged values (splines)
# when all flaggs are applied and interpolated, proceed with convolve!


#plt.figure()
#convspec = np.convolve(spec, [1,1,1,1], mode='same')
#w = sig.boxcar(4)
#convspec=np.convolve(w/w.sum(),spec,mode='valid')
##convspec = sig.decimate(spec, 2)
#fftsize = fftsize/2
#halffft = int(0.5*fftsize)
#convfreqs = 0.5*samp_rate*np.array(range(-halffft,halffft))/(halffft)
#print np.shape(convspec)
#print np.shape(convfreqs)
#plt.plot(convfreqs,convspec)
#plt.xlabel('relative to center [Mhz]')
plt.show()
