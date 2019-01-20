from time import sleep
from numpy import degrees
from controller.util import AzEl, angular_dist_azel


class TelescopeController:
    """
    Provides functions to communicate with the RIO telescope driver
    device.  This uses the DMC language communicated via telnet using
    python socket connections.
    """

    def __init__(self, logger_, tcom_, stow_pos_, limits_, tolerance_):
        """
        Creates a new object with a connection to the RIO driver
        device.
        """
        self._logger = logger_
        self._tcom = tcom_
        self._stow_pos = stow_pos_
        self._limits = limits_
        self._tolerance = tolerance_

    def terminate(self):
        self._tcom.terminate()

    def set_LNA(self, turned_on):
        status = "ON" if turned_on else "OFF"
        if self._tcom.set_LNA(turned_on):
            self._logger.info("RIO: LNA is now %s." % (status))

    def set_noise_diode(self, turned_on):
        status = "ON" if turned_on else "OFF"
        if self._tcom.set_noise_diode(turned_on):
            self._logger.info("RIO: Noise diode is now %s." % (status))

    def reset(self, hard_reset=False):
        if hard_reset:
            self._logger.info("RIO: Initializing hard reset")
            if self._tcom.reset_hardware():
                self._logger.info("RIO: Control hardware successfully reset to power-on state.")
                sleep(1.0)
            else:
                self._logger.info("RIO: Control hardware failed to reset to power-on state.")
        else:
            self._logger.info("RIO: Initializing soft reset")
        if self._tcom.reset_pointing():
            self._logger.info("RIO: Moving telescope to end position. Please wait...")
            sleep(1.0)
        else:
            self._logger.info("RIO: Unable to move to end position. ")

    def is_moving(self):
        """
        Returns true if telescope motors are on, false if motors are off.
        """
        return self._tcom.motors_running()

    def is_lost(self):
        """
        Check if telescope is lost and needs a reset.
        """
        return not self._tcom.get_know_pos()

    def isreset(self):
        """
        Check if telescope has reached reset position.
        """
        return self._tcom.get_know_pos()

    def set_pos_ok(self):
        # deprecated
        return

    def get_pos_ok(self):
        """
        Check if the telescope knows where it is, i.e. if there has
        been a power cut. If "knowpos"=1, then all is well.
        If knowpos = 0, then the telscope has been reset due to a
        power cut, and is currently in its power-on state where it
        does not know the position. A reset is needed. here.
        """
        return self._tcom.get_know_pos()

    def stop(self):
        """
        Stops any movement of the telescope by setting target to current.
        """
        if self._tcom.motors_running():
            self._tcom.stop_motors()

    def can_reach(self, az, el):
        """
        Check if telescope can reach this position. Assuming input in degrees.

        All directions might not be possible due to telescope mechanics. Also,
        some angles such as pointing towards the earth, are not reachable. Some
        galactic coordinates for example will translate to unreachable
        directions at some times while OK directions at other times.
        """
        if (el > self._limits.get_max_el() or el < self._limits.get_min_el()):
            return False

        if (az > self._limits.get_max_az()):
            az -= 360.0
        if az < self._limits.get_min_az():
            return False
        return True

    def get_min_azerror_deg(self):
        return self._limits.get_min_az_error()

    def get_min_elerror_deg(self):
        return self._limits.get_min_el_error()

    def get_min_az(self):
        return self._limits.get_min_az()

    def get_min_el(self):
        return self._limits.get_min_el()

    def get_target(self):
        """
        Returns the target altitude and azimuth of the telescope as
        a tuple of decimal numbers [degrees].
        """
        return AzEl(self._limits.get_target_az(), self._limits.get_target_el())

    def get_current_el(self):
        return self._limits.get_current_el()

    def get_current_az(self):
        return (self._limits.get_current_az() + 360) % 360.0

    def get_current(self):
        """
        Returns the current altitude and azimuth of the telescope as
        a tuple of decimal numbers [degrees].
        Will return azimuth in interval 0-360
        """
        return AzEl(self.get_current_az(), self.get_current_el())

    def is_at_target(self):
        return not self._tcom.motors_running()

    def is_close_to_target(self):
        """
        Returns true if telescope is close enough to observe, else False.
        """
        dist = angular_dist_azel(self.get_current(), self.get_target())
        return abs(degrees(dist)) < self._tolerance

    def is_close_to_target_beam(self):
        """
        Returns true if telescope is close enough to observe, else False.
        """
        dist = abs(self.get_current() - self.get_target())
        # Must be slightly larger than 1 and slightly
        # less than 2 to account for rounding errors
        return (dist.get_azimuth() < 1.5*self._limits.get_min_az_error() and
                dist.get_elevation() < 1.5*self._limits.get_min_el_error())

    def set_target(self, target):
        t_az, t_el = self._find_closest(target.get_azimuth(), target.get_elevation(),
                                        self.get_current_az(), self.get_current_el())
        if self.can_reach(t_az, t_el):
            self._limits.set_target_az(t_az)
            self._limits.set_target_el(t_el)
        else:
            raise PositionUnreachable((
                'You requested the telescope to move to horizontal '
                'coordinates alt=%.2f, az=%.2f. Sorry, but this telescope '
                'cannot reach this position. In altitude the telescope '
                'cannot reach below %.2f or above %.2f degrees. '
                'In azimuth, the telescope cannot reach values between '
                '%.2f and %.2f degrees. If you are trying to reach a '
                'moving coordinate, such as the Sun or the galaxy, try '
                'later when your object have moved to an observable '
                'direction.') % (t_el, t_az,
                                 self._limits.get_min_el(),
                                 self._limits.get_max_el(),
                                 self._limits.get_max_az() % 360,
                                 self._limits.get_min_az() % 360))

    def _get_flip(self, az, el):
        return (az + 180) % 360, 180 - el

    def _find_closest(self, t_az, t_el, c_az, c_el):
        """
        Determine if the shortest azimuth distance is found by flipping
        (i.e. elevation >90 to <90 or <90 to >90) the telescope or not.
        """
        tf_az, tf_el = self._get_flip(t_az, t_el)
        if not self.can_reach(tf_az, tf_el):
            return (t_az, t_el)
        elif not self.can_reach(t_az, t_el):
            return (tf_az, tf_el)
        else:
            # movement is limited by the longest distance.
            longest_flip = max(self._get_azimuth_distance(c_az, tf_az),
                               self._get_elevation_distance(c_el, tf_el))
            longest = max(self._get_azimuth_distance(c_az, t_az),
                          self._get_elevation_distance(c_el, t_el))
            return (tf_az, tf_el) if longest_flip < longest else (t_az, t_el)

    def get_distance(self, pos_from, pos_to):
        c_az, c_el = self._find_closest(pos_from.get_azimuth(), pos_from.get_elevation(),
                                        pos_from.get_azimuth(), pos_from.get_elevation())
        t_az, t_el = self._find_closest(pos_to.get_azimuth(), pos_to.get_elevation(),
                                        c_az, c_el)
        return max(self._get_elevation_distance(c_el, t_el),
                   self._get_azimuth_distance(c_az, t_az))

    def _get_elevation_distance(self, el1, el2):
        return abs(el1 - el2)

    def _get_azimuth_distance(self, az1, az2):
        """
        This function calculates the distance needed to move in azimuth
        to between two angles. This takes into account that the
        telescope may need to go 'the other way around' to reach some
        positions, i.e. the distance to travel can be much larger than
        the simple angular distance. This assumes that both azimuth
        positions are valid, something which can be checked first with
        the can_reach function.
        """
        # CHECK AZIMUTH
        # This assumes that azimuth is always given in range 0 to 360,
        # something assured by the high-level system. But, here we need to
        # account for the fact that the telescope works in a range which
        # might be negative (for practical programming reasons).
        if (az1 > self._limits.get_max_az()):
            az1 -= 360.0
        elif (az1 < self._limits.get_min_az()):
            az1 += 360.0
        # Second position
        if (az2 > self._limits.get_max_az()):
            az2 -= 360.0
        elif (az2 < self._limits.get_min_az()):
            az2 += 360.0
        # Now return the distance needed to travel in degrees
        return abs(az1 - az2)

    def wait_for_movement(self, t_sleep=0.01):
        while self._tcom.motors_running():
            sleep(t_sleep)


# Exceptions for this class
class PositionUnreachable(RuntimeError):
    """
    Used for telescope errors.
    """
    pass
