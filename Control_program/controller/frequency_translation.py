from util import overrides
from copy import deepcopy


class Frequency:
    def __init__(self, freq_, band_="N/A"):
        self._freq = freq_
        self._band = band_

    def get_frequency(self):
        return self._freq

    def get_band(self):
        return self._band


class GNSSFrequencyTranslation:
    @staticmethod
    def create_with_typical_values(sky_frequency):
        raise NotImplementedError("Abstract Method")

    def get_frequency(self, f_band, satellite_name):
        raise NotImplementedError("Abstract Method")

    def get_system_acronyme(self):
        raise NotImplementedError("Abstract Method")


class FT_BySystem(GNSSFrequencyTranslation):
    def __init__(self, band_to_frequency):
        """
        band_to_frequency: dict
            maps frequency bands, such as L1, to corresponding
            frequency, 1575.42 MHz for L1.
        """
        self._band_to_freq = deepcopy(band_to_frequency)

    @overrides(GNSSFrequencyTranslation)
    def get_frequency(self, f_band, satellite_name):
        try:
            return Frequency(self._band_to_freq[f_band], f_band)
        except KeyError:
            raise ValueError("%s is not a valid frequency band for %s"
                             % (str(f_band), self.get_system_acronyme()))


class FT_BySatellite(GNSSFrequencyTranslation):
    def __init__(self, name_to_satellite):
        self._name_to_satellite = deepcopy(name_to_satellite)

    @overrides(GNSSFrequencyTranslation)
    def get_frequency(self, f_band, satellite_name):
        try:
            return Frequency(self._name_to_satellite[satellite_name][f_band], f_band)
        except KeyError:
            raise ValueError("%s is not a valid frequency band for %s"
                             % (str(f_band), satellite_name))


class GPS_FT(FT_BySystem):
    @staticmethod
    @overrides(FT_BySystem)
    def create_with_typical_values(sky_frequency):
        gps_band_to_freq = {
            "L0": sky_frequency,
            "L1": 1575.42e6,
            "L2": 1227.60e6,
            "L5": 1176.45e6
        }
        return GPS_FT(gps_band_to_freq)

    def __init__(self, band_to_frequency):
        FT_BySystem.__init__(self, band_to_frequency)

    @overrides(FT_BySystem)
    def get_system_acronyme(self):
        return "GPS"


class ASTRO_FT(FT_BySystem):
    @staticmethod
    @overrides(FT_BySystem)
    def create_with_typical_values(sky_frequency):
        gps_band_to_freq = {
            "A0": sky_frequency,
            "A1": 1550.0e6,
            "A2": 1200.0e6,
            "A5": 1150.0e6
        }
        return GPS_FT(gps_band_to_freq)

    def __init__(self, band_to_frequency):
        FT_BySystem.__init__(self, band_to_frequency)

    @overrides(FT_BySystem)
    def get_system_acronyme(self):
        return "ASTRO"


class GALILEO_FT(FT_BySystem):
    @staticmethod
    @overrides(FT_BySystem)
    def create_with_typical_values(sky_frequency):
        galileo_band_to_freq = {
            "E0": sky_frequency,
            "E1": 1575.42e6,
            "E5a": 1176.45e6,
            "E5b": 1207.14e6,
            "E6": 1278.75e6
        }
        return GALILEO_FT(galileo_band_to_freq)

    def __init__(self, band_to_frequency):
        FT_BySystem.__init__(self, band_to_frequency)

    @overrides(FT_BySystem)
    def get_system_acronyme(self):
        return "GALILEO"


class BEIDOU_FT(FT_BySystem):
    @staticmethod
    @overrides(FT_BySystem)
    def create_with_typical_values(sky_frequency):
        # https://en.wikipedia.org/wiki/BeiDou_Navigation_Satellite_System#Frequencies
        beidou_band_to_freq = {
            "E0": sky_frequency,
            "E2": 1561.098e6,
            "E5B": 1207.14e6,
            "E6": 1268.52e6
        }
        return BEIDOU_FT(beidou_band_to_freq)

    def __init__(self, band_to_frequency):
        FT_BySystem.__init__(self, band_to_frequency)

    @overrides(FT_BySystem)
    def get_system_acronyme(self):
        return "BEIDOU"


class GLONASS_FT(FT_BySatellite):
    @staticmethod
    @overrides(FT_BySatellite)
    def create_with_typical_values(sky_frequency):
        # https://glonass-iac.ru/en/GLONASS/index.php
        _name_to_fr_id = {
            "717": -7, "752": -7,

            "701": -5,
            "733": -4, "747": -4,
            "731": -3, "754": -3,
            "702": -2, "721": -2,
            "723": -1, "736": -1,
            "716": 0, "753": 0,
            "730": 1, "734": 1,
            "719": 2, "735": 2,
            "720": 3, "732": 3,
            "751": 4, "755": 4,
            "744": 5, "745": 5,
            "742": 6, "743": 6
        }
        # https://gssc.esa.int/navipedia/index.php/GLONASS_Signal_Plan
        glonass_name_to_satellite = dict()
        for k, v in _name_to_fr_id.items():
            glonass_name_to_satellite[k] = {
                "G0": sky_frequency,
                "G1": (lambda n: (1602 + n*0.5625)*1e6)(v),
                "G2": (lambda n: (1246 + n*0.4375)*1e6)(v),
                "G3": (lambda n: (1201 + n*0.4375)*1e6)(v)
            }
        return GLONASS_FT(glonass_name_to_satellite)

    def __init__(self, name_to_satellite):
        FT_BySatellite.__init__(self, name_to_satellite)

    @overrides(FT_BySatellite)
    def get_frequency(self, f_band, satellite_name):
        s = satellite_name
        if "(" in s and ")" in s:  # NORAD name
            s = s[s.find("(")+1:s.find(")")]
        s = ''.join([c for c in s if c.isdigit()])
        return FT_BySatellite.get_frequency(self, f_band, s)

    @overrides(FT_BySatellite)
    def get_system_acronyme(self):
        return "GLONASS"


class BandToFrequencyConverter:
    def __init__(self, system_to_band_, constel_to_ft):
        self._sys_freq = system_to_band_
        self._constel_to_ft = constel_to_ft

    def get_freq(self, constellation, band, sat_name):
        if constellation in self._constel_to_ft:
            return self._constel_to_ft[constellation].get_frequency(band, sat_name)
        raise KeyError("frequency bands for %s has not yet been implemented"
                       % constellation)

    def get_bands(self, constellation):
        return self._sys_freq[constellation]
