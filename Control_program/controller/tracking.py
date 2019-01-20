from time import time, sleep
from threading import Thread

from controller.util import AzEl
from controller.telescope.telescope_controller import PositionUnreachable


class TrackingAborting(RuntimeError):
    """
    Exception to raise in case the measurement should be
    aborted. The exception should not be catched in any
    node, but instead where the observation is started.
    """
    pass


class TimedOut(RuntimeError):
    """
    Exception to raise if a waiting process timed out.
    """
    pass


class SatelliteTracker:
    """
    Tracks a satellite object by continously updating the target
    position for the telescope based on the target's current
    position.
    """
    def __init__(self, logger_, telescope_, target_, offset_=AzEl(0.0, 0.0),
                 update_int_=0.25, f_signal_if_lost_=(lambda: None),
                 f_signal_at_target_=(lambda: None)):
        self._logger = logger_
        self._telescope = telescope_
        self._target = target_
        self._offset = offset_
        self._signal_telescope_lost = f_signal_if_lost_

        self._tracking = False
        self._track_update_interval_s = update_int_

        self.__reached_target = f_signal_at_target_
        self.__at_target = self.__nothing
        self._reached_target = self.__at_target

        self._stop_if_aborting = self.__nothing

    def __enter__(self):
        self.start_tracking()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_tracking()
        return False

    def __nothing(self):
        return False

    def __stop_if_aborting(self):
        self._stop_if_aborting = self.__nothing
        raise TrackingAborting()

    def abort_tracking(self):
        self._stop_if_aborting = self.__stop_if_aborting

    def start_tracking(self):
        if self.is_tracking():
            return
        self._reached_target = self.__reached_target
        pos = AzEl.create_with_offset(self._target.compute_az_el(),
                                      self._offset.get_azimuth(),
                                      self._offset.get_elevation())
        # set initial target to avoid any race conditions.
        self._telescope.set_target(pos)
        self._tracker = Thread(target=self._track)
        self._tracking = True
        self._tracker.start()
        self._logger.info("Telescope started moving to %s @ %s ..."
                          % (self._target.name(), str(pos)))

    def stop_tracking(self):
        if not self.is_tracking():
            return
        self._tracking = False
        try:
            self._tracker.join()
            del self._tracker
        except RuntimeError as e:
            self._logger.error(e.message, exc_info=1)
        self._telescope.stop()
        self._reached_target = self.__at_target

    def is_tracking(self):
        return self._tracking

    def set_target(self, target_):
        self._target = target_
        self._reached_target = self.__reached_target

    def set_offset(self, offset_):
        self._offset = offset_
        self._reached_target = self.__reached_target

    def set_lost_callback(self, f_signal_if_lost_):
        self._signal_telescope_lost = f_signal_if_lost_

    def set_update_intervall(self, update_int_):
        self._track_update_interval_s = update_int_

    def get_target(self):
        return self._target

    def get_offset(self):
        return self._offset

    def connect_telescope_lost(self, f_signal_if_lost_):
        self._signal_telescope_lost = f_signal_if_lost_

    def connect_reached_target(self, f_signal_at_target_):
        self.__reached_target = f_signal_at_target_

    def _track(self):
        while self._tracking:
            if self._telescope.is_lost():
                self._signal_telescope_lost()
                break
            if self._telescope.is_at_target():
                self._reached_target()
            t_start = time()
            pos = AzEl.create_with_offset(self._target.compute_az_el(),
                                          self._offset.get_azimuth(),
                                          self._offset.get_elevation())
            try:
                self._telescope.set_target(pos)
            except PositionUnreachable as e:
                self._logger.trace(e.message, exc_info=1)
                break
            t_stop = time()
            t_sleep = self._track_update_interval_s - (t_stop - t_start)
            if t_sleep > 0:
                sleep(t_sleep)

    def reach_target(self, t_o=-1):
        """
        Block thread while telescope is moving.
        """
        cond = ((lambda: True) if t_o < 0 else
                (lambda t_end=time()+t_o: time() < t_end))
        while self.is_tracking() and not self._stop_if_aborting():
            if not cond():
                raise TimedOut(
                    "Timed out while reaching %s (telescope is at %s)"
                    % (str(self._target), str(self._telescope.get_current())))
            t0 = time()
            if self._telescope.is_close_to_target_beam():
                self._logger.info("Telescope is at %s @ %s." % (
                    self._target.name(), str(self._target.position())))
                return
            t_sleep = self._track_update_interval_s - (time()-t0)
            if t_sleep > 0:
                sleep(t_sleep)
