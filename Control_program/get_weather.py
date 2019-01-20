"""
TLEephem class to cope with data from TLE files

Columns:
 1  day                       day-number + fraction of day
 2  exmem->m25.temp,	         Vaisala25 outdoor temp
 3  exmem->m25.humid,	 Vaisala25 humidity
 4  exmem->m25.press,	 Vaisala25 pressure
 5  exmem->m25.wspeed,	 Vaisala25 Wind speed
 6  exmem->m25.wdir,	         Vaisala25 Wind direction
 7  exmem->m25.itemp,	 Vaisala25 internal temp
 8  exmem->m25.supply,	 Vaisala25 supply voltage
 9  exmem->m25.wtemp,	 water temp
10  exmem->m25.gustwspeed,    Vaisala25 Gusts wind speed
11  exmem->m25.gustwdir,	 Vaisala25 Old mechanical wind sensor
                                 (formerly used for gust wind direction)
12  exmem->m25.rainrate,      rain rate
13  exmem->m25.rainsample,    rain sample
14  exmem->m25.rain_24h,      rain amount last 24h
15  exmem->m25.rain_1h,	 rain amount last 1h
16  exmem->m25.timestamp,     Unix time for update
17  exmem->m20.temp,	         Vaisala20 outdoor temp
18  exmem->m20.humid,	 Vaisala20 humidity
19  exmem->m20.press,	 Vaisala20 pressure
20  exmem->m20.timestamp,     Unix time for update
21  exmem->vane.vane_setting  Vane setting
22  exmem->vane.pressure1     Differential pressure1
23  exmem->vane.pressure2     Differential pressure2
24  exmem->vane.timestamp     Unix time for update
"""
from datetime import datetime
from re import sub
from numpy import degrees
from ephem import readtle
from urllib2 import urlopen

from collections import OrderedDict
from controller.util import AzEl


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


class wx_oso_weather:
    def __init__(self):
        pass

    @staticmethod
    def download_weather_data(url_):
        with TLEURL(url_) as url:
            return url.read()


if __name__ == "__main__":
    tt = datetime.utcnow().timetuple()
    # http://wx.oso.chalmers.se/data/weater/<year>/weather_<year>_<day_no>.log
    url_txt = "http://wx.oso.chalmers.se/data/weather/%d/weather_%d_%d.log" % (tt.tm_year, tt.tm_year, tt.tm_yday)
    print url_txt
    print wx_oso_weather.download_weather_data(url_txt)
