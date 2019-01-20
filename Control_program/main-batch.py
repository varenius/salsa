#!/usr/bin/env python2

from argparse import ArgumentParser
from logging import (
    getLogger, Formatter, StreamHandler, FileHandler,
    NOTSET, DEBUG, INFO, WARN, ERROR, CRITICAL, FATAL
)
from os import path, makedirs
from re import sub
from glob import glob
from time import time, sleep
from multiprocessing.pool import ThreadPool
from socket import socket, AF_INET, SOCK_STREAM
from getpass import getuser
from ConfigParser import ConfigParser

from ephem import Observer, now, degrees
from numpy import radians, arange, array, float64

from controller.tle.tle_ephem import TLEephem
from controller.util import (
    project_file_path, TelescopeFileOutput, AzEl, progressbar,
    overrides
)
from controller.pyprogbar.progressbar import (
    get_default_config, pbt_frac_color
)
from controller.path.path_finder import (
    PathFindingManager, CelestialObjectMapping, EmptyPath
)
from controller.path.wrappers import PathFinderWrapper
from controller.satellites.poscomp import (
    SatPosComp, CelObjComp, ManualComp
)
from controller.satellites.posmodel import PositionModel
from controller.satellites.satellite import ReferenceSatellite
from controller.telescope.telescope_controller import (
    TelescopeController, PositionUnreachable
)
from controller.telescope.communication_handler import TelescopeCommunication
from controller.telescope.connection_handler import TelescopeConnection
from controller.telescope.position_interface import TelescopePosInterface
from controller.observation.measurement import (
    WarnOnNaN, MeasurementSetup, BatchMeasurementSetup
)
from controller.observation.spectrum import ArchiveConnection
from controller.observation.receiver import SALSA_Receiver
from controller.frequency_translation import (
    Frequency, BandToFrequencyConverter,
    GPS_FT, GLONASS_FT, GALILEO_FT, BEIDOU_FT, ASTRO_FT
)
from controller.tracking import SatelliteTracker, TrackingAborting, TimedOut
from controller.observation.observation_nodes import (
    ObservationNode, MultipleFrequencyNode, SignalNode,
    SwitchingNode, RepeatingNode, DiodeSwitchingNode,
    LNANode, BeamSwitchingNode, WaitForUserInputNode
)
from controller.observation.post_processing_nodes import (
    DecimateChannelsNode, RemoveRFINode, SaveObservationDataNode,
    DisplayObservationDataNode, PostProcessingTerminatingNode,
    SaveSpectrumTXTNode
)


class EvalFrequencyError(RuntimeError):
    pass


class EvalBandError(RuntimeError):
    pass


class NotTracking(RuntimeError):
    pass


class FatalError(BaseException):
    pass


