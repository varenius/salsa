import matplotlib.pyplot as plt
import numpy as np
import sys
import time
import scipy.signal as sig

infile = sys.argv[1]
indata = np.load(infile)
spec = indata[0]
samp_rate = indata[1]
fftsize = indata[2]
center_freq = indata[3] # MHz


halffft = int(0.5*fftsize)
freqs = 0.5*samp_rate*np.array(range(-halffft,halffft))/(halffft)
#plt.plot(spec)
delta_nu = samp_rate/fftsize
plt.plot(freqs,spec)
plt.xlabel('relative to center [Mhz]')

#plt.figure()


RFI = [[1419.4-0.210, 0.02], 
       [1419.4-1.937, 0.015], 
       [1419.4-4.4, 0.015], 
       [1419.4+3.0, 0.01], 
       [center_freq, 4*delta_nu], # remove dip in the center of band, always about 4 fft points wide. Use 8, else errors
       [1416.4-0.8, 0.04],
       [1420.4-2, 0.01],
       [1425, 0.01],
       [1424.4-1.8, 0.01],
       [1424.4+0.5845, 0.01],
       [1424.4+0.483, 0.005],
       ]
flags = []
#plt.plot(spec)

for item in RFI:
    RFI_freq = item[0]
    RFI_width = item[1]
    ch0_freq = center_freq - 0.5*samp_rate
    ind_low = int(np.floor((RFI_freq-0.5*RFI_width - ch0_freq)/delta_nu))
    ind_high = int(np.ceil((RFI_freq+0.5*RFI_width - ch0_freq)/delta_nu))
    if ind_low>0 and ind_high<len(spec):
        margin = min(ind_high-ind_low, ind_low, len(spec)-ind_high)
        RFI_part = spec[ind_low-margin:ind_high+margin]
        xdata = np.arange(len(RFI_part))
        weights = np.ones_like(RFI_part)
        weights[margin:-margin] = 0.0 # Ignore RFI when fitting
        pf = np.polyfit(xdata, RFI_part, deg=1, w=weights)
        interpdata = np.polyval(pf, xdata)
        #plt.figure()
        #plt.plot(xdata, interpdata)
        spec[ind_low:ind_high] = interpdata[margin:-margin]
    else: 
        print 'Ignoring', item

plt.figure()
calspec = spec * 750/1.6
plt.plot(calspec)
plt.ylabel('Roughly [K]')

#plt.figure()
#fftsize = 0.8*fftsize
#halffft = int(0.5*fftsize)
#freqs = 0.5*samp_rate*np.array(range(-halffft,halffft))/(halffft)
#l = len(spec)
#lind = 0.1*l
#hind = 0.9*l
#newspec = spec[lind:hind-1]
#print np.shape(newspec), np.shape(freqs)
#plt.plot(freqs, newspec)
#xdata = np.arange(len(newspec))
#weights = np.ones_like(newspec)
#margin = 0.25*len(newspec)
#weights[margin:-margin] = 0.0 # Ignore RFI when fitting
#pf = np.polyfit(xdata, newspec, w=weights, deg=8)
#interpdata = np.polyval(pf, xdata)
#plt.plot(freqs,interpdata)
#plt.figure()
#plt.plot(freqs, newspec-interpdata)

#plt.figure()
#dec = sig.decimate(spec, 8, axis=0)
#plt.plot(dec)


plt.show()
