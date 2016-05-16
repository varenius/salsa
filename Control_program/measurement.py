from receiver import *
from spectrum import *
import ephem
import matplotlib.pyplot as plt
import numpy as np
import math
import os
import time
from multiprocessing.pool import ThreadPool as Pool

class Measurement:

    def __init__(self, c_freq, ref_freq, switched, int_time, bandwidth, alt, az, site, noutchans, username, config, offset_alt, offset_az, calfact):
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
        self.sig_freq = float(c_freq)
        self.ref_freq = float(ref_freq)
        self.int_time = int(int_time)
        self.bandwidth = float(bandwidth)
        self.alt = alt
        self.az = az
        self.calfactor = calfact
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
        self.switched = switched
        

        # Create receiver object to run GNUradio flowgraph.
        # Using both upper and lower sideband, so bandwidth is equal to 
        # sampling rate, not half.
        self.receiver = SALSA_Receiver(c_freq, int_time, bandwidth, self.fftsize, self.observer, config)

    def measure(self):
		self.receiver.start()
		if self.switched == True:
			self.sigCount = 0
			self.refCount = 0
			self.int_time *=2
			self.sig_time = self.int_time/2
			self.ref_time = self.int_time/2
			self.signal_time = 0
			self.reference_time = 0
			
			t_end = time.time() + self.int_time
			while time.time() <= t_end:
				self.receiver.uhd_usrp_source_0.set_center_freq(self.sig_freq, 0)
				time.sleep(5e-3)
				self.receiver.signal_sink.open("/home/Olvhammar/Documents/sig" + str(self.sigCount))
				t_end2 = time.time() + self.sig_time
				start = time.time()
				print "Signal"
				while time.time() <= t_end2 and time.time() <= t_end:
					continue
				self.receiver.signal_sink.close()
				end = time.time()
				self.signal_time += (end-start)
				self.sigCount +=1
				self.receiver.uhd_usrp_source_0.set_center_freq(self.ref_freq, 0)
				time.sleep(5e-3)
				self.receiver.signal_sink.open("/home/Olvhammar/Documents/ref" + str(self.refCount))
				t_end3 = time.time() + self.ref_time
				start1 = time.time()
				print "Reference"
				while time.time() <= t_end3 and time.time() <= t_end:
					continue
				self.receiver.signal_sink.close()
				end1 = time.time()
				self.reference_time += (end1-start1)
				self.refCount +=1
        
			self.sigList = []
			self.refList = []

			for i in range(self.sigCount):
				item = "/home/Olvhammar/Documents/sig" + str(i)
				self.sigList.append(item)
			for i in range(self.refCount):
				item = "/home/Olvhammar/Documents/ref" + str(i)
				self.refList.append(item)
		
			if os.path.getsize('/home/Olvhammar/Documents/sig' + str(self.sigCount-1)) == 0:
				self.sigList.remove('/home/Olvhammar/Documents/sig' + str(self.sigCount-1))
				self.refList.remove('/home/Olvhammar/Documents/ref' + str(self.refCount-1))				
			elif os.path.getsize('/home/Olvhammar/Documents/ref' + str(self.refCount-1)) == 0:
				self.refList.remove('/home/Olvhammar/Documents/ref' + str(self.refCount-1))

			print "Actual Signal time: "
			print self.signal_time
			print "Actual Reference time: "
			print self.reference_time			

			#Stack all the data
			self.sig_spec = self.stack_all_data(self.sigList)
			self.ref_spec = self.stack_all_data(self.refList)
		
			#Calculates mean value for all signal and reference data
			self.SIG_data = self.mean(self.sig_spec)
			self.REF_data = self.mean(self.ref_spec)
		
			self.signal_spec = SALSA_spectrum(self.SIG_data, self.receiver.get_samp_rate(), self.receiver.get_fftsize(), self.sig_freq, self.site, self.alt, self.az, self.int_time, self.observer, self.config, self.offset_alt, self.offset_az)
			self.reference_spec = SALSA_spectrum(self.REF_data, self.receiver.get_samp_rate(), self.receiver.get_fftsize(), self.ref_freq, self.site, self.alt, self.az, self.int_time, self.observer, self.config, self.offset_alt, self.offset_az)
			#Clear temporary files
			#files = glob.glob('/home/Olvhammar/Documents/*')
			#for f in files:
			#	if f.endswith(self.index):
			#		os.remove(f)
			#	else:
			#		continue	
		else:
			self.receiver.uhd_usrp_source_0.set_center_freq(self.sig_freq, 0)
			time.sleep(5e-3)
			self.receiver.signal_sink.open("/home/Olvhammar/Documents/sig")
			end = time.time() + self.int_time
			while time.time() <= end:
				continue
			self.receiver.signal_sink.close()
			
			spec = self.stack_measured_FFTs("/home/Olvhammar/Documents/sig")
			self.signal_spec = SALSA_spectrum(spec, self.receiver.get_samp_rate(), self.receiver.get_fftsize(), self.sig_freq, self.site, self.alt, self.az, self.int_time, self.observer, self.config, self.offset_alt, self.offset_az)
               
    def stack_all_data(self, files):
		pool = Pool(processes=4)
		spectra = pool.map(self.stack_measured_FFTs, files)
		pool.terminate()
		return spectra

    def stack_measured_FFTs(self,infile):
        fftsize = self.receiver.get_fftsize() 
        samp_rate = self.receiver.get_samp_rate()

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
        calfactor = 300 # K/USRP input unit with 60dB gain.  
        spec = self.calfactor * spec/(1.0*nspec)
        # Clean up temporary object and file
        del signal
        os.remove(infile)
        return spec
        
    def mean(self, spectra):
		sum_spec = np.sum(spectra, axis=0, dtype = np.float32)
		return sum_spec/float(len(spectra))
