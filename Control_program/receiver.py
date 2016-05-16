#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Salsa Receiver
# Generated: Wed Jul  2 11:16:40 2014
##################################################

from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import fft
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.fft import window
from gnuradio.filter import firdes
from optparse import OptionParser
import time

class SALSA_Receiver(gr.top_block):

    def __init__(self, c_freq, int_time, samp_rate, fftsize, username, config):
        gr.top_block.__init__(self, "Salsa Receiver")

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate
        self.outfile = outfile =  config.get('USRP', 'tmpdir') + "/SALSA_" + username + ".tmp" ##Change to ramdisk for high BWs
        self.int_time = int_time
        self.gain = gain = config.getfloat('USRP', 'gain')
        self.fftsize = fftsize
        self.c_freq = c_freq
        self.probe_var = probe_var = 0
        
        #Integrate 100 FFTS using IIR block and keep 1 in N
        self.alpha = 0.01
	self.N = 100

        ##################################################
        # Blocks
        ##################################################
        self.uhd_usrp_source_0 = uhd.usrp_source(
        	device_addr="addr="+config.get('USRP', 'host'),
        	stream_args=uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_center_freq(c_freq, 0)
        self.uhd_usrp_source_0.set_gain(gain, 0)
        
        self.fft_vxx_0 = fft.fft_vcc(fftsize, True, (window.blackmanharris(fftsize)), True, 1)
        self.blocks_vector_to_stream_0 = blocks.vector_to_stream(gr.sizeof_gr_complex*1, fftsize)
        self.blocks_stream_to_vector_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, fftsize)
        self.blocks_signal_sink = blocks.file_sink(gr.sizeof_float*1, outfile, False)
        self.blocks_file_sink_0.set_unbuffered(False)
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(1)
        self.single_pole_iir_filter_xx_0 = filter.single_pole_iir_filter_ff(self.alpha, fftsize)
        self.blocks_keep_one_in_n_0 = blocks.keep_one_in_n(gr.sizeof_float*fftsize, self.N)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.uhd_usrp_source_0, 0), (self.blocks_stream_to_vector_0, 0))
        self.connect((self.blocks_stream_to_vector_0, 0), (self.fft_vxx_0, 0))
        self.connect((self.fft_vxx_0, 0), (self.blocks_vector_to_stream_0, 0))
        self.connect((self.blocks_vector_to_stream_0, 0), (self.blocks_complex_to_mag_squared_0, 0))
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.single_pole_iir_filter_xx_0, 0))
	self.connect((self.single_pole_iir_filter_xx_0, 0), (self.blocks_keep_one_in_n_0, 0))
        self.connect(self.blocks_keep_one_in_n_0, 0, (self.blocks_signal_sink, 0))
        
        #Probe update rate
	def _probe_var_probe():
		while True:
			val = self.probe_signal.level()
			try:
				self.set_probe_var(val)
			except AttributeError:
				pass
			time.sleep(10 / (self.samp_rate)) #Update probe variabel every 10/samp_rate seconds
	_probe_var_thread = threading.Thread(target=_probe_var_probe)
	_probe_var_thread.daemon = True
	_probe_var_thread.start()
		
	#self.blocks_head_0 = blocks.head(gr.sizeof_float*1, int(int_time*samp_rate))
	#self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.blocks_head_0, 0))

# QT sink close method reimplementation

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)

    def get_outfile(self):
        return self.outfile

    def set_outfile(self, outfile):
        self.outfile = outfile
        self.blocks_file_sink_0.open(self.outfile)

    def get_int_time(self):
        return self.int_time

    def set_int_time(self, int_time):
        self.int_time = int_time

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain
        self.uhd_usrp_source_0.set_gain(self.gain, 0)

    def get_fftsize(self):
        return self.fftsize

    def set_fftsize(self, fftsize):
        self.fftsize = fftsize

    def get_c_freq(self):
        return self.c_freq

    def set_c_freq(self, c_freq):
        self.c_freq = c_freq
        self.uhd_usrp_source_0.set_center_freq(self.c_freq, 0)
        
    def get_probe_var(self):
        return self.probe_var

    def set_probe_var(self, probe_var):
        self.probe_var = probe_var


if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    tb = SALSA_Receiver()
    tb.start()
    tb.wait()

