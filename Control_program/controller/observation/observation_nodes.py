from controller.util import overrides


class ObservationAborting(RuntimeError):
    """
    Exception to raise in case the measurement should be
    aborted. The exception should not be catched in any
    node, but instead where the observation is started.
    """
    pass


class AbstractObservationNode:
    """
    Base class for observation node.
    """
    def __init__(self):
        pass

    def execute(self, observation_node):
        raise NotImplementedError("Abstract Method")


class ObservationNode(AbstractObservationNode):
    """
    Performs an observation with current settings and starts the
    post processing. The settings are typically modified by
    instances of IntermeriateObservationNode.
    This should be the last node in an observation.
    """
    def __init__(self, logger_, telescope_, meas_setup_,
                 target_name_="target"):
        AbstractObservationNode.__init__(self)
        self._logger = logger_
        self._telescope = telescope_
        self._meas_setup = meas_setup_
        self._target_name = target_name_
        self._post_processer = None
        self._freq = 0
        self._band = "N/A"
        self._f_create_meas_handler = (lambda f: None)
        self._meas_handler = None

    @overrides(AbstractObservationNode)
    def execute(self, this):
        this._meas_handler = this._f_create_meas_handler(this._freq)
        this._logger.info("Observing %s on %.3f MHz (band %s)..."
                          % (this._target_name, this._freq*1e-6, this._band))
        this._meas_handler.measure()
        this._logger.info("Finished observing %s." % this._target_name)
        this._post_processer.execute(this._meas_handler.get_spectrum())
        del this._meas_handler

    def abort_measurement(self):
        if self._meas_handler:
            self._meas_handler.abort_measurement()

    def connect_post_processer(self, post_processer_):
        self._post_processer = post_processer_

    def set_offset(self, offset_):
        self._meas_setup.set_offset(offset_)

    def set_target_name(self, name_):
        self._target_name = name_

    def set_diode(self, enabled_):
        self._meas_setup.set_diode_on(enabled_)
        self._telescope.set_noise_diode(enabled_)

    def set_lna(self, enabled_):
        self._telescope.set_LNA(enabled_)

    def set_observation_frequency(self, freq_, band_="Unknown"):
        self._freq = freq_
        self._band = band_

    def get_observation_frequency(self):
        return self._freq

    def get_observation_band(self):
        return self._band

    def set_switched_measurement(self, ref_offset_):
        self._f_create_meas_handler = lambda f: self._meas_setup.create_switched_measurement(f, ref_offset_)

    def set_unswitched_measurement(self):
        self._f_create_meas_handler = lambda f: self._meas_setup.create_unswitched_measurement(f)


class IntermeriateObservationNode(AbstractObservationNode):
    """
    Base class for intermediate observation nodes. The
    purpose of derived classes will be to allow more
    complex observations to be performed. The derived
    classes should not directly call the observe method
    but instead to its thing and call the next step in
    the observation.
    """
    def __init__(self):
        AbstractObservationNode.__init__(self)
        self._next_step = None

    def connect(self, next_step):
        self._next_step = next_step


class FrequencyAlteringNode(IntermeriateObservationNode):
    """
    Base class for nodes that alters the observation
    frequency. Multiple derived classes should not be
    combined, but at least one such step must be included
    in the observation.
    """
    def __init__(self):
        IntermeriateObservationNode.__init__(self)


class SingleFrequencyNode(FrequencyAlteringNode):
    """
    Measurement with a single frequency.
    """
    def __init__(self, frequency_):
        FrequencyAlteringNode.__init__(self)
        self._freq = frequency_

    @overrides(FrequencyAlteringNode)
    def execute(self, observation_node):
        observation_node.set_observation_frequency(self._freq.get_frequency(),
                                                   self._freq.get_band())
        self._next_step.execute(observation_node)


class MultipleFrequencyNode(FrequencyAlteringNode):
    """
    Measurement with a multiple frequencies.
    """
    def __init__(self, frequencies_):
        FrequencyAlteringNode.__init__(self)
        self._frequencies = frequencies_

    @overrides(FrequencyAlteringNode)
    def execute(self, observation_node):
        for freq in self._frequencies:
            observation_node.set_observation_frequency(freq.get_frequency(),
                                                       freq.get_band())
            self._next_step.execute(observation_node)


class FrequencySwitchingNode(IntermeriateObservationNode):
    """
    Measurements with current frequency and then an offset
    from that frequency. This step can be combined with a
    FrequencyAlteringNode instance.
    """
    def __init__(self, switched_freq_offset_):
        IntermeriateObservationNode.__init__(self)
        self._switched_freq_offset = switched_freq_offset_

    @overrides(IntermeriateObservationNode)
    def execute(self, observation_node):
        sig_freq = observation_node.get_observation_frequency()
        band = observation_node.get_observation_band()
        try:
            self._next_step.execute(observation_node)
            observation_node.set_observation_frequency(
                sig_freq + self._switched_freq_offset, "Switched")
            self._next_step.execute(observation_node)
        finally:
            # observation frequency should be restored whatever happens
            observation_node.set_observation_frequency(sig_freq, band)


