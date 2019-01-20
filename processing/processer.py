import argparse
import re
from datetime import datetime
from calendar import timegm
import matplotlib.pyplot as plt
import numpy as np
from numpy import max, min
from scipy.interpolate import interp1d


plot_markers = ['.', 'x', '*', 'o', '+', 'd', 's', 'v', '^', '<', '>',
                '1', '2', '3', '4', '8', 'h', 'p', 'H', 'D',
                '|', ',', '_']
plot_band_marker_colors = ['blue', 'red', 'green', 'yellow',
                           'magenta', 'cyan', 'black']


def dt_to_dec(dt):
    year_start = datetime(dt.year, 1, 1)
    year_end = year_start.replace(year=dt.year+1)

    ysec = (dt - year_start).total_seconds()  # seconds so far
    ysec_tot = (year_end - year_start).total_seconds()  # seconds in year
    return dt.year + ysec/ysec_tot


def CalculateFluxCasA(year, freq):
    if (freq < 300e6 or freq > 31e9):
        raise Exception("Only valid for 300e6<freq [GHz]<31e9")
    if isinstance(year, datetime):
        year = dt_to_dec(year)
    rate = (0.97 - 0.3*np.log10(freq*1e-9))/100  # decrease of flux in % per year; freq in GHz
    x = np.log10(freq*1e-6)  # freq in MHz!
    val = 5.745 - 0.77*x
    return np.power(10, val) - np.power(10, val)*(year-1980.0)*rate


def todb(v):
    if v > 0:
        return 10 * np.log10(v)
    #raise Exception("attempted to convert a NaN value")
    return 10 * np.log10(abs(v))


def fromdb(v):
    return np.power(10, (v/10.0))


def _marker(i):
    return plot_markers[i % len(plot_markers)]


def marker_color(i):
    return plot_band_marker_colors[i % len(plot_band_marker_colors)]


def dsec_to_hhmmss(sday):
    sday = int(sday)
    shour = int(sday % (60*60))
    return int(sday / (60*60)), int(shour / 60), int(shour % 60)


def y_yday_dsec_to_date(y, yday, dsec):
    (h, m, s) = dsec_to_hhmmss(int(dsec))
    return datetime.strptime("%d/%d %d:%d:%d" % (int(y), int(yday), h, m, s),
                             "%Y/%j %H:%M:%S")


class MeasurementResult:
    def __init__(self, frequency_, time_, az_, el_, power_, diode_on_, offset_):
        self.freq = frequency_
        self.time = time_
        self.az = az_
        self.el = el_
        self.power = power_
        self.diode_on = diode_on_
        self.offset = offset_


class MeasurementSeries:
    def __init__(self, frequency):
        self._freq = frequency
        self._time = list()
        self._az = list()
        self._el = list()
        self._power = list()
        self._diode_on = list()
        self._offset = list()

    def add_entry(self, result):
        self._time.append(result.time)
        self._az.append(result.az)
        self._el.append(result.el)
        self._power.append(result.power)
        self._diode_on.append(result.diode_on)
        self._offset.append(result.offset)

    def frequency(self):
        return self._freq

    def azimuth(self):
        return self._az

    def elevation(self):
        return self._el

    def time(self):
        return self._time

    def power(self):
        return self._power

    def diode(self):
        return self._diode_on

    def offset(self):
        return self._offset

    def _filter(self, data, cond):
        try:
            return [d for d, c in zip(data, cond) if c]
        except TypeError:
            return data

    def filter_diode(self, data, diode_on):
        cond = bool(diode_on)
        return self._filter(data, [cond == bool(c) for c in self._diode_on])

    def filter_offset(self, data, include_offset):
        cond = bool(include_offset)
        return self._filter(data, [cond == bool(c) for c in self._offset])

    def compute_errbar(self, data):
        return np.average(data), np.std(data)

    @staticmethod
    def get_sorted(sort_key, sort_val):
        return zip(*sorted([(k, v) for k, v in zip(sort_key, sort_val)],
                           key=lambda e: e[0]))

    def __getitem__(self, key):
        return {"frequency": self.frequency,
                "azimuth": self.azimuth,
                "elevation": self.elevation,
                "time": self.time,
                "power": self.power,
                "diode": self.diode,
                "offset": self.offset}[key]()


