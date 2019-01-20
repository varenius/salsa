from re import sub
from ephem import (now, Sun, Equatorial, hours, degrees as ephem_deg,
                   J2000, FixedBody, Moon)
from numpy import radians, sqrt, arctan2, pi, degrees
from controller.util import az_el_to_cart, AzEl, overrides

from controller.satellites.satellite import CelestialObject
from controller.satellites.posmodel import PositionModel


class AbstractSatelliteComputer:
    _valid_constellations = ["GPS", "COSMOS", "GSAT", "BEIDOU", "ASTRO"]

    def load_satellites(self, constellation, el_cutoff=-100.0):
        raise NotImplementedError("Abstract Method")

    def load_satellite(self, name_):
        raise NotImplementedError("Abstract Method")

    @staticmethod
    def _norad_from_abbrev(abrv_name):
        raise NotImplementedError("Abstract Method")

    @staticmethod
    def _find_abbrev_in_name(norad_name):
        abrv_name = norad_name[norad_name.find("(")+1:norad_name.find(")")]
        if "(" not in norad_name or ")" not in norad_name:
            # satellite name not on the form "NORAD_NAME (ABBREV_NAME)"
            abrv_name = norad_name[norad_name.find(" ")+1:]
        return sub("\\s*", "", abrv_name)

    @staticmethod
    def _is_norad_name(name_):
        for cnst in AbstractSatelliteComputer._valid_constellations:
            if cnst in name_:
                return True
        # in case we have not updated their list of valid systems
        # use default method for determining norad name.
        return "(" in name_ and ")" in name_


class SatPosComp(AbstractSatelliteComputer):
    _all_satellites_ = dict()

    def __init__(self, tleEphem):
        self._tleEphem = tleEphem
        SatPosComp._all_satellites_.update(self.load_satellites("all"))

    def SatCompute(self, constellation, el_cutoff):
        """
        Provides a list of available satellites and their position over
        the local horizon in polar coordinates.

        Parameters
        ----------
        constellation : str
            'ALL'    - all constellations
            'GPS'    - GPS satellites only
            'GSAT'   - GALILEO satellites only
            'COSMOS' - GLONASS satellites only
            'BEIDOU' - BEIDOU satellites only
        el_cutoff : float
            minimum allowed elevation

        Returns
        -------
        out : tuple
            A tuple containing
                name - list of satellites' names
                phi  - list of polar coordinates: angle
                r    - list of polar coordinates: distance
        """
        tle_sat = self._tleEphem.ComputeAzEl(constellation, el_cutoff)
        name = list()
        r = list()
        phi = list()
        for sat in tle_sat:
            x, y = az_el_to_cart(radians(sat.get_azimuth()),
                                 radians(sat.get_elevation()))
            name.append(sat.get_name())
            r.append(sqrt(x**2 + y**2) * 90)
            phi.append(arctan2(y, x) - pi/2)
        return name, phi, r

    @overrides(AbstractSatelliteComputer)
    def load_satellites(self, constellation, el_cutoff=-100.0):
        tle_sat = self._tleEphem.ComputeAzEl(constellation, el_cutoff)
        out = dict()
        for sat in tle_sat:
            n = sat.get_name()
            out[n] = CelestialObject(n, constellation,
                                     PositionModel(lambda name_=n: self.SatComputeAzElSingle(name_).get_position()))
        return out

    def SatComputeAzElSingle(self, satName):
        """
        Computes Azimuth and Elevation angles for a given satellite
        Args:
            satName - name of the requested satellite
        Returns:
            Azimuth   - in degrees
            Elevation - in degrees
        """
        return self._tleEphem.ComputeAzElSingle(satName)

    @overrides(AbstractSatelliteComputer)
    def load_satellite(self, name_):
        gnss_name = name_
        if not self._is_norad_name(name_):
            gnss_name = self._norad_from_abbrev(name_)
        f_pos = lambda: self.SatComputeAzElSingle(gnss_name).get_position()
        for cnst in self._valid_constellations:
            if cnst in gnss_name:
                return CelestialObject(gnss_name, cnst, PositionModel(f_pos))
        return CelestialObject(gnss_name, None, PositionModel(f_pos))

    @staticmethod
    @overrides(AbstractSatelliteComputer)
    def _norad_from_abbrev(abrv_name):
        if not abrv_name or not abrv_name.strip():
            raise NameError("%s is not a valid abbreviated "
                            "satellite name" % abrv_name)
        an = sub("\\s*", "", abrv_name)
        for sat_name in SatPosComp._all_satellites_.keys():
            if an in SatPosComp._find_abbrev_in_name(sat_name):
                return sat_name
        raise NameError("%s is not a valid abbreviated satellite name" % abrv_name)


