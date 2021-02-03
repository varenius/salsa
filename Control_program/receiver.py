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
#from gnuradio import blks2 as grc_blks2
from gnuradio.eng_option import eng_option
from gnuradio.fft import window
from gnuradio.filter import firdes
from optparse import OptionParser
from gnuradio import filter
import time
import threading

class SALSA_Receiver(gr.top_block):

    def __init__(self, c_freq, int_time, samp_rate, fftsize, username, config, usrp_gain):
        gr.top_block.__init__(self, "Salsa Receiver")

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate
        self.outfile = outfile =  config.get('USRP', 'tmpdir') + "/SALSA_" + username + ".tmp" #Only used for sink init
        self.int_time = int_time
        self.gain = usrp_gain
        self.fftsize = fftsize
        self.c_freq = c_freq
        self.probe_var = probe_var = 0
        
        #Integrate 10 FFTS using IIR block and keep 1 in N, increase for higher bandwidths to lower processing times.
        self.alpha = 0.1
        self.N = 10

        ##################################################
        # Blocks
        ##################################################
        self.uhd_usrp_source_0 = uhd.usrp_source(
       	    device_addr="addr="+config.get('USRP', 'host'),
            stream_args=uhd.stream_args(
                cpu_format="fc32",
                channels=range(1),
                #recv_frame_size=4096, #Problems with overflow at bw>5 MHz, this might be a solution (depends on ethernet connection capabilities)
                #recv_buff_size=4096,
             ),
        )
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_center_freq(c_freq, 0)
        self.uhd_usrp_source_0.set_gain(self.gain, 0)
        
        self.fft_vxx_0 = fft.fft_vcc(fftsize, True, (window.blackmanharris(fftsize)), True, 1)
        self.blocks_vector_to_stream_0 = blocks.vector_to_stream(gr.sizeof_float*1, fftsize)
        self.blocks_stream_to_vector_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, fftsize)
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(fftsize)
        self.single_pole_iir_filter_xx_0 = filter.single_pole_iir_filter_ff(self.alpha, fftsize)
        self.blocks_keep_one_in_n_0 = blocks.keep_one_in_n(gr.sizeof_float*fftsize, self.N)


        #Signal and reference file sinks
        self.signal_file_sink_1 = blocks.file_sink(gr.sizeof_float*1, self.outfile, False)
        self.signal_file_sink_1.set_unbuffered(False)
        self.signal_file_sink_2 = blocks.file_sink(gr.sizeof_float*1, self.outfile, False)
        self.signal_file_sink_2.set_unbuffered(False)
        self.blocks_null_sink = blocks.null_sink(gr.sizeof_float*1)	
		#Selector for switch
        #self.blks2_selector_0 = grc_blks2.selector(
        self.blks2_selector_0 = blocks.selector(
            itemsize=gr.sizeof_float*1,
            input_index=0,
            output_index=0,
        )
		
        ##################################################
        # Connections
        ##################################################
        self.connect((self.uhd_usrp_source_0, 0), (self.blocks_stream_to_vector_0, 0))
        self.connect((self.blocks_stream_to_vector_0, 0), (self.fft_vxx_0, 0))
        self.connect((self.fft_vxx_0, 0), (self.blocks_complex_to_mag_squared_0, 0))
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.single_pole_iir_filter_xx_0, 0))
        self.connect((self.single_pole_iir_filter_xx_0, 0), (self.blocks_keep_one_in_n_0, 0))
        self.connect((self.blocks_keep_one_in_n_0, 0), (self.blocks_vector_to_stream_0, 0))
        self.connect((self.blocks_vector_to_stream_0, 0), (self.blks2_selector_0, 0))
        
        #Selector connections
        self.connect((self.blks2_selector_0, 1), (self.signal_file_sink_1, 0))
        self.connect((self.blks2_selector_0, 2), (self.signal_file_sink_2, 0))
		
    	#Null sink connection
        self.connect((self.blks2_selector_0, 0), (self.blocks_null_sink, 0))

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