class SatelliteData:
    def __init__(self, name_):
        self._name = name_
        self._frequency_data = dict()

    def add_entry(self, result):
        if result.freq not in self._frequency_data:
            self._frequency_data[result.freq] = MeasurementSeries(result.freq)
        self._frequency_data[result.freq].add_entry(result)

    def compute_errbar(self, h_item, v_item, diode):
        horz = list()
        vert = list()
        for s in self._frequency_data.values():
            x = s.filter_diode(s[h_item], diode)
            y = [todb(i) for i in s.filter_diode(s[v_item], diode)]
            horz.append((np.average(x), np.std(x)))
            vert.append((np.average(y), np.std(y)))
        return zip(*horz), zip(*vert)

    def compute_errbar_diode_delta(self, h_item, v_item):
        horz = list()
        vert = list()
        for s in self._frequency_data.values():
            x_o = s.filter_diode(s[h_item], True)
            x_f = s.filter_diode(s[h_item], False)
            try:
                x = [(o+f)/2 for o, f in zip(x_o, x_f)]
            except TypeError:
                x = (x_o+x_f)/2
            y = [todb(o-f) for o, f in zip(s.filter_diode(s[v_item], True), s.filter_diode(s[v_item], False))]
            horz.append((np.average(x), np.std(x)))
            vert.append((np.average(y), np.std(y)))
        return zip(*horz), zip(*vert)

    @staticmethod
    def get_sorted(sort_key, sort_val):
        return MeasurementSeries.get_sorted(sort_key, sort_val)

    def __iter__(self):
        return self._frequency_data.values().__iter__()


def load_data(fname):
    def get_lines(data_): return re.split("\\r?\\n", data_)

    def skip_line(line_): return not line_ or line_.startswith("#")

    with open(fname, "r") as f:
        return [line for line in get_lines(f.read()) if not skip_line(line)]


def load_file(fname):
    ddict = dict()
    for line in load_data(fname):
        cols = [t.strip() for t in line.split("\t")]
        t_, n_ = cols[0], cols[1]
        if n_ not in ddict:  # name
            ddict[n_] = SatelliteData(n_)
        d_ = y_yday_dsec_to_date(*t_.split(":"))
        if len(cols) == 6:      # v1 (time,name,freq,az,el,pwr)
            (_, name, freq, az, el, pwr) = cols
            res = MeasurementResult(float(freq), d_, float(az), float(el),
                                    float(pwr), False, False)
            ddict[n_].add_entry(res)
        elif len(cols) == 9:    # v2 (time,name,freq,az,el,pwr,diode,offset)
            (_, name, freq, az, el, pwr, az_offset_, el_offset_, diode_) = cols
            try:
                res = MeasurementResult(float(freq), d_, float(az), float(el),
                                        float(pwr), bool(int(diode_)),
                                        float(az_offset_) or float(el_offset_))
                ddict[n_].add_entry(res)
            except Exception:
                pass
    return ddict


def time_diff_s(date0, date1):
    return abs(timegm(date1.timetuple()) - timegm(date0.timetuple()))

__Colors=['blue','green','red','cyan','magenta','yellow','black']
def plot_on_axis(ax, data_dict_items, show_diode, h_data="elevation", v_data="power"):
    i_mrk = 0
    for sat_name, freqs in data_dict_items:
        #if ("PRN 10" not in sat_name and "PRN 26" not in sat_name and "PRN 27" not in sat_name and "PRN 30" not in sat_name): continue
        #if ("PRN 10" in sat_name or "PRN 15" in sat_name or "PRN 20" in sat_name or "PRN 24" in sat_name or "PRN 28" in sat_name): continue
        marker = _marker(i_mrk)
        for i, series in enumerate(freqs):
            print("%s: max(pwr)-min(pwr)=%f"
                  % (sat_name, todb(max(series.power())) - todb(min(series.power()))))
            abbrv_name = sat_name[sat_name.find("(")+1:sat_name.find(")")]
            x = series.filter_diode(series[h_data], False)
            y = [todb(j) for j in series.filter_diode(series[v_data], False)]
            #y_max = max(y); y = [todb(j/y_max) for j in y]
            """
            X, Y = list(), list()
            a, b = list(), list()
            for a0, a1, b0, b1 in zip(x[:-1], x[1:], y[:-1], y[1:]):
                if time_diff_s(a0, a1) < 3600:
                    a.append(a0)
                    b.append(b0)
                else:
                    X.append(a)
                    a = list()
                    Y.append(b)
                    b = list()
            if a and b:
                X.append(a)
                Y.append(b)
            for x, y in zip(X, Y):
            """
            ax.plot(x, y, color=__Colors[i_mrk % len(__Colors)],
                    marker=marker, markersize=2, linewidth=0.5, markeredgecolor=marker_color(i),
                    label="%s @ %.2f MHz (diode %s)" % (abbrv_name, series.frequency(), "OFF"))
            if show_diode:
                ax.plot(series.filter_diode(series[h_data], True),
                        series.filter_diode(series[v_data], True),
                        marker=marker, markersize=2, linewidth=0.5, markeredgecolor=marker_color(i),
                        label="%s @ %.2f MHz (diode %s)" % (abbrv_name, series.frequency(), "ON"))
        i_mrk += 1


