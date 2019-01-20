"""
TLEephem class to cope with data from TLE files
"""
from datetime import datetime
from re import sub
from numpy import degrees
from ephem import readtle
from urllib2 import urlopen

from collections import OrderedDict
from controller.util import AzEl


class TLESatellite:
    def __init__(self, TLEname, TLEaz, TLEel):
        self._name = TLEname
        self._az = TLEaz
        self._el = TLEel

    def get_name(self):
        return self._name

    def get_azimuth(self):
        return self._az

    def get_elevation(self):
        return self._el

    def get_position(self):
        return AzEl(self._az, self._el)


class TLEEntry:
    def __init__(self, name_, line1_, line2_):
        self.name = name_
        self.line1 = line1_
        self.line2 = line2_


class TLEURL:
    def __init__(self, link_):
        self._link = link_
        self._url = None

    def __enter__(self):
        self._url = urlopen(self._link)
        return self._url

    def __exit__(self, exc_type, exc_value, traceback):
        self._url.close()
        return False


class TLEephem:
    def __init__(self, tle_files, observer_):
        self.tle_files = tle_files
        self._observer = observer_

    @staticmethod
    def download_tle(output_dir, links):
        """
        Downloads files from links ant puts them in output_dir.
        Files downloaded from the urls mapped to corresponding
        file names will be named according to those names.

        Parameters
        ----------
        output_dir : str
            Output directory for the downloaded files.
        links : map
            URLs mapped to corresponding output file names (not
            including extension).
        """
        for c, link in links.items():
            with open("%s/%s.tle" % (output_dir, c), "w") as f, TLEURL(link) as url:
                f.write(url.read())

    def reload_tle(self):
        """
        Reloads the data from the TLE files.

        Returns
        -------
        out : dict
            A dictionary of TLEEntry objects mapped to their
            corresponding satelite names.
        """
        data = list()
        for ftle in self.tle_files:
            with open(ftle, 'r') as f:
                data.extend([sub("\\s*\r*\n+", "", l) for l in f.readlines()])
        out = OrderedDict()
        for n, l1, l2 in zip(data[0::3], data[1::3], data[2::3]):
            out[n] = TLEEntry(n, l1, l2)
        return out

    def ComputeAzEl(self, constellation, el_cutoff, date_=None):
        """
        Computes azimuth and elevation angles for a defined
        group of GNSS satellites.

        Parameters
        ----------
        constellation : str
            'GPS', 'GLONASS', 'GALILEO', 'BEIDOU' or 'ALL'
        el_cutoff : float
            minimum allowed elevation in degrees.
            values range from -90 to 90.

        Returns
        -------
        out : list
            list of TLESatellite objects
        """
        constellation = constellation.upper()
        self._observer.date = date_ if date_ is not None else datetime.utcnow()
        SatAzEl = list()
        for tle in self.reload_tle().values():
            if (constellation == "ALL" or constellation in tle.name):
                sat = readtle(tle.name, tle.line1, tle.line2)
                sat.compute(self._observer)
                tle_sat = TLESatellite(tle.name, degrees(sat.az), degrees(sat.alt))
                if tle_sat.get_elevation() >= el_cutoff:
                    SatAzEl.append(tle_sat)
        return SatAzEl

    def ComputeAzElSingle(self, satName, date_=None):
        """
        Returns Azimuth and Elevation angles in decimal degrees
        for a given satName.

        Parameters
        ----------
        satName : str
            name of the satellite

        Returns
        -------
        out : tuple
            az, el - in decimal degrees
        """
        self._observer.date = date_ if date_ is not None else datetime.utcnow()
        tle = self.reload_tle()[satName]
        sat = readtle(tle.name, tle.line1, tle.line2)
        sat.compute(self._observer)
        return TLESatellite(tle.name, degrees(sat.az), degrees(sat.alt))