class BatchMeasurementHandler:
    def __init__(self, logger_, output_, telescope_, measurement_setup_,
                 progressbar_, tracker_, path_finder, stow_pos_,
                 wait_int_=0.25):
        self._logger = logger_
        self._output = output_
        self._telescope = telescope_
        self._setup = measurement_setup_
        self._progressbar = progressbar_
        self._tracker = tracker_
        self._path_finder = path_finder

        self._stow_pos = stow_pos_
        self._wait_update_interval_s = wait_int_
        self._obs_node = None

    def terminate(self):
        self._telescope.set_target(self._stow_pos)
        self._telescope.terminate()

    def telescope_lost_action(self):
        self._tracker.abort_tracking()

    def abort(self):
        self._logger.info("Aborting measurement.")
        if self._obs_node:
            self._obs_node.abort_measurement()

    def __enter__(self):
        self._progressbar.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._progressbar.stop()
        return False

    def _try_recover(self):
        try:
            self._logger.info("Issuing a soft reset on the telescope...")
            self.reset_telescope(600)
        except TimedOut:
            self._logger.critical("Soft reset timed out.")
            try:
                self._logger.info("Issuing a hard reset on the telescope...")
                self.reset_telescope(600, True)
            except TimedOut:
                self._logger.fatal("Hard reset timed out. Panic!")
                raise FatalError()

    def batch_loop(self):
        for target in self._path_finder:
            try:
                with self.start_tracking(target) as tracker:
                    tracker.reach_target(600)
                    self.observe(self.create_frequency_list(target))
            except TrackingAborting:
                self._logger.error(
                    "Tracking was aborted for %s because the telescope is "
                    "stuck at %s. Attempting to recover"
                    % (str(target), str(self._telescope.get_current())))
                self._try_recover()
            except (TimedOut, PositionUnreachable, NotTracking) as e:
                self._logger.error(e.message, exc_info=1)

    def get_tracker(self):
        return self._tracker

    def start_tracking(self, sat):
        self._tracker.set_target(sat)
        return self._tracker

    def observe(self, freqs):
        if not self._tracker.is_tracking():
            raise NotTracking("Telescope is not tracking anything.")
        target = self._tracker.get_target()

        # connect observation steps
        if self._setup.get_frequency_offset() != 0.0:
            ref_offset = self._setup.get_frequency_offset()
            prev_node = first_obs_node = SwitchingNode(ref_offset)
        else:
            prev_node = first_obs_node = SignalNode()
        if self._setup.get_lna_on():
            lna_node = LNANode()
            prev_node.connect(lna_node)
            prev_node = lna_node
        if True:                # placeholder for actual condition
            mul_obs_node = RepeatingNode(self._setup.get_measurements_per_satellite())
            prev_node.connect(mul_obs_node)
            prev_node = mul_obs_node
        if self._setup.get_offset() != AzEl(0, 0):
            # Since actual offset should initialy be set in tracker
            # and measurement setup, we should switch to zero offset.
            beam_node = BeamSwitchingNode(self._tracker, AzEl(0, 0))
            prev_node.connect(beam_node)
            prev_node = beam_node
        if True:                # placeholder for actual condition
            mul_freq_node = MultipleFrequencyNode(freqs)
            prev_node.connect(mul_freq_node)
            prev_node = mul_freq_node
        if True:                # placeholder for actual condition
            mul_obs_node = RepeatingNode(self._setup.get_measurements_per_frequency())
            prev_node.connect(mul_obs_node)
            prev_node = mul_obs_node
        if self._setup.get_diode_on():
            diode_node = DiodeSwitchingNode()
            prev_node.connect(diode_node)
            prev_node = diode_node
        obs_node = ObservationNode(self._logger, self._telescope, self._setup,
                                   target.name())
        prev_node.connect(obs_node)

        # connect post-processing nodes
        prev_node = first_pp_node = RemoveRFINode(self._logger)
        obs_node.connect_post_processer(first_pp_node)
        if True:                # placeholder for actual condition
            decch_node = DecimateChannelsNode(self._logger, self._setup.get_channels())
            prev_node.connect(decch_node)
            prev_node = decch_node
        if True:                # placeholder for actual condition
            save_spec_node = SaveSpectrumTXTNode(self._logger, target, self._output)
            prev_node.connect(save_spec_node)
            prev_node = save_spec_node
        if True:                # placeholder for actual condition
            save_data_node = SaveObservationDataNode(self._logger, target, self._output)
            prev_node.connect(save_data_node)
            prev_node = save_data_node
        if True:                # placeholder for actual condition
            disp_data_node = DisplayObservationDataNode(self._logger)
            prev_node.connect(disp_data_node)
            prev_node = disp_data_node
        if True:                # placeholder for actual condition
            term_node = PostProcessingTerminatingNode(self._logger)
            prev_node.connect(term_node)
            prev_node = term_node

        # execute observation and post processing
        self._obs_node = obs_node
        first_obs_node.execute(obs_node)
        self._obs_node = None

    def wait_for_reset(self, cond=lambda: True):
        while True:
            if not cond():
                raise TimedOut("Timed out while waiting for reset")
            t0 = time()
            if self._telescope.isreset():
                self._logger.info("Telescope is reset")
                return
            t_sleep = self._wait_update_interval_s - (time()-t0)
            if t_sleep > 0:
                sleep(t_sleep)

    def reset_telescope(self, t_o=-1, hard_reset=False):
        """
        Stops and resets the telescope
        """
        self._logger.info("Telescope is resetting ...")
        self._telescope.reset(hard_reset)
        if t_o < 0:
            self.wait_for_reset(lambda: True)
        elif t_o > 0:
            self.wait_for_reset(lambda t_end=time()+t_o: time() < t_end)

    def create_frequency_list(self, target):
        raise NotImplementedError("Abstract Method")