def dt_to_ut(dt):
    try:
        return [timegm(t.timetuple()) for t in dt]
    except TypeError:
        return timegm(dt.timetuple())


def dt_avg(dt):
    return datetime.utcfromtimestamp(int(np.average(dt_to_ut(dt))))


def ut_avg(ut):
    return datetime.utcfromtimestamp(int(np.average(ut)))


def func(series, h_data, v_data, asd=True):
    _, s_data = series.get_sorted(series["time"], zip(series[h_data],
                                                      series[v_data],
                                                      series["offset"],
                                                      series["diode"]))
    lx, ly, o_last = list(), list(), s_data[0][2]
    x_out, y_out, yerr_out, o_out = list(), list(), list(), list()
    for x, y, o, d in s_data:
        if o == o_last:
            if not d:
                lx.append(x)
                ly.append(y if asd else y)
        else:
            x_out.append(dt_avg(lx))
            y_out.append(np.average(ly))
            yerr_out.append(np.std(ly))
            o_out.append(o_last)
            lx, ly, o_last = list(), list(), o
    x_out.append(dt_avg(lx))
    y_out.append(np.average(ly))
    yerr_out.append(np.std(ly))
    o_out.append(o_last)
    return x_out, y_out, yerr_out, o_out


def func_casa(series, h_data, v_data):
    x_out, y_out, yerr_out, o_out = func(series, h_data, v_data, False)

    _x1, _y1, _yerr1 = list(), list(), list()
    for i_on, i_off, j_on, j_off, jerr_on, jerr_off in zip(x_out[1::2], x_out[:-1:2], y_out[1::2], y_out[:-1:2], yerr_out[1::2], yerr_out[:-1:2]):
        _x1.append(dt_avg([i_on, i_off]))
        _y1.append(np.average(j_on - j_off))
        _yerr1.append(np.linalg.norm([jerr_on, jerr_off]))
    _x2, _y2, _yerr2 = list(), list(), list()
    for i_on, i_off, j_on, j_off, jerr_on, jerr_off in zip(x_out[1:-1:2], x_out[2:-1:2], y_out[1:-1:2], y_out[2:-1:2], yerr_out[1:-1:2], yerr_out[2:-1:2]):
        _x2.append(dt_avg([i_on, i_off]))
        _y2.append(np.average(j_on - j_off))
        _yerr2.append(np.linalg.norm([jerr_on, jerr_off]))
    _x, _y, _yerr = [_x1[0]], [_y1[0]], [_yerr1[0]]
    for (a, b, c, d, e, f) in zip(_x2, _x1[1:], _y2, _y1[1:], _yerr2, _yerr1[1:]):
        _x.append(a)
        _x.append(b)
        _y.append(c)
        _y.append(d)
        _yerr.append(e)
        _yerr.append(f)
    return _x, _y, _yerr


def gen_spline_from_datetime(x, y, spline_kind):
    x_int = [int(timegm(t.timetuple())) for t in x]
    f = interp1d(x_int, y, kind=spline_kind)
    x_gen = np.linspace(min(x_int), max(x_int), 10*len(x_int) + 1)
    return [datetime.utcfromtimestamp(tstamp) for tstamp in x_gen], f(x_gen)


