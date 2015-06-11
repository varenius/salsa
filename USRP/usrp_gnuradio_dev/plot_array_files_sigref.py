import matplotlib.pyplot as plt
import numpy as np
import sys
import time
import scipy.signal as sig

sigfile = sys.argv[1]
reffile = sys.argv[2]
files = [sigfile, reffile]
result = []
for infile in files:
    indata = np.load(infile)
    spec = indata[0]
    samp_rate = indata[1]
    fftsize = indata[2]
    center_freq = indata[3] # MHz
    halffft = int(0.5*fftsize)
    freqs = 0.5*samp_rate*np.array(range(-halffft,halffft))/(halffft)
    delta_nu = samp_rate/fftsize
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
            spec[ind_low:ind_high] = interpdata[margin:-margin]
        else: 
            print 'Ignoring', item
    calspec = spec*230 # Determined from comparing with LAB survey at glong 80, glat 0
    result.append(calspec[:])

specres = result[0]-result[1]
plt.figure()
indata = np.load(sigfile)
samp_rate = indata[1]
fftsize = indata[2]
center_freq = indata[3] # MHz
halffft = int(0.5*fftsize)
freqs = 0.5*samp_rate*np.array(range(-halffft,halffft))/(halffft)
plt.xlabel('Offset from ' + str(round(center_freq, 2)) + 'MHz')
plt.plot(freqs, result[0])
plt.plot(freqs, result[1])
plt.legend(['Sig', 'Ref'])

plt.figure()
plt.plot(specres)
plt.title('Signal - ref * [Approx. LAB comparision at 80,0] ')

l = len(specres)
lind = 0.1*l
hind = 0.9*l
plt.figure()
nout = 1024
dec = sig.decimate(specres, fftsize/nout, axis=0)
plt.plot(dec)
plt.title('Decimated to ' +str(nout) + 'ch.')
plt.show()