class RepeatingNode(IntermeriateObservationNode):
    """
    Performs multiple identical observations. The observations
    are identical in the sense that this step itself does not
    alter anything in then observation instance, it only invokes
    the next step a given number of times.
    """
    def __init__(self, repeats_):
        IntermeriateObservationNode.__init__(self)
        self._repeats = repeats_

    @overrides(IntermeriateObservationNode)
    def execute(self, observation_node):
        for i in xrange(self._repeats):
            self._next_step.execute(observation_node)


class LNANode(IntermeriateObservationNode):
    def __init__(self):
        IntermeriateObservationNode.__init__(self)

    @overrides(IntermeriateObservationNode)
    def execute(self, observation_node):
        try:
            observation_node.set_lna(True)
            self._next_step.execute(observation_node)
        finally:
            # LNA should be turned off whatever happens
            observation_node.set_lna(False)


class DiodeNode(IntermeriateObservationNode):
    """
    Performs measurement measurement with then noise diode turend on.
    """
    def __init__(self):
        IntermeriateObservationNode.__init__(self)

    @overrides(IntermeriateObservationNode)
    def execute(self, observation_node):
        try:
            observation_node.set_diode(True)
            self._next_step.execute(observation_node)
        finally:
            # diode should be turned off whatever happens
            observation_node.set_diode(False)


class DiodeSwitchingNode(IntermeriateObservationNode):
    """
    Performs one measurement with the noise diode turend on
    and then one with the noise diode turned off.
    """
    def __init__(self):
        IntermeriateObservationNode.__init__(self)

    @overrides(IntermeriateObservationNode)
    def execute(self, observation_node):
        try:
            observation_node.set_diode(True)
            self._next_step.execute(observation_node)
        finally:
            # diode should be turned off whatever happens
            observation_node.set_diode(False)
        self._next_step.execute(observation_node)


class WaitForUserInputNode(IntermeriateObservationNode):
    """
    Performs the measurement and then wait for user input
    before returning.
    """
    def __init__(self):
        IntermeriateObservationNode.__init__(self)

    @overrides(IntermeriateObservationNode)
    def execute(self, observation_node):
        self._next_step.execute(observation_node)
        # wait for user to press return
        raw_input("\n--> Press return to continue.")


class MeasurementAlteringNode(IntermeriateObservationNode):
    """
    This node sets the type of measurement to be performed.
    The type can for example be signal or switched (meaning
    that a signal measurement and a reference measurement are
    performed and the referecne is subtraced from then signal).
    One such node must be included in the observation.
    """
    def __init__(self):
        IntermeriateObservationNode.__init__(self)


class SignalNode(MeasurementAlteringNode):
    """
    Sets the measurement type to signal/non-switched.
    """
    def __init__(self):
        MeasurementAlteringNode.__init__(self)

    @overrides(MeasurementAlteringNode)
    def execute(self, observation_node):
        observation_node.set_unswitched_measurement()
        self._next_step.execute(observation_node)


class SwitchingNode(MeasurementAlteringNode):
    """
    Sets the measurement type to switched.
    """
    def __init__(self, ref_offset_):
        MeasurementAlteringNode.__init__(self)
        self._ref_offset = ref_offset_

    @overrides(MeasurementAlteringNode)
    def execute(self, observation_node):
        observation_node.set_switched_measurement(self._ref_offset)
        self._next_step.execute(observation_node)


class TrackingAlteringNode(IntermeriateObservationNode):
    """
    This node alters the target tracking.
    At mose one such node should be included in the observation.
    """
    def __init__(self):
        IntermeriateObservationNode.__init__(self)


class BeamSwitchingNode(TrackingAlteringNode):
    """
    Performs one measurement without an explicit offset (i.e. the
    current offset, if any) and one measurement with an offset.
    """
    def __init__(self, tracker_, offset_):
        TrackingAlteringNode.__init__(self)
        self._tracker = tracker_
        self._offset = offset_

    @overrides(TrackingAlteringNode)
    def execute(self, observation_node):
        old_offs = self._tracker.get_offset()
        # continue without explicit offset
        self._next_step.execute(observation_node)
        self._tracker.stop_tracking()
        self._tracker.set_offset(self._offset)
        observation_node.set_offset(self._offset)
        self._tracker.start_tracking()
        self._tracker.reach_target()
        # continue with explicit offset
        self._next_step.execute(observation_node)

        # switch back to old offset
        self._tracker.stop_tracking()
        self._tracker.set_offset(old_offs)
        observation_node.set_offset(old_offs)
        self._tracker.start_tracking()
        self._tracker.reach_target()