class BatchBandMeasurementHandler(BatchMeasurementHandler):
    def __init__(self, logger_, output_, telescope_, measurement_setup_,
                 progressbar_, tracker_, path_finder_, stow_pos_, band_to_fc_,
                 wait_int_=0.25):
        BatchMeasurementHandler.__init__(
            self, logger_, output_, telescope_, measurement_setup_,
            progressbar_, tracker_, path_finder_, stow_pos_, wait_int_=wait_int_)
        self._b2fc = band_to_fc_

    @overrides(BatchMeasurementHandler)
    def create_frequency_list(self, target):
        freqs = list()
        for band in self._b2fc.get_bands(target.get_constellation()):
            try:
                freqs.append(self._b2fc.get_freq(target.get_constellation(),
                                                 band, target.name()))
            except KeyError:
                self._logger.critical("Could not get valid frequency for "
                                      "%s on %s. Skipping" % (target.name(), band))
        return freqs


class BatchFrequencyMeasurementHandler(BatchMeasurementHandler):
    def __init__(self, logger_, output_, telescope_, measurement_setup_,
                 progressbar_, tracker_, path_finder_, stow_pos_, frequencies_,
                 wait_int_=0.25):
        BatchMeasurementHandler.__init__(
            self, logger_, output_, telescope_, measurement_setup_,
            progressbar_, tracker_, path_finder_, stow_pos_, wait_int_=wait_int_)
        self._frequencies = frequencies_

    @overrides(BatchMeasurementHandler)
    def create_frequency_list(self, target):
        return [Frequency(f) for f in self._frequencies]


def eval_bands(s):
    s = sub("\\s*", "", s)  # remove whitespace
    if s.startswith("[") and s.endswith("]"):  # list of frequency bands
        s = sub("\\]$", "", sub("^\\[", "", s)) # remove first [ and last ]
        return [e.split(",") for e in s.split("],[")]
    raise EvalBandError("Input string is not a list of frequency bands")


def eval_frequencies(s):
    if s.startswith("range") and "(" in s and ")" in s:  # range(start,stop,step)
        args = s[s.find("(")+1:s.find(")")].split(",")
        argsf = [float(arg) for arg in args]
        f_start, f_stop, f_step = 1000, 2001, 100
        if len(args) == 1:  # range(0, args[0], 1)  MHz
            if argsf[0] > f_start and argsf[0] < f_stop:
                f_stop = argsf[0]
        elif len(args) >= 2:  # range(args[0], args[1], 1)  MHz
            if argsf[0] > f_start and argsf[0] < f_stop:
                f_start = argsf[0]
            if argsf[1] > f_start and argsf[1] < f_stop:
                f_stop = argsf[1]
            if len(args) == 3:  # range(args[0], args[1], args[2])
                if argsf[2] > 0 and argsf[2] < f_stop - f_start:
                    f_step = argsf[2]
        return arange(f_start, f_stop, f_step, dtype=float64)*1e6
    elif "[" not in s and "]" not in s:  # comma-separated list of frequencies
        return array([float(f) for f in s.split(",")], dtype=float64)*1e6
    raise EvalFrequencyError("Input string is not a list of frequencies")


class EvalSatelliteError(RuntimeError):
    pass


def eval_satellites(constel, s):
    if constel.lower() == "manual":
        # 's' should be on the form "(az0,el0),(az1,el1),..."
        s = sub("\\s*", "", s)  # remove whitespace
        if s.startswith("(") and s.endswith(")"):
            s = sub("\\)$", "", sub("^\\(", "", s))
            return [("(%s)" % e) for e in s.split("),(")]
        raise EvalSatelliteError("Input string is not a list of (az,el)-tuples")
    else:
        # 's' should be on the form "sat0,sat1,..." or empty ("")
        return filter(None, s.split(","))


