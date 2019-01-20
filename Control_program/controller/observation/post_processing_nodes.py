from datetime import datetime
from os import remove
from controller.util import overrides


class AbstractPostProcessingNode:
    def __init__(self, logger):
        self._logger = logger

    def execute(self, spectrum):
        """
        Applies a post-processing step to spectrum.
        The data in spectrum should be altered.

        Parameters
        ----------
        spectrum : SALSA_spectrum
            Object containing data from observation.

        Returns
        -------
        out : None
            The metod should change then data directly in
            spectrum instead of returning a new instance
            with the altered data.
        """
        raise NotImplementedError("Abstract method")


class PostProcessingTerminatingNode(AbstractPostProcessingNode):
    def __init__(self, logger):
        AbstractPostProcessingNode.__init__(self, logger)

    @overrides(AbstractPostProcessingNode)
    def execute(self, spectrum):
        return


class PostProcessingNode(AbstractPostProcessingNode):
    def __init__(self, logger):
        AbstractPostProcessingNode.__init__(self, logger)
        self._next_step = PostProcessingTerminatingNode(logger)

    def connect(self, next_step):
        self._next_step = next_step


class DecimateChannelsNode(PostProcessingNode):
    """
    Average to desired number of channels.
    """
    def __init__(self, logger, channels_):
        PostProcessingNode.__init__(self, logger)
        self._channels = channels_

    @overrides(PostProcessingNode)
    def execute(self, spectrum):
        spectrum.decimate_channels(self._channels)
        self._next_step.execute(spectrum)


class ShiftToVLSRFrameNode(PostProcessingNode):
    """
    Correct VLSR; translating freq/vel to LSR frame of reference.
    """
    def __init__(self, logger):
        PostProcessingNode.__init__(self, logger)

    @overrides(PostProcessingNode)
    def execute(self, spectrum):
        self._logger.info("Translating freq/vel to LSR frame of reference.")
        spectrum.shift_to_vlsr_frame()
        self._next_step.execute(spectrum)


class RemoveRFINode(PostProcessingNode):
    """
    Removes radio frequency interference from data.
    """
    def __init__(self, logger):
        PostProcessingNode.__init__(self, logger)

    @overrides(PostProcessingNode)
    def execute(self, spectrum):
        self._logger.info("Removing RFI from signal...")
        spectrum.auto_edit_bad_data()
        self._next_step.execute(spectrum)


class UploadToArchiveNode(PostProcessingNode):
    """
    Uploads the spectrum to then spectrum's database.
    The spectrum is saved in txt, FITS and png formats.
    """
    def __init__(self, logger, fig_, tmp_file_,
                 f_update_plot_, save_vel_=True):
        PostProcessingNode.__init__(self, logger)
        self._fig = fig_
        self._tmp_file = tmp_file_
        self._f_update_plot = f_update_plot_
        self._save_vel = save_vel_

    @overrides(PostProcessingNode)
    def execute(self, spectrum):
        # Save temporary files
        txtfile = "%s.txt" % self._tmp_file
        if self._save_vel:
            spectrum.save_to_txt_vel(txtfile)
        else:
            spectrum.save_to_txt_freq(txtfile, spectrum.get_observation_freq())
        fitsfile = "%s.fits" % self._tmp_file
        spectrum.save_to_fits(fitsfile)
        pngfile = "%s.png" % self._tmp_file
        self._f_update_plot()
        self._fig.savefig(pngfile)

        spectrum.upload_to_archive(fitsfile, pngfile, txtfile)
        try:                    # remove temporary files
            remove(txtfile)
            remove(fitsfile)
            remove(pngfile)
        except EnvironmentError:  # in case we can not remove it
            pass
        self._next_step.execute(spectrum)


class DisplayObservationDataNode(PostProcessingNode):
    def __init__(self, logger):
        PostProcessingNode.__init__(self, logger)

    @overrides(PostProcessingNode)
    def execute(self, spectrum):
        self._logger.info(
            "SPECTRUM INFO: Offset_alt=%.3f deg, Offset_az=%.3f deg, "
            "Total power = %e, alt=%.3f, az=%.3f" %
            (spectrum.get_offset_el(), spectrum.get_offset_az(),
             spectrum.get_total_power(), spectrum.get_elevation(),
             spectrum.get_azimuth()))


class SaveSpectrumTXTNode(PostProcessingNode):
    def __init__(self, logger, target_, measurement_series_):
        PostProcessingNode.__init__(self, logger)
        self._target = target_
        self._meas_series = measurement_series_

    @overrides(PostProcessingNode)
    def execute(self, spectrum):
        self._meas_series.save_spectrum_txt(datetime.now().timetuple(),
                                            self._target.name(), spectrum)
        self._next_step.execute(spectrum)


class SaveObservationDataNode(PostProcessingNode):
    def __init__(self, logger, target_, measurement_series_):
        PostProcessingNode.__init__(self, logger)
        self._target = target_
        self._meas_series = measurement_series_

    @overrides(PostProcessingNode)
    def execute(self, spectrum):
        observed_temperature = spectrum.get_total_power()
        pos = self._target.position()
        t_start = datetime.now().timetuple()
        self._meas_series.append_output(t_start, self._target.name(),
                                        spectrum.get_observation_freq()*1e-6,
                                        pos.get_azimuth(), pos.get_elevation(),
                                        observed_temperature,
                                        spectrum.get_offset_az(),
                                        spectrum.get_offset_el(),
                                        spectrum.get_diode_on())
        self._next_step.execute(spectrum)


class CustomNode(PostProcessingNode):
    def __init__(self, logger, f_process_spectrum_):
        PostProcessingNode.__init__(self, logger)
        self._process_spectrum = f_process_spectrum_

    @overrides(PostProcessingNode)
    def execute(self, spectrum):
        self._process_spectrum(spectrum)
        self._next_step.execute(spectrum)
