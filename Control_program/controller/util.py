from os import path, makedirs
from re import sub
from threading import Thread
from time import sleep
from datetime import datetime
from ephem import degrees as ephem_deg
from numpy import degrees

from numpy import sin, cos, clip, dot, pi, arccos, radians

from controller.pyprogbar.progressbar import (create_progressbar,
                                              destroy_progressbar,
                                              draw_progressbar)


def overrides(interface_class):
    """
    function decorator that checks if
    overridden method exists in parent class.
    """
    def overrider(method):
        """
        returns method if it exists in parent
        """
        assert(method.__name__ in dir(interface_class))
        return method
    return overrider


def project_path():
    return path.dirname(path.dirname(path.abspath(__file__)))


def project_file_path(project_rel_path):
    return project_path() + project_rel_path


def ephdeg_to_deg(eph_deg):
    return degrees(float(ephem_deg(str(eph_deg))))


def stoc(phi, theta):
    return (sin(theta)*cos(phi),
            sin(theta)*sin(phi),
            cos(theta))


def spherical_dot(phi0, theta0, phi1, theta1):
    # clip to compensate for floating point errors
    # in case (phi0 is phi1 and theta0 is theta1)
    return clip(dot(stoc(phi0, theta0), stoc(phi1, theta1)), -1, 1)


def az_el_to_spherical(az, el):
    return (pi/2 - az, pi/2 - el)


def angular_dist(az0, el0, az1, el1):
    phi0, theta0 = az_el_to_spherical(az0, el0)
    phi1, theta1 = az_el_to_spherical(az1, el1)
    return arccos(spherical_dot(phi0, theta0, phi1, theta1))


def angular_dist_azel(azel0, azel1):
    return angular_dist(radians(azel0.get_azimuth()),
                        radians(azel0.get_elevation()),
                        radians(azel1.get_azimuth()),
                        radians(azel1.get_elevation()))


def az_el_to_cart(az, el):
    r = -(pi/2 - abs(el)) / (pi/2)
    return (r * cos(az-pi/2),
            r * sin(az-pi/2))


class AzEl:
    @staticmethod
    def from_tuple(az_el_tuple):
        return AzEl(float(az_el_tuple[0]), float(az_el_tuple[1]))

    @staticmethod
    def create_with_offset(pos, az_offset, el_offset, correct_az_for_el=True):
        if correct_az_for_el:
            az_offset /= cos(radians(pos.get_elevation() + el_offset))
        return pos + AzEl(az_offset, el_offset)

    def __init__(self, azimuth=0.0, elevation=0.0,
                 az_offset=0.0, el_offset=0.0, correct_az_for_el=True):
        self._az, self._el = 0.0, 0.0
        # set_elevation may change azimuth value
        self.set_azimuth(float(azimuth))
        self.set_elevation(float(elevation))

    def __eq__(self, other):
        return (abs(self._az - other._az) < 1e-10 and
                abs(self._el - other._el) < 1e-10)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __add__(self, other):
        return AzEl(self._az + other._az,
                    self._el + other._el)

    def __sub__(self, other):
        return AzEl(self._az - other._az,
                    self._el - other._el)

    def __iadd__(self, other):
        self.set_azimuth(self._az + other._az)
        self.set_elevation(self._el + other._el)
        return self

    def __isub__(self, other):
        self.set_azimuth(self._az - other._az)
        self.set_elevation(self._el - other._el)
        return self

    def __abs__(self):
        return AzEl(360 - self._az if self._az > 180 else self._az,
                    -self._el if self._el < 0 else self._el)

    def __str__(self):
        return "(Az=%.2f, El=%.2f)" % (float(self._az),
                                       float(self._el))

    def __repr__(self):
        return "AzEl(%.3f, %.3f)" % (float(self._az),
                                     float(self._el))

    def get_azimuth(self):
        return self._az

    def get_elevation(self):
        return self._el

    def set_azimuth(self, azimuth):
        self._az = azimuth % 360
        if self._az < 0:
            self._az += 360

    def set_elevation(self, elevation):
        if elevation > 360:
            elevation %= 360
            if elevation > 180:
                elevation -= 360
        elif elevation < -360:
            elevation %= -360
            if elevation < -180:
                elevation += 360
        if elevation < -90:
            self.set_azimuth(self._az - 180)
            self._el = -90 - elevation % -90
        elif elevation > 90:
            self.set_azimuth(self._az + 180)
            self._el = 90 - elevation % 90
        else:
            self._el = elevation