def load_logger(cfg_):
    logger = getLogger(__file__)
    logger.setLevel({
        "debug": DEBUG,
        "info": INFO,
        "warn": WARN,
        "error": ERROR,
        "critical": CRITICAL,
        "fatal": FATAL
    }.get(cfg_.get("LOGGING", "type").lower(), NOTSET))
    fmt = Formatter('[%(asctime)s] [%(levelname)s] %(message)s', "%H:%M:%S")

    # create console handler
    ch = StreamHandler()
    ch.setLevel(DEBUG)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # create file handler
    log_dir = path.dirname(path.abspath(cfg_.get("LOGGING", "file")))
    if not path.exists(log_dir):
        makedirs(log_dir)
    fh = FileHandler(cfg_.get("LOGGING", "file"))
    fh.setLevel(DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger


def load_site(salsa_cfg_):
    site = Observer()
    site.name = salsa_cfg_.get("SITE", "name")
    site.date = now()
    site.lat = degrees(salsa_cfg_.get("SITE", "latitude"))
    site.lon = degrees(salsa_cfg_.get("SITE", "longitude"))
    site.elev = salsa_cfg_.getfloat("SITE", "elevation")
    return site


def load_telescope_control(logger_, salsa_cfg_):
    # Create connection to RIO
    host = salsa_cfg_.get("RIO", "host")
    port = salsa_cfg_.getint("RIO", "port")
    s = socket(AF_INET, SOCK_STREAM)
    tcom = TelescopeCommunication(logger_, TelescopeConnection(host, port, s))

    lim = TelescopePosInterface(tcom,
                                salsa_cfg_.getfloat("RIO", "minaz"),
                                salsa_cfg_.getfloat("RIO", "minal"))

    # Read stow position from config file
    stow_pos = AzEl(salsa_cfg_.getfloat("RIO", "stowaz"),
                    salsa_cfg_.getfloat("RIO", "stowal"))

    tolerance = salsa_cfg_.getfloat("RIO", "close_enough")

    return TelescopeController(logger_, tcom, stow_pos, lim, tolerance)


def load_batch_measurement_handler(logger_, site_, telescope_, progressbar_,
                                   path_finder_, batch_cfg_, salsa_cfg_):
    username = getuser()
    dbconn = ArchiveConnection(salsa_cfg_.get("ARCHIVE", "host"),
                               salsa_cfg_.get("ARCHIVE", "database"),
                               salsa_cfg_.get("ARCHIVE", "user"),
                               salsa_cfg_.get("ARCHIVE", "password"),
                               salsa_cfg_.get("ARCHIVE", "table"))
    tmpdir = salsa_cfg_.get('USRP', 'tmpdir')
    rcv = SALSA_Receiver(salsa_cfg_.get("USRP", "host"),
                         "%s/SALSA_%s.tmp" % (tmpdir, username))
    rcv.set_gain(salsa_cfg_.getfloat("USRP", "usrp_gain"))
    # Using both upper and lower sideband, so bandwidth is equal to
    # sampling rate, not half.
    rcv.set_sample_rate(batch_cfg_.getfloat("MEASUREMENT", "bandwidth") * 1e6)

    # use 1 process for signal
    tp_signal = ThreadPool(processes=1)
    # use 1 process for signal and 1 for reference
    tp_switched = ThreadPool(processes=2)
    nan_handler = WarnOnNaN(logger_)
    meas_setup = MeasurementSetup(logger_, nan_handler, site_,
                                  telescope_.get_current, dbconn, rcv,
                                  username, tp_signal, tp_switched)
    bw = batch_config.getfloat("MEASUREMENT", "bandwidth") * 1e6
    n_ch = batch_config.getint("MEASUREMENT", "nchanels")
    cal_fact = batch_config.getfloat("MEASUREMENT", "calfact")
    duration = batch_config.getfloat("MEASUREMENT", "measurement-time-per-sat")
    offset = AzEl(batch_config.getfloat("MEASUREMENT", "azimuth-offset"),
                  batch_config.getfloat("MEASUREMENT", "elevation-offset"))
    frequency_offset = batch_config.getfloat("MEASUREMENT", "frequency-offset") * 1e6
    obs_per_sat = batch_config.getint("MEASUREMENT", "observations-per-satellite")
    obs_per_freq = batch_config.getint("MEASUREMENT", "observations-per-frequency")
    use_lna = batch_config.get("MEASUREMENT", "lna").lower() == "true"
    use_diode = batch_config.get("MEASUREMENT", "diode_switching").lower() == "true"
    mul_meas_setup = BatchMeasurementSetup(
        meas_setup, bw, n_ch, cal_fact, duration, offset, frequency_offset,
        obs_per_sat, obs_per_freq, use_lna, use_diode)

    stow_az = salsa_cfg_.getfloat("RIO", "stowaz")
    stow_el = salsa_cfg_.getfloat("RIO", "stowal")
    stow_pos = AzEl(stow_az, stow_el)
    stow_sat = ReferenceSatellite("Stow", PositionModel(lambda: AzEl(stow_az, stow_el)))
    tracker = SatelliteTracker(logger_, telescope_, stow_sat,
                               offset_=offset, update_int_=0.25)

    mh = None
    output_dest = TelescopeFileOutput(batch_cfg_.get("RESULT", "data_dir"))
    try:
        systems = batch_config.get("GNSS-SYS", "systems").split(",")
        bands = eval_bands(batch_config.get("MEASUREMENT", "frequency-bands"))
        sys_to_band = {k: v for k, v in zip(systems, bands)}

        sky_frequency = batch_config.getfloat("MEASUREMENT", "sky-frequency") * 1e6
        constel_to_ft = {
            "GPS": GPS_FT.create_with_typical_values(sky_frequency),
            "COSMOS": GLONASS_FT.create_with_typical_values(sky_frequency),
            "GSAT": GALILEO_FT.create_with_typical_values(sky_frequency),
            "BEIDOU": BEIDOU_FT.create_with_typical_values(sky_frequency),
            "ASTRO": ASTRO_FT.create_with_typical_values(sky_frequency)
        }

        b2fc = BandToFrequencyConverter(sys_to_band, constel_to_ft)
        mh = BatchBandMeasurementHandler(
            logger_, output_dest.create_new_measurement_series(),
            telescope_, mul_meas_setup, progressbar_, tracker,
            path_finder_, stow_pos, b2fc)
    except EvalBandError:
        try:
            frequencies = eval_frequencies(batch_config.get("MEASUREMENT",
                                                            "frequency-bands"))
            mh = BatchFrequencyMeasurementHandler(
                logger_, output_dest.create_new_measurement_series(),
                telescope_, mul_meas_setup, progressbar_, tracker,
                path_finder_, stow_pos, frequencies)
        except EvalFrequencyError:
            raise RuntimeError("Error evaluating bands/frequencies")
    tracker.set_lost_callback(mh.telescope_lost_action)
    return mh


def load_pathfinder(logger_, site_, telescope_,
                    salsa_cfg_, batch_cfg_, tle_cfg_):
    # """  # batch measurements
    systems = batch_cfg_.get("GNSS-SYS", "systems")

    load_astro = systems == "ASTRO"
    if not load_astro and "ASTRO" in systems:
        logger_.warn("Mixing ASTRO with MANUAL/GNSS constellations is not supprorted.")
    load_manual = systems == "MANUAL"
    if not load_manual and "MANUAL" in systems:
        logger_.warn("Mixing MANUAL with ASTRO/GNSS constellations is not supprorted.")

    constellations_ = filter(None, batch_cfg_.get("GNSS-SYS", "systems").split(","))
    satellites_ = list()
    try:
        satellites_ = eval_satellites(systems, batch_cfg_.get("GNSS-SAT", "satellites"))
    except EvalSatelliteError:
        pass
    if satellites_:
        constellations_ = list()

    if load_astro:
        obj_pos_comp = CelObjComp(site_)
    elif load_manual:
        obj_pos_comp = ManualComp(satellites_)
    else:
        tle_files = glob(path.join(tle_cfg_.get("TLE", "output-dir"), "*.tle"))
        obj_pos_comp = SatPosComp(TLEephem(tle_files, site_))

    ref_sat = ReferenceSatellite("Telescope",
                                 PositionModel(lambda: telescope_.get_current()))

    el_cutoff_ = max(min(batch_cfg_.getfloat("PATHFIND", "elevation-cutoff-angle"), 90.0), 0.0)
    max_batch_size_ = max(5, batch_cfg_.getint("PATHFIND", "maximum-batch-size"))

    pf_wrapper = PathFinderWrapper(dict(), ref_sat,
                                   lambda p1, p2: radians(telescope_.get_distance(p1, p2)),
                                   max_batch_size_)
    pf = PathFindingManager(logger_, obj_pos_comp, pf_wrapper,
                            satellites_, constellations_, el_cutoff_)
    """
    azimuth_offset = batch_cfg_.get("MEASUREMENT", "azimuth-offset")
    elevation_offset = batch_cfg_.get("MEASUREMENT", "elevation-offset")
    obj_pos_comp = CelObjComp(site_)
    pf = CelestialObjectMapping(logger, obj_pos_comp.load_satellite("Sun"),
                                AzEl(azimuth_offset, elevation_offset),
                                9, 9, 0.5, 0.5)
    """  # grid measurements
    return pf


def make_config_parser(from_file):
    cp = ConfigParser()
    cp.read(from_file)
    return cp


def load_progressbar(rows):
    pbcfg = get_default_config()
    pbcfg.type = pbt_frac_color
    pbcfg.rows = rows
    return progressbar(pbcfg)


if __name__ == "__main__":
    parser = ArgumentParser(description='Execute a batch measurement using a set of configurations')
    parser.add_argument("-s", "--salsa-cfg",
                        action="store", dest="salsa_cfg_path",
                        type=str, required=False,
                        help="/path/to/SALSA.cfg that defines the SALSA configuration.")
    parser.add_argument("-b", "--batch-cfg",
                        action="store", dest="batch_cfg_path",
                        type=str, required=False,
                        help="/path/to/batch_config.cfg that defines the batch measurement.")

    batch_config = make_config_parser(parser.batch_cfg_path if hasattr(parser, "batch_cfg_path") else
                                      project_file_path("/config/batch-measurement.cfg"))
    salsa_config = make_config_parser(parser.salsa_cfg_path if hasattr(parser, "salsa_cfg_path") else
                                      project_file_path("/config/SALSA.cfg"))
    tle_config = make_config_parser(project_file_path("/config/tle.cfg"))

    prgbar = load_progressbar(1)
    logger = load_logger(batch_config)
    telescope = load_telescope_control(logger, salsa_config)

    site = load_site(salsa_config)
    pf = load_pathfinder(logger, site, telescope,
                         salsa_config, batch_config, tle_config)
    window = load_batch_measurement_handler(logger, site, telescope, prgbar,
                                            pf, batch_config, salsa_config)

    scan_time = batch_config.getfloat("MEASUREMENT", "scan-time") * 60 * 60
    intervall = batch_config.getfloat("MEASUREMENT", "measurement-intervall")
    logger.info(("Measurement config:\n"
                 "\t%.3f seconds per satellite.\n"
                 "\t%.1f hours total scan time\n"
                 "\t%.1f minutes between measurements")
                % (batch_config.getfloat("MEASUREMENT", "measurement-time-per-sat"),
                   batch_config.getfloat("MEASUREMENT", "scan-time"),
                   batch_config.getfloat("MEASUREMENT", "measurement-intervall")))

    try:
        t_start = time()
        prgbar.add_row(lambda: 100*(time()-t_start)/scan_time, lambda: "Progress")
        window.reset_telescope(600)
        window.wait_for_reset()
        with window:
            while time()-t_start < scan_time:
                logger.info("Starting new observation lap.")

                t0 = time()
                try:
                    window.batch_loop()
                except EmptyPath as e:
                    retry_in = 60
                    logger.warn("%s. Retrying in %d seconds" % (e.message, retry_in))
                    sleep(retry_in)
                    continue
                t_observation = time() - t0

                logger.info("Lap took %.2f seconds." % (t_observation))
                t_sleep = intervall - t_observation
                if t_sleep > 0:
                    logger.info("Sleeping for %.2f s before next run" % (t_sleep))
                    sleep(t_sleep)
            logger.info("~Scan complete~")
    except (BaseException, FatalError) as e:
        logger.fatal("Observation ended unexpectedly.")
        logger.error(e.message, exc_info=1)
    finally:
        window.terminate()
