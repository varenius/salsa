#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Receiver
# Generated: Fri Jun  5 17:18:32 2015
##################################################

from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import time

class Receiver(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Receiver")

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 5000000.0
        self.outfile = outfile = "/tmp/timedata.dat"
        self.int_time = int_time = 10
        self.gain = gain = 60
        self.fftsize = fftsize = 4096
        self.c_freq = c_freq = 1410.0e6

        ##################################################
        # Blocks
        ##################################################
        self.uhd_usrp_source_0 = uhd.usrp_source(
        	device_addr="addr=192.168.20.2",
        	stream_args=uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_center_freq(c_freq, 0)
        self.uhd_usrp_source_0.set_gain(gain, 0)
        self.blocks_head_0 = blocks.head(gr.sizeof_float*1, int(int_time*samp_rate))
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_float*1, outfile, False)
        self.blocks_file_sink_0.set_unbuffered(False)
        self.blocks_complex_to_float_0 = blocks.complex_to_float(1)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_head_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.blocks_complex_to_float_0, 0))
        self.connect((self.blocks_complex_to_float_0, 0), (self.blocks_head_0, 0))


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

if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    tb = Receiver()
    tb.start()
    tb.wait()