def plot_beam_switch(ax, data_dict_items, show_diode, h_data="elevation", v_data="power"):
    spline_kind = "cubic"
    i_mrk = 0
    azs = list()
    els = list()
    for sat_name, freqs in data_dict_items:
        marker = _marker(i_mrk)
        for i, series in enumerate(freqs):
            azs.extend(series.azimuth())
            els.extend(series.elevation())
            abbrv_name = sat_name[sat_name.find("(")+1:sat_name.find(")")]
            x_onoff, y_onoff, yerr_onoff, offset = func(series, h_data, v_data)
            x_off, y_off, yerr_off = zip(*((a, b, c) for a, b, c, d in zip(x_onoff, y_onoff, yerr_onoff, offset) if d))
            x_on, y_on, yerr_on = zip(*((a, b, c) for a, b, c, d in zip(x_onoff, y_onoff, yerr_onoff, offset) if not d))
            # create spline
            """
            x_off_spline, y_off_spline = gen_spline_from_datetime(x_off, y_off, spline_kind)
            ax.plot(x_off_spline, y_off_spline, linewidth=1, color=marker_color(i_mrk),
                    label=("%s @ %.2f MHz (beam %s), %s spline"
                           % (abbrv_name, series.frequency(), "OFF", spline_kind)))
            """
            ax.errorbar(x_off, y_off, yerr=yerr_off, marker=marker, markersize=5,
                        markeredgecolor=marker_color(i_mrk),
                        markerfacecolor=marker_color(i_mrk), linestyle="none",
                        label="%s @ %.2f MHz (beam %s)" % (abbrv_name, series.frequency(), "OFF"),
                        ecolor=marker_color(i_mrk))
            # create spline
            """
            x_on_spline, y_on_spline = gen_spline_from_datetime(x_on, y_on, spline_kind)
            ax.plot(x_on_spline, y_on_spline, linewidth=1, color=marker_color(i_mrk+1),
                    label=("%s @ %.2f MHz (beam %s), %s spline"
                           % (abbrv_name, series.frequency(), "ON", spline_kind)))
            """
            ax.errorbar(x_on, y_on, yerr=yerr_on, marker=marker, markersize=5,
                        markeredgecolor=marker_color(i_mrk+1),
                        markerfacecolor=marker_color(i_mrk+1), linestyle="none",
                        label="%s @ %.2f MHz (beam %s)" % (abbrv_name, series.frequency(), "ON"),
                        ecolor=marker_color(i_mrk+1))

            x_casa, y_casa, yerr_casa = func_casa(series, h_data, v_data)
            # create spline
            """
            x_casa_spline, y_casa_spline = gen_spline_from_datetime(x_casa, y_casa, spline_kind)
            ax.plot(x_casa_spline, y_casa_spline, linewidth=1, color=marker_color(i_mrk+2),
                    label=("%s contribution @ %.2f MHz (ON-OFF), %s spline"
                           % (abbrv_name, series.frequency(), spline_kind)))
            ax.errorbar(x_casa, y_casa,
                        yerr=np.transpose([(min(a, b), b) for a, b in zip(y_casa, yerr_casa)]),
                        marker=marker, markersize=5,
                        markeredgecolor=marker_color(i_mrk+2),
                        markerfacecolor=marker_color(i_mrk+2), linestyle="none",
                        label="%s contribution @ %.2f MHz (ON-OFF)" % (abbrv_name, series.frequency()),
                        ecolor=marker_color(i_mrk+2))
            """

            _t_avg = dt_avg(x_casa)
            __weights = 1/np.array(yerr_casa)**2
            _y_avg = np.average(y_casa, weights=__weights)
            _y_err = 1/np.sqrt(np.sum(__weights))
            
            flux = CalculateFluxCasA(_t_avg, series['frequency']*1e6)  # Jy
            eff = 0.5
            salsa_area = 2.3**2 * np.pi / 4  # m^2
            k_b = 1.38e-23
            t_diff = eff * salsa_area * flux * 1e-26 / (2 * k_b)
            try:
                print _t_avg, ": ", _y_avg, _y_err
                msg = 'CasA: %e K (model), %e K (observed) -> %e' % (t_diff, _y_avg, t_diff/_y_avg)
                msg += " (N/A dB)" if _y_avg < 0 else " ((%f dB)" % todb(t_diff/_y_avg)
                print msg + " (%s dB) factor" % ("N/A" if _y_avg < 0 else ("%f" % todb(t_diff/_y_avg)))
            except Exception as e:
                print e.message
            """
            ax.errorbar(_t_avg, _y_avg, yerr=_y_err,
                        marker=marker, markersize=5,
                        markeredgecolor=marker_color(i_mrk+4),
                        markerfacecolor=marker_color(i_mrk+4), linestyle="none",
                        label="%s average @ %.2f MHz (ON-OFF)" % (abbrv_name, series.frequency()),
                        ecolor=marker_color(i_mrk+4))
            """
        i_mrk += 1
    return azs, els

