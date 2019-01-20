from os import remove
from ephem import now
from numpy import average, size, reshape, abs, round, nan
from numpy.fft import fftshift, fft, ifftshift

from controller.util import overrides
from controller.observation.spectrum import SALSA_spectrum


class AbstractNaNAction:
    def handle_raw(self, raw_data_):
        """
        Check if NaN-valued elements exists in the raw data
        and perhaps perform some action.
        Return True if Nan was found; False it not found

        If NaN is encountered in the raw data it could indicate
        that different floating point formats are used in the
        device that created the raw data (e.g. the USRP) uses a
        different format than the device that read the data (e.g.
        this machine).
        """
        raise NotImplementedError("Abstract Method")

    def handle_processed(self, processed_data_, nan_in_raw_):
        """
        Check if NaN-valued elements exists in the processed data
        and perhaps perform some action.
        Return True if Nan was found; False it not found

        If NaN is encountered in the processed data but not in the
        raw data it could indicate a problem in the data processing.
        """
        raise NotImplementedError("Abstract Method")


class IgnoreOnNaN(AbstractNaNAction):
    def handle_raw(self, raw_data_):
        pass

    def handle_processed(self, processed_data_, nan_in_raw_):
        pass


class WarnOnNaN(AbstractNaNAction):
    def __init__(self, logger_):
        self._logger = logger_

    def handle_raw(self, raw_data_):
        nan_in_raw = nan in raw_data_
        if nan_in_raw:
            self._logger.warn("NaN encountered in raw data")
        return nan_in_raw

    def handle_processed(self, processed_data_, nan_in_raw_):
        nan_in_processed = nan in processed_data_
        if nan_in_processed and not nan_in_raw_:
            self._logger.warn("NaN encountered in processed data")
        return nan_in_processed


class AbstractMeasurement:
    def __init__(self, nan_handler_, bandwidth_, noutchans_, calfact_, receiver_):
        self._nan_handler = nan_handler_
        self._bandwidth = float(bandwidth_)
        self._calfactor = float(calfact_)
        self._noutchans = int(noutchans_)
        self._fftsize = 2*self._noutchans  # max(0x1000, 2*self._noutchans)
        self._receiver = receiver_

    @staticmethod
    def remove_files(file_list):
        while len(file_list) > 0:
            remove(file_list.pop())

    def get_nbr_outchannels(self):
        return self._noutchans

    def abort_measurement(self):
        self._receiver.abort_measurement()

    def measure(self):
        raise NotImplementedError("Abstract Method")

    def get_spectrum(self):
        raise NotImplementedError("Abstract Method")

    def _partition(self, data_):
        j = self._fftsize
        i = int(size(data_) / j)
        return reshape(data_[:i*j], (i, j))

    def _fft(self, sig, ax=1):
        n = self._fftsize
        return ifftshift(fft(fftshift(sig, axes=ax), axis=ax)/n, axes=ax)

    def _power_spec(self, volt_spec_):
        return abs(volt_spec_)**2

    def _stack(self, power_spec, ax=0):
        return average(power_spec, axis=ax)

    def create_spec(self, data_):
        nan_in_raw = self._nan_handler.handle_raw(data_)
        spec = self._stack(self._power_spec(self._fft(self._partition(data_))))
        self._nan_handler.handle_processed(spec, nan_in_raw)

        # Calibrate intensity from comparison with LAB survey
        # TODO: Proper amplitude calibration! For now just single scale factor.
        return self._calfactor * spec


