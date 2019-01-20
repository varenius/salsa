##################################################
# Gnuradio Python Flow Graph
# Title: Salsa Receiver
# Generated: Wed Jul  2 11:16:40 2014
##################################################

from gnuradio.blocks import file_sink, null_sink
from gnuradio.gr import top_block, sizeof_gr_complex
from gnuradio.uhd import usrp_source, stream_args
from grc_gnuradio.blks2 import selector

from numpy import fromfile, complex64
from time import time, sleep
from os import remove

from controller.observation.observation_nodes import ObservationAborting


class SALSA_Receiver(top_block):
    class IOSyncHandler:
        def __init__(self, sync_obj):
            self._sync_obj = sync_obj

        def __enter__(self):
            self._sync_obj.lock()
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            self._sync_obj.unlock()
            return False

    class SinkHandler:
        def __init__(self, sync_handler_, block_selector_, f_i_to_sink_,
                     i_null_sink_, i_file_sink_, outfile_):
            self._sync_handler = sync_handler_
            self._selector = block_selector_
            self._i_nul_s = i_null_sink_
            self._i_to_sink = f_i_to_sink_
            self._i_sink = i_file_sink_
            self._outfile = outfile_

        def __enter__(self):
            self._open_sink(self._i_to_sink(self._i_sink))
            self._selector.set_output_index(self._i_sink)
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            self._selector.set_output_index(self._i_nul_s)
            self._close_sink(self._i_to_sink(self._i_sink))
            return False

        def _open_sink(self, fs_):
            with self._sync_handler:
                fs_.open(self._outfile)

        def _close_sink(self, fs_):
            with self._sync_handler:
                fs_.close()

    def __init__(self, host_, outfile_):
        top_block.__init__(self, "Salsa Receiver")

        self._stop_if_aborting = self.__nothing
        self._io_sync_handler = self.IOSyncHandler(self)
        self._sel_con = list()

        self._usrp_connection = SALSA_Receiver._open_usrp_connection(host_)
        self._block_selector = SALSA_Receiver._create_block_selector(
            num_inputs_=1,
            num_outputs_=3  # null, signal and reference
        )
        self.connect((self._usrp_connection, 0), (self._block_selector, 0))

        self._outfile = outfile_
        self._i_nul_s = self._connect_sink(self._create_null_sink())
        self._i_sig_s = self._connect_sink(self._create_file_sink(self._outfile))
        self._i_ref_s = self._connect_sink(self._create_file_sink(self._outfile))

    def __nothing(self):
        return False

    def __stop_if_aborting(self):
        raise ObservationAborting()

    def __enter__(self):
        try:                    # create/clear output file
            open(self._outfile, "w").close()
        except EnvironmentError:  # in case we can not open/create it
            pass
        self.start()
        self._stop_if_aborting = self.__nothing
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._stop_if_aborting = self.__stop_if_aborting
        self.stop()
        self.wait()
        try:                    # remove output file
            remove(self._outfile)
        except EnvironmentError:  # in case we can not remove it
            pass
        return False

    def stream_signal(self, duration_):
        return self.stream(self._i_sig_s, self._outfile, duration_)

    def stream_reference(self, duration_):
        return self.stream(self._i_ref_s, self._outfile, duration_)

    def stream(self, i_file_sink_, outfile_, duration_):
        with self._create_sink_handler(i_file_sink_, outfile_):
            t_end = time() + duration_
            while time() <= t_end and not self._stop_if_aborting():
                self._wait_ms(1)
            return fromfile(outfile_, dtype=complex64)

    def set_center_frequency(self, frequency_):
        self._usrp_connection.set_center_freq(frequency_, 0)
        # Sleep in order for LO to lock and GNURadio stream to clear out
        self._wait_ms(10)

    def set_sample_rate(self, samp_rate_):
        self._usrp_connection.set_samp_rate(samp_rate_)
        self._wait_ms(10)

    def set_gain(self, gain_):
        self._usrp_connection.set_gain(gain_, 0)
        self._wait_ms(10)

    def get_samp_rate(self):
        return self._usrp_connection.get_samp_rate()

    def abort_measurement(self):
        self._stop_if_aborting = self.__stop_if_aborting

    def get_sig_output(self):
        return self._i_sig_s

    def get_ref_output(self):
        return self._i_ref_s

    def _create_sink_handler(self, i_file_sink_, outfile_):
        return self.SinkHandler(self._io_sync_handler, self._block_selector,
                                lambda i: self._sel_con[i],
                                self._i_nul_s, i_file_sink_, outfile_)

    def _connect_sink(self, fs_):
        i_fs_ = len(self._sel_con)
        self._sel_con.append(fs_)
        self.connect((self._block_selector, i_fs_),
                     (self._sel_con[i_fs_], 0))
        return i_fs_

    def _wait_ms(self, t):
        sleep(t * 1e-3)

    def _create_null_sink(self):
        return null_sink(sizeof_gr_complex)

    def _create_file_sink(self, outfile_, unbuffered_=False):
        fs_ = file_sink(sizeof_gr_complex, outfile_, False)
        fs_.set_unbuffered(unbuffered_)
        return fs_

    @staticmethod
    def _create_block_selector(num_inputs_, num_outputs_):
        return selector(item_size=sizeof_gr_complex,
                        num_inputs=num_inputs_,
                        num_outputs=num_outputs_,
                        input_index=0,
                        output_index=0)

    @staticmethod
    def _open_usrp_connection(address_):
        return usrp_source(device_addr="addr="+address_,
                           stream_args=stream_args(cpu_format="fc32",
                                                   channels=[0]))
