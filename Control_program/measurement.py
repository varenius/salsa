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

    def __init__(self, c_freq, ref_freq, switched, int_time, sig_time, ref_time, bandwidth, alt, az, site, noutchans, username, config, offset_alt, offset_az, usrp_gain):
        # Copy everything to make sure immutable operations
        # do not change the original input objects in case
        # we pass references to this constructor.

        # Username needed for tmpfile to make sure we can edit the file,
        # else (if using one file for every user) we may get
        # permission errors if, say, the program
        # crashes after creating the file but before
        # managing to remove it or fix permissions.

        # To remove narrow band RFI, use at least 4096 points FFT.
        # But, if more channels requested, use at least twice 
        # the desired channel numbers to allow
        # some smoothing of the spectra to get rid of RFI.
        self.noutchans = int(noutchans)
        self.fftsize = max(4096,2*self.noutchans)
        self.sig_freq = float(c_freq)
        self.ref_freq = float(ref_freq)
        self.int_time = int(int_time)
        self.bandwidth = float(bandwidth)
        self.usrp_gain = float(usrp_gain)
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
        self.switched = switched
        self.sig_time = sig_time
        self.ref_time = ref_time
        self.abort = False

        self.outfile = outfile =  config.get('USRP', 'tmpdir') + "/SALSA_" + username
        
        # Create receiver object to run GNUradio flowgraph.
        # Using both upper and lower sideband, so bandwidth is equal to 
        # sampling rate, not half.
        self.receiver = SALSA_Receiver(c_freq, int_time, bandwidth, self.fftsize, self.observer, config, self.usrp_gain)

    def measure(self):
       self.receiver.start()
       if self.switched == True:
            self.sigCount = 0 #Counter for signal and reference files
            self.refCount = 0
            self.signal_time = 0 #Actual signal time
            self.reference_time = 0
                        
            t_end = time.time() + self.int_time #Run loop for total observation time
            while time.time() <= t_end and self.abort == False:
                self.receiver.uhd_usrp_source_0.set_center_freq(self.sig_freq, 0) #Switch to signal frequency
                time.sleep(10e-3) #Sleep in order for LO to lock and GNURadio stream to clear out, can be lowered
                self.receiver.lock()
                self.receiver.signal_file_sink_1.open(self.outfile + "_sig" + str(self.sigCount)) #Switch to signal file sink
                self.receiver.unlock()
                self.receiver.blks2_selector_0.set_output_index(1) #Switch GNURadio stream to signal file sink (switching just file sinks also works but this functions as extra security)
                t_end2 = time.time() + self.sig_time
                start = time.time()
                print("Measuring signal...")
                while time.time() <= t_end2 and time.time() <= t_end and self.abort == False: #Continue stream to signal file sink for set signal time
                      continue
                self.receiver.blks2_selector_0.set_output_index(0) #Switch to null sink for blanking time
                self.receiver.lock()
                self.receiver.signal_file_sink_1.close() #Close current file sink
                self.receiver.unlock()
                end = time.time()
                self.signal_time += (end-start)
                self.sigCount +=1
                self.receiver.uhd_usrp_source_0.set_center_freq(self.ref_freq, 0) #Switch to reference frequency
                time.sleep(10e-3)
                self.receiver.lock()
                self.receiver.signal_file_sink_2.open(self.outfile + "_ref" + str(self.refCount)) #Switch to reference file sink
                self.receiver.unlock()
                self.receiver.blks2_selector_0.set_output_index(2) #Switch GNURadio stream to reference file sink
                t_end3 = time.time() + self.ref_time
                start1 = time.time()
                print("...done.")
                print("Measuring reference...")
                while time.time() <= t_end3 and time.time() <= t_end and self.abort == False:
                      continue
                self.receiver.blks2_selector_0.set_output_index(0)
                self.receiver.lock()
                self.receiver.signal_file_sink_2.close()
                self.receiver.unlock()
                end1 = time.time()
                self.reference_time += (end1-start1)
                self.refCount +=1
                print("...done.")
        
            self.sigList = [] #Init signal file sink list
            self.refList = []

            for i in range(self.sigCount):
                item = self.outfile + "_sig" + str(i) #Append items depending on the amount of files
                self.sigList.append(item)
            for i in range(self.refCount):
                item = self.outfile + "_ref" + str(i)
                self.refList.append(item)
                        
            #Incase loop starts at end of integration time (empty files might occur)
            if os.path.getsize(self.outfile + "_sig" + str(self.sigCount-1)) == 0:
                self.sigList.remove(self.outfile + "_sig" + str(self.sigCount-1))
                self.refList.remove(self.outfile + "_ref" + str(self.refCount-1))                               
            elif os.path.getsize(self.outfile + "_ref" + str(self.refCount-1)) == 0:
                self.refList.remove(self.outfile + "_ref" + str(self.refCount-1))

            print("Actual Signal time: ", self.signal_time)
            print("Actual Reference time: ", self.reference_time) 
            #Stack all the data
            # Multiply with 1000 to get higher raw intensity numbers for printout
            self.sig_spec = 1000*self.stack_all_data(self.sigList)
            self.ref_spec = 1000*self.stack_all_data(self.refList)
               
            if self.abort == False:
                #Calculates mean value for all signal and reference data
                self.SIG_data = self.mean(self.sig_spec)
                self.REF_data = self.mean(self.ref_spec)
                self.signal_spec = SALSA_spectrum(self.SIG_data, self.receiver.get_samp_rate(), self.receiver.get_fftsize(), self.sig_freq, self.site, self.alt, self.az, self.int_time, self.observer, self.config, self.offset_alt, self.offset_az)
                self.reference_spec = SALSA_spectrum(self.REF_data, self.receiver.get_samp_rate(), self.receiver.get_fftsize(), self.ref_freq, self.site, self.alt, self.az, self.int_time, self.observer, self.config, self.offset_alt, self.offset_az)
       else:#Unswitched measurement
            self.receiver.uhd_usrp_source_0.set_center_freq(self.sig_freq, 0)
            time.sleep(10e-3)
            self.receiver.lock()
            self.receiver.signal_file_sink_1.open(self.outfile + "_sig")
            self.receiver.unlock()
            self.receiver.blks2_selector_0.set_output_index(1)
            end = time.time() + self.sig_time
            while time.time() <= end and self.abort == False:
                 continue
            self.receiver.blks2_selector_0.set_output_index(0)
            self.receiver.lock()
            self.receiver.signal_file_sink_1.close()
            self.receiver.unlock()
                        
            if self.abort == False:
                # Multiply with 1000 to get higher raw intensity numbers for printout
                spec = 1000*self.stack_measured_FFTs(self.outfile + "_sig")
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
        # integration time
        spec = spec/(1.0*nspec)
        # Clean up temporary object and file
        del signal
        os.remove(infile)
        return spec
        
    def mean(self, spectra):
                sum_spec = np.sum(spectra, axis=0, dtype = np.float32)
                return sum_spec/float(len(spectra))