class UnswitchedMeasurement(AbstractMeasurement):
    def __init__(self, nan_handler_, c_freq_, bandwidth_, noutchans_, calfact_,
                 receiver_, logger_, signal_spec_, t_int_, pool_):
        AbstractMeasurement.__init__(self, nan_handler_, bandwidth_,
                                     noutchans_, calfact_, receiver_)
        self._logger = logger_
        self._c_freq = float(c_freq_)

        self._signal_spec = signal_spec_
        if t_int_ > 1.0:
            self._t_sig = 1.0
            self._t_int = round(t_int_)
        else:
            self._t_int = self._t_sig = float(t_int_)

        self._t_streamed = 0
        self._n_streams = 0
        while self._t_streamed < self._t_int:
            self._t_streamed += self._t_sig
            self._n_streams += 1
        self._pool = pool_
        self._async = lambda: self._pool.apply_async(
            self.create_spec, (self._receiver.stream_signal(self._t_sig),))

    @overrides(AbstractMeasurement)
    def get_spectrum(self):
        return self._signal_spec

    @overrides(AbstractMeasurement)
    def measure(self):
        with self._receiver:
            # Using both upper and lower sideband, so bandwidth is equal to
            # sampling rate, not half.
            self._receiver.set_sample_rate(self._bandwidth)
            self._receiver.set_center_frequency(self._c_freq)

            asyncs = list()
            for _ in xrange(self._n_streams):
                asyncs.append(self._async())
            fft_data = average([a.get() for a in asyncs], axis=0)

            self._logger.info("Actual Signal time: %f" % self._t_streamed)
            self._signal_spec.add_data(fft_data, self._c_freq,
                                       self._receiver.get_samp_rate(),
                                       self._fftsize, self._t_int)


class SwitchedMeasurement(AbstractMeasurement):
    def __init__(self, nan_handler_, sig_freq_, ref_offset_, bandwidth_,
                 noutchans_, calfact_, receiver_, logger_, signal_spec_,
                 reference_spec_, t_int_, pool_):
        AbstractMeasurement.__init__(self, nan_handler_, bandwidth_,
                                     noutchans_, calfact_, receiver_)
        self._logger = logger_
        self._sig_freq = sig_freq_
        self._ref_freq = sig_freq_ + ref_offset_
        self._signal_spec = signal_spec_
        self._reference_spec = reference_spec_
        if t_int_ > 2:
            self._t_sig = self._t_ref = 1.0
            self._t_int = 2.0 * round(t_int_ / 2.0)
        else:
            self._t_sig = self._t_ref = t_int_ / 2.0
            self._t_int = float(t_int_)

        self._t_streamed_sig = 0
        self._t_streamed_ref = 0
        self._n_streams = 0
        while self._t_streamed_sig + self._t_streamed_ref < self._t_int:
            self._t_streamed_sig += self._t_sig
            self._t_streamed_ref += self._t_ref
            self._n_streams += 1
        self._pool = pool_
        self._async_sig = lambda: self._pool.apply_async(
            self.create_spec, (self._receiver.stream_signal(self._t_sig),))
        self._async_ref = lambda: self._pool.apply_async(
            self.create_spec, (self._receiver.stream_reference(self._t_ref),))

    @overrides(AbstractMeasurement)
    def get_spectrum(self):
        self._logger.info("Removing reference from signal...")
        return self._signal_spec - self._reference_spec

    @overrides(AbstractMeasurement)
    def measure(self):
        with self._receiver:
            # Using both upper and lower sideband, so bandwidth is equal to
            # sampling rate, not half.
            self._receiver.set_sample_rate(self._bandwidth)

            asyncs_sig, asyncs_ref = list(), list()
            for _ in xrange(self._n_streams):
                self._receiver.set_center_frequency(self._sig_freq)
                asyncs_sig.append(self._async_sig())
                self._receiver.set_center_frequency(self._ref_freq)
                asyncs_ref.append(self._async_ref())
            sig_fft_data = average([a.get() for a in asyncs_sig], axis=0)
            ref_fft_data = average([a.get() for a in asyncs_ref], axis=0)

            self._logger.info("Actual Signal time: %f" % self._t_streamed_sig)
            self._logger.info("Actual Reference time: %f" % self._t_streamed_ref)
            self._signal_spec.add_data(sig_fft_data, self._sig_freq,
                                       self._receiver.get_samp_rate(),
                                       self._fftsize, self._t_int)
            self._reference_spec.add_data(ref_fft_data, self._ref_freq,
                                          self._receiver.get_samp_rate(),
                                          self._fftsize, self._t_int)