__Colors  = ['blue', 'red', 'green']
__Splines = ['darkblue', 'darkred', 'darkgreen']
__i = 0
def _plot_err_bar(ax, name, x, xerr, y, yerr, diode, marker, errblbl):
    global __i
    spline_kind = "cubic"
    f = interp1d(x, y, kind=spline_kind)
    _x = np.arange(min(x), max(x), 4)
    ax.plot(_x, f(_x), linewidth=1, color=__Splines[__i],
            label="%s, %s spline" % (errblbl, spline_kind))
    ax.errorbar(x, y,
                #xerr=xerr,
                yerr=yerr, marker=marker, markersize=5,
                linestyle="none", color=__Colors[__i],
                label=errblbl)
    __i += 1


def plot_err_bar(ax, data_dict_items, show_diode, h_data="elevation", v_data="power"):
    i_mrk = 0
    for sat_name, freqs in data_dict_items:
        marker = "."#_marker(i_mrk)
        abbrv_name = sat_name[sat_name.find("(")+1:sat_name.find(")")]

        (x_df, xerr_df), (y_df, yerr_df) = freqs.compute_errbar(h_data, v_data, False)
        _, s_data = freqs.get_sorted(x_df, zip(x_df, xerr_df, y_df, yerr_df))
        x_df, xerr_df, y_df, yerr_df = zip(*s_data)
        _plot_err_bar(ax, abbrv_name, x_df, xerr_df, y_df, yerr_df, False, marker,
                      "diode OFF")

        if show_diode:
            (x_dn, xerr_dn), (y_dn, yerr_dn) = freqs.compute_errbar(h_data, v_data, True)
            _, s_data = freqs.get_sorted(x_dn, zip(x_dn, xerr_dn, y_dn, yerr_dn))
            x_dn, xerr_dn, y_dn, yerr_dn = zip(*s_data)
            _plot_err_bar(ax, abbrv_name, x_dn, xerr_dn,
                          y_dn,
                          yerr_dn, True, marker,
                          "diode ON")
            """
            (x_d, xerr_d), (y_d, yerr_d) = freqs.compute_errbar_diode_delta(h_data, v_data)
            _plot_err_bar(ax, abbrv_name, x_d, xerr_d, y_d, yerr_d,
                          True, marker,
                          "diode contribution")
            """
        i_mrk += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot elevation vs power.')
    parser.add_argument("-f", "--file",
                        action="store", dest="data_file",
                        type=str, required=True,
                        help="/path/to/file that is to be processed")
    parser.add_argument("-x", "--horizontal-data",
                        action="store", dest='horizontal_data',
                        type=str, required=True,
                        help="The data to be used for the horizontal axis")
    parser.add_argument("-y", "--vertical-data",
                        action="store", dest='vertical_data',
                        type=str, required=True,
                        help="The data to be used for the vertical axis")
    args = parser.parse_args()
    fig = plt.figure()
    ax = fig.add_subplot(111)
    #ax.yaxis.grid(which="major", color='r', linestyle='-', linewidth=2)
    ax.yaxis.grid()
    ax.set_ylabel("Uncalibraded power (dBW)")
    #ax.set_xlabel("Elevation angle (degrees)")
    data_dict = load_file(args.data_file)

    choise = 0
    if choise == 0:
        ax.set_title("2-hour measurement on all GPS PRN 30")
        ax.set_xlabel("Time (HH:MM)")
        plot_on_axis(ax, data_dict.items(), False, args.horizontal_data, args.vertical_data)
        #ax.legend(loc='lower right')
        #ax.set_ylim((-20, 0))
    elif choise == 1:
        az, el = plot_beam_switch(ax, data_dict.items(), False, args.horizontal_data, args.vertical_data)
        fig.suptitle("Casiopeia A @ Az=%.2f, El=%.2f" % (np.average(az), np.average(el)), fontsize=16)
        ax.set_xlabel("Time (HH:MM)")
        #ax.set_ylim((-25.2, -24.9))
        ax.legend(loc='lower left')
        #ax.set_yscale('log')
    elif choise == 2:
        plot_err_bar(ax, data_dict.items(), True, args.horizontal_data, args.vertical_data)
        ax.set_title("Zenith @ Az=270, El=90")
        ax.set_xlabel("Frequency (MHz)")
        ax.set_ylim((-30.0, 10.0))
        ax.legend(loc='lower left')
    plt.show()