class ManualComp(AbstractSatelliteComputer):
    def __init__(self, positions_):
        self._positions = dict()
        for p in positions_:
            n = p.strip()
            if n.startswith("(") and n.endswith(")"):
                self._positions[p] = AzEl.from_tuple(n[1:-1].split(","))

    @overrides(AbstractSatelliteComputer)
    def load_satellites(self, constellation, el_cutoff=-100.0):
        if constellation.lower() != "manual":
            return dict()
        return {name: self.load_satellite(name) for name in self._positions.keys()}

    @overrides(AbstractSatelliteComputer)
    def load_satellite(self, name_):
        try:
            
            return CelestialObject("MANUAL %s" % name_, "MANUAL", PositionModel(lambda: self._positions[name_]))
        except KeyError:
            return CelestialObject("MANUAL %s" % name_, None, PositionModel(lambda: AzEl()))


class CelObjComp(AbstractSatelliteComputer):
    _astro = {
        "Sun": lambda obs: CelObjComp._create("Sun", lambda: CelObjComp._update_sun_pos(obs)),
        "CasA": lambda obs: CelObjComp._create("CasA", lambda: CelObjComp._update_casa_pos(obs)),
        "Moon": lambda obs: CelObjComp._create("Moon", lambda: CelObjComp._update_moon_pos(obs))
    }
    _abbrev_to_norad = {
        "Sun": "ASTRO Sun (Sun)",
        "CasA": "ASTRO Cas. A (CasA)",
        "Moon": "ASTRO Moon (Moon)"
    }

    @staticmethod
    def _create(abbrev_name, f_update_pos):
        return CelestialObject(CelObjComp._norad_from_abbrev(abbrev_name),
                               "ASTRO", PositionModel(f_update_pos))

    @staticmethod
    def create(norad_name, f_update_pos):
        return CelestialObject(norad_name,
                               "ASTRO", PositionModel(f_update_pos))

    def __init__(self, observer_):
        self._observer = observer_

    @overrides(AbstractSatelliteComputer)
    def load_satellites(self, constellation, el_cutoff=-100.0):
        if constellation.lower() != "astro":
            return dict()
        sat_names = [name for name in CelObjComp._abbrev_to_norad.keys()]
        return {name: self.load_satellite(name) for name in sat_names}

    @overrides(AbstractSatelliteComputer)
    def load_satellite(self, name_):
        abbrev_name = name_
        if self._is_norad_name(name_):
            abbrev_name = self._find_abbrev_in_name(name_)
        try:
            return CelObjComp._astro[abbrev_name](self._observer)
        except KeyError:
            return CelestialObject(self._norad_from_abbrev(abbrev_name),
                                   None, PositionModel(lambda: AzEl()))

    @staticmethod
    def refresh_observer_time(observer_):
        observer_.date = now()
        return observer_

    @staticmethod
    def astro_compute(astro_obj, observer_):
        # Calculate alt, az, via fixedbody since only fixed body has
        # alt, az. First needs to make sure we have equatorial coordinates
        eq = Equatorial(astro_obj)
        fb = FixedBody()
        fb._ra, fb._dec, fb._epoch = eq.ra, eq.dec, eq.epoch
        fb.compute(observer_)
        return AzEl(degrees(float(fb.az)), degrees(float(fb.alt)))

    @staticmethod
    def _update_sun_pos(observer_):
        CelObjComp.refresh_observer_time(observer_)
        pos = Sun()
        pos.compute(observer_)  # Needed sun since time-dependant
        return CelObjComp.astro_compute(pos, observer_)

    @staticmethod
    def _update_casa_pos(observer_):
        CelObjComp.refresh_observer_time(observer_)
        pos = Equatorial(hours('23:23:26'), ephem_deg('58:48:0'), epoch=J2000)
        return CelObjComp.astro_compute(pos, observer_)

    @staticmethod
    def _update_moon_pos(observer_):
        CelObjComp.refresh_observer_time(observer_)
        pos = Moon()
        pos.compute(observer_)  # Needed moon since time-dependant
        return CelObjComp.astro_compute(pos, observer_)

    @staticmethod
    def _norad_from_abbrev(abrv_name):
        try:
            return CelObjComp._abbrev_to_norad[abrv_name]
        except KeyError:
            raise NameError("%s is not a valid abbreviated satellite name"
                            % abrv_name)