class progressbar:
    def __init__(self, cfg_):
        self._cfg = cfg_
        self._f_percent_done = list()
        self._f_message = list()
        self._running = False
        self._thread = None

    def get_config(self):
        return self._cfg

    def add_row(self, f_percent_done_, f_message_):
        self._f_percent_done.append(f_percent_done_)
        self._f_message.append(f_message_)

    def update_row(self, row_, f_percent_done_, f_message_):
        self._f_percent_done[row_] = f_percent_done_
        self._f_message[row_] = f_message_

    def start(self):
        create_progressbar(self._cfg)
        self._thread = Thread(target=self._run)
        self._running = True
        self._thread.start()

    def stop(self):
        self._running = False
        self._thread.join()
        self._thread = None
        destroy_progressbar()

    def _run(self):
        while self._running:
            for i, (msg, prc) in enumerate(zip(self._f_message,
                                               self._f_percent_done)):
                draw_progressbar(i, msg(), prc())
                if not self._running:
                    break
                sleep(0.01)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()
        return False


def time_tuple_to_yyyymmdd(t):
    return "%04d-%02d-%02d" % (t.tm_year, t.tm_mon, t.tm_mday)


def time_tuple_to_hhmmss(t):
    return "%02d:%02d:%02d" % (t.tm_hour, t.tm_min, t.tm_sec)


class TelescopeOutput:
    def append_output(self, out):
        raise NotImplementedError("Abstract Method")


class TelescopeFileOutput(TelescopeOutput):
    def __init__(self, output_dir):
        if not path.exists(output_dir):
            makedirs(output_dir)
        self.m_dir = output_dir

    def _get_header(self):
        return "\n".join([
            "# File header. Lines beginning with # should be ignored.",
            "# ",
            "# Columns:",
            "# time: yyyy:yday:dsec, e.g. 2018:032:7200 is Feb 2 2018 at 2 AM",
            "# name: name of the observed satellite",
            "# frequency: center frequency (in MHz) of the observation",
            "# azimuth: azimuth (in degrees) of the observed satellite",
            "# elevation: elevation (in degrees) of the observed satellite",
            "# power: received power (in watt).",
            "# az-offset: azimuth offset (in degrees) of the observed satellite",
            "# el-offset: elevation offset (in degrees) of the observed satellite",
            "# diode: whether or not the noise diode is turned on.",
            "# ",
            "# %12s\t%30s\t% 10s\t% 9s\t% 9s\t% 13s\t% 9s\t% 9s\t% 5s" % (
                "Time", "NORAD Name", "Freq", "Azimuth", "Elevation", "Power",
                "Az-Offset", "El-Offset", "Diode"),
            "# %s" % (147*"-")])

    def create_new_measurement_series(self):
        time_tuple = datetime.now().timetuple()
        output_file = ("%s/%04d%03d%05d.txt"
                       % (self.m_dir,
                          time_tuple.tm_year,
                          time_tuple.tm_yday,
                          3600*time_tuple.tm_hour + 60*time_tuple.tm_min + time_tuple.tm_sec))
        with open(output_file, 'w') as f:
            f.write(self._get_header() + "\n")
        return MeasurementSeriesOutput(self.m_dir, output_file)


class MeasurementSeriesOutput:
    def __init__(self, output_dir_, output_file_):
        self._output_dir = output_dir_
        self.m_output_file = output_file_

    def append_output(self, t_start, name, f_center, azimuth,
                      elevation, temp_obs_uncal,
                      az_offset, el_offset, diode_on_):
        with open(self.m_output_file, "a") as f:
            f.write("%04d:%03d:%05d\t% 30s\t%010.4f\t%09.5f\t%09.5f\t% 13s"
                    "\t%09.5f\t%09.5f\t%d\n"
                    % (t_start.tm_year, t_start.tm_yday,
                       3600*t_start.tm_hour + 60*t_start.tm_min + t_start.tm_sec,
                       name, f_center, azimuth, elevation, "%e" % temp_obs_uncal,
                       az_offset, el_offset, 1 if diode_on_ else 0))

    def save_spectrum_txt(self, t_start, name, spectrum):
        spectrum.save_to_txt_freq("%s/%s_%s_%s_%s.txt"
                                  % (self._output_dir,
                                     sub("\\s+", "_", name),
                                     "%.2f_MHz" % (spectrum.get_observation_freq()*1e-6),
                                     time_tuple_to_yyyymmdd(t_start),
                                     time_tuple_to_hhmmss(t_start)),
                                  spectrum.get_observation_freq())