class MeasurementSetup:
    """
    Convenient class for creating Measurement instances.
    """
    def __init__(self, logger_, nan_handler_, site_, current_, dbconn_,
                 receiver_, user_, signal_pool_, switched_pool_):
        self._logger = logger_
        self._nan_handler = nan_handler_
        self._site = site_
        self._current = current_
        self._dbconn = dbconn_
        self._receiver = receiver_
        self._user = user_
        self._signal_pool = signal_pool_
        self._switched_pool = switched_pool_

    def create_switched_handler(self, offset, bw, nchans, calfact,
                                int_time, diode_on_, sig_freq, ref_offset):
        self._site.date = now()
        current = self._current()
        signal_spec_ = SALSA_spectrum(
            self._logger, self._site, current.get_elevation(),
            current.get_azimuth(), self._user, offset.get_elevation(),
            offset.get_azimuth(), self._site.name, self._dbconn, diode_on_)
        reference_spec_ = SALSA_spectrum(
            self._logger, self._site, current.get_elevation(),
            current.get_azimuth(), self._user, offset.get_elevation(),
            offset.get_azimuth(), self._site.name, self._dbconn, diode_on_)
        return SwitchedMeasurement(
            self._nan_handler, sig_freq, ref_offset, bw, nchans, calfact,
            self._receiver, self._logger, signal_spec_, reference_spec_,
            int_time, self._switched_pool)

    def create_unswitched_handler(self, offset, bw, nchans, calfact,
                                  int_time, diode_on_, sig_freq):
        self._site.date = now()
        current = self._current()
        signal_spec_ = SALSA_spectrum(
            self._logger, self._site, current.get_elevation(),
            current.get_azimuth(), self._user, offset.get_elevation(),
            offset.get_azimuth(), self._site.name, self._dbconn, diode_on_)
        return UnswitchedMeasurement(
            self._nan_handler, sig_freq, bw, nchans, calfact, self._receiver,
            self._logger, signal_spec_, int_time, self._signal_pool)


class BatchMeasurementSetup:
    """
    Convenience class for performing multible measurements with
    the same basic settings.
    """
    def __init__(self, measurement_setup_, bandwidth_,
                 channels_, cal_fact_, duration_, offset_,
                 frequency_offset_, measurements_per_satellite_,
                 measurements_per_frequency_, lna_on_, diode_on_):
        self._setup = measurement_setup_
        self._bw = bandwidth_
        self._n_ch = channels_
        self._cal_fact = cal_fact_
        self._duration = duration_
        self._offset = offset_
        self._frequency_offset = frequency_offset_
        self._measurements_per_satellite = measurements_per_satellite_
        self._measurements_per_frequency = measurements_per_frequency_
        self._lna_on = lna_on_
        self._diode_on = diode_on_

    def set_offset(self, offset_):
        self._offset = offset_

    def get_offset(self):
        return self._offset

    def get_frequency_offset(self):
        return self._frequency_offset

    def set_diode_on(self, diode_on_):
        self._diode_on = diode_on_

    def get_diode_on(self):
        return self._diode_on

    def get_lna_on(self):
        return self._lna_on

    def get_channels(self):
        return self._n_ch

    def get_measurements_per_satellite(self):
        return self._measurements_per_satellite

    def get_measurements_per_frequency(self):
        return self._measurements_per_frequency

    def create_switched_measurement(self, sig_freq, ref_offset):
        return self._setup.create_switched_handler(
            self._offset, self._bw, self._n_ch, self._cal_fact,
            self._duration, self._diode_on, sig_freq, ref_offset)

    def create_unswitched_measurement(self, frequency):
        return self._setup.create_unswitched_handler(
            self._offset, self._bw, self._n_ch, self._cal_fact,
            self._duration, self._diode_on, frequency)
