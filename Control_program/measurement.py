from receiver import *
from spectrum import *
import ephem
import matplotlib.pyplot as plt
import numpy as np
import math
import os

class Measurement:

    def __init__(self, c_freq, int_time, bandwidth, alt, az, site, noutchans, username, config, offset_alt, offset_az):
        # Copy everything to make sure immutable operations
        # do not change the original input objects in case
        # we pass references to this constructor.

        # Username needed for tmpfile to make sure we can edit the file,
        # else (if using one file for every user) we may get
        # permission errors if, say, the program
        # crashes after creating the file but before
        # managing to remove it or fix permissions.

        # To remove narrow band RFI, use at least 4906 points FFT.
        # But, if more channels requested, use at least twice 
        # the desired channel numbers to allow
        # some smoothing of the spectra to get rid of RFI.
        self.noutchans = int(noutchans)
        self.fftsize = max(4096,2*self.noutchans)
        self.center_freq = float(c_freq)
        self.int_time = int(int_time)
        self.bandwidth = float(bandwidth)
        self.alt = alt
        self.az = az
        # Copy relevant properties from input site
        self.site = ephem.Observer()
        self.site.lat = site.lat
        self.site.long = site.long
        self.site.elevation = site.elevation
        self.site.pressure = site.pressure
        self.site.date = ephem.Date(site.date)
        self.site.name = site.name
        self.observer = username
        self.config = config
        self.offset_alt = offset_alt
        self.offset_az = offset_az

        # Create receiver object to run GNUradio flowgraph.
        # Using both upper and lower sideband, so bandwidth is equal to 
        # sampling rate, not half.
        self.receiver = SALSA_Receiver(c_freq, int_time, bandwidth, self.fftsize, self.observer, config)

    def measure(self):
        self.receiver.start()
        self.receiver.wait()
        self.stack_measured_FFTs()

    def stack_measured_FFTs(self):
        infile = self.receiver.get_outfile()
        fftsize = self.receiver.get_fftsize() 
        samp_rate = self.receiver.get_samp_rate()
        cfreq = self.receiver.get_c_freq()

        # Load FFT segments as memory mapped file in case it is large
        signal = np.memmap(infile, mode = 'r', dtype=np.float32)
        #print np.size(signal)# 19999744 for 10s data, but should be 2e7...
        # Will take only full spectra to stack, not the missing last(or first) samples.
        nspec = int(signal.size/fftsize) # Now floored to contain only full spectra
        goodpoints = nspec*fftsize # The number of good samples (excluding last partial spectra)
        signal = signal[0:goodpoints]
        spec = signal.reshape((nspec,fftsize))
        spec = spec.sum(axis=0)
        # Normalise power spectrum to be invariant of
        # integration time and Calibrate intensity
        # from comparison with LAB survey
        # TODO: Proper amplitude calibration! For now just single scale factor.
        calfactor = 500 # K/USRP input unit with 60dB gain. 
        spec = calfactor * spec/(1.0*nspec)
        self.spectrum = SALSA_spectrum(spec, samp_rate, fftsize, cfreq, self.site, self.alt, self.az, self.int_time, self.observer, self.config, self.offset_alt, self.offset_az)
        # Clean up temporary object and file
        del signal
        os.remove(infile)
