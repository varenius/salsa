import argparse
import logging
import re
from datetime import datetime
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np


band_to_sys = {
    "A1": "ASTRO",
    "A2": "ASTRO",
    "A5": "ASTRO",
    "L1": "GPS",
    "L2": "GPS",
    "L5": "GPS",
    "E1": "GSAT",
    "E5a": "GSAT",
    "E5b": "GSAT",
    "E6": "GSAT",
    "G1": "COSMOS",
    "G2": "COSMOS",
    "G3": "COSMOS"
}

band_to_freq = {
    "A1": ["%010.4f" % 1550.0],
    "A2": ["%010.4f" % 1200.0],
    "A5": ["%010.4f" % 1150.0],
    "L1": ["%010.4f" % 1575.42],
    "L2": ["%010.4f" % 1227.60],
    "L5": ["%010.4f" % 1176.45],
    "E1": ["%010.4f" % 1575.42],
    "E5a": ["%010.4f" % 1176.45],
    "E5b": ["%010.4f" % 1207.14],
    "E6": ["%010.4f" % 1278.75],
    "G1": ["%010.4f" % (lambda n: 1602 + n*0.5625)(v) for v in range(-7, 7)],
    "G2": ["%010.4f" % (lambda n: 1246 + n*0.4375)(v) for v in range(-7, 7)],
    "G3": ["%010.4f" % (lambda n: 1201 + n*0.4375)(v) for v in range(-7, 7)]
}

plot_markers = ['o', 'x', '*', '+', 'd', 's', 'v', '^', '<', '>',
                '1', '2', '3', '4', '8', 'h', 'p', 'H', 'D',
                '|', '.', ',', '_']
plot_band_marker_colors = ['red', 'green', 'blue', 'yellow',
                           'magenta', 'cyan', 'black']


def todb(v):
    return 10 * np.log10(v)


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


class MeasurementSeries:
    def __init__(self, frequency):
        self._freq = frequency
        self._time = list()
        self._az = list()
        self._el = list()
        self._power = list()

    def add_entry(self, time_, az_, el_, power_):
        self._time.append(time_)
        self._az.append(az_)
        self._el.append(el_)
        self._power.append(power_)

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

    def get_sorted(self, sort_key, sort_val):
        return zip(*sorted([(k, v) for k, v in zip(sort_key, sort_val)],
                           key=lambda e: e[0]))


def load_data(fname):
    with open(fname, "r") as f:
        d = f.read()
    return [l for l in re.split("\\r?\\n", d) if l and not l.startswith("#")]


def include_data(systems, freqs, name, freq):
    if freq not in freqs:
        return False
    go_on = False
    for n in systems:
        if n in name:
            go_on = True
            break
    return go_on


def load_file(fname, systems, freqs):
    dlist = [[t.strip() for t in l.split("\t")] for l in load_data(fname)]
    ddict = dict()
    for (time_stamp, name, freq, az, el, pwr) in dlist:
        if not include_data(systems, freqs, name, freq):
            continue
        if name not in ddict:
            ddict[name] = dict()
        if freq not in ddict[name]:
            ddict[name][freq] = MeasurementSeries(float(freq))
        y, yday, dsec = time_stamp.split(":")
        r, c = name.replace("ASTRO Sun (Sun)_", "").split("_")
        if (r.endswith(".8")):
            r = r[:-2] + ".75"
        elif (r.endswith(".2")):
            r = r[:-2] + ".25"
        if (c.endswith(".8")):
            c = c[:-2] + ".75"
        elif (c.endswith(".2")):
            c = c[:-2] + ".25"

        ddict[name][freq].add_entry(y_yday_dsec_to_date(y, yday, dsec),
                                    float(c), float(r), float(pwr))
    return ddict


def asd_(v):
    for v0, v1 in zip(v[:-1], v[1:]):
        if abs(v1-v0) > 0:
            return abs(v1 - v0)
    return 0


def plot_on_axis(ax, data_dict_items):
    n_cols = [ddi.values()[0].azimuth()[0] for _, ddi in data_dict_items]
    n_rows = [ddi.values()[0].elevation()[0] for _, ddi in data_dict_items]
    n_pwr = [ddi.values()[0].power()[0] for _, ddi in data_dict_items]
    c_sep = asd_(sorted(n_cols))
    r_sep = asd_(sorted(n_rows))

    n_cols_ = [int(round((c - min(n_cols))/c_sep)) for c in n_cols]
    n_rows_ = [int(round((r - min(n_rows))/r_sep)) for r in n_rows]
    data_pwr = np.zeros((1 + int(round((max(n_rows)-min(n_rows))/r_sep)),
                         1 + int(round((max(n_cols)-min(n_cols))/c_sep))),
                        dtype=np.float64)
    data_col = np.zeros((1 + int(round((max(n_rows)-min(n_rows))/r_sep)),
                         1 + int(round((max(n_cols)-min(n_cols))/c_sep))),
                        dtype=np.float64)
    data_row = np.zeros((1 + int(round((max(n_rows)-min(n_rows))/r_sep)),
                         1 + int(round((max(n_cols)-min(n_cols))/c_sep))),
                        dtype=np.float64)
    for ((i, x), (j, y), p) in zip(zip(n_cols_, n_cols),
                                   zip(n_rows_, n_rows),
                                   n_pwr):
        data_col[j, i] = x
        data_row[j, i] = y
        data_pwr[j, i] = p
    (xmin, xmax, ymin, ymax) = (min(n_cols)-c_sep/2, max(n_cols)+c_sep/2,
                                min(n_rows)-r_sep/2, max(n_rows)+r_sep/2)
    im = ax.imshow(data_pwr, cmap='jet', interpolation='nearest',
                   extent=[xmin, xmax, ymax, ymin])
    ax.axis([xmin, xmax, ymin, ymax])
    return im


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot elevation vs power.')
    parser.add_argument("-f", "--file",
                        action="store", dest="data_file",
                        type=str, required=True,
                        help="/path/to/file that is to be processed")
    parser.add_argument("-b", "--frequency-band",
                        action="store", dest='frequency_bands',
                        type=str, required=True, nargs="+",
                        help="The frequency bands that are of interest. ")
    args = parser.parse_args()
    data_file = args.data_file
    band = args.frequency_bands
    sys_ = list()
    freqs_ = list()
    for b in band:
        sys_.append(band_to_sys[b])
        freqs_.extend(band_to_freq[b])
    data_dict = load_file(data_file, sys_, freqs_)
    fig = plt.figure()
    ddi = data_dict.items()
    if False:
        plot_on_axis(fig.add_subplot(241), ddi[int(0*len(ddi)/8):int(1*len(ddi)/8)])
        plot_on_axis(fig.add_subplot(242), ddi[int(1*len(ddi)/8):int(2*len(ddi)/8)])
        plot_on_axis(fig.add_subplot(243), ddi[int(2*len(ddi)/8):int(3*len(ddi)/8)])
        plot_on_axis(fig.add_subplot(244), ddi[int(3*len(ddi)/8):int(4*len(ddi)/8)])
        plot_on_axis(fig.add_subplot(245), ddi[int(4*len(ddi)/8):int(5*len(ddi)/8)])
        plot_on_axis(fig.add_subplot(246), ddi[int(5*len(ddi)/8):int(6*len(ddi)/8)])
        plot_on_axis(fig.add_subplot(247), ddi[int(6*len(ddi)/8):int(7*len(ddi)/8)])
        plot_on_axis(fig.add_subplot(248), ddi[int(7*len(ddi)/8):int(8*len(ddi)/8)])
    elif False:
        plot_on_axis(fig.add_subplot(221), ddi[:int(1*len(ddi)/4)])
        plot_on_axis(fig.add_subplot(222), ddi[int(len(ddi)/4):int(len(ddi)/2)])
        plot_on_axis(fig.add_subplot(223), ddi[int(len(ddi)/2):int(3*len(ddi)/4)])
        plot_on_axis(fig.add_subplot(224), ddi[int(3*len(ddi)/4):])
    else:
        # fig.add_subplot(111, projection='3d')
        # fig.gca(projection='3d')
        ax = fig.add_subplot(111)
        im = plot_on_axis(ax, ddi)
        divider = make_axes_locatable(ax)
        cax = divider.append_axes('right', size='5%', pad=0.05)
        fig.colorbar(im, cax=cax, orientation='vertical')
    plt.show()


"""
# Define model function to be used to fit measured beam data:
def oneD_Gaussian(x, *p):
    A, mu, sigma, offset = p
    return offset + A*np.exp(-(x-mu)**2/(2.*sigma**2))


def twoD_Gaussian((x, y), amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
    # ""
    # Define 2D Gaussian according to
    # http://stackoverflow.com/questions/21566379/fitting-a-2d-gaussian-function-using-scipy-optimize-curve-fit-valueerror-and-m/21566831#21566831
    # ""
    xo = float(xo)
    yo = float(yo)
    a = np.cos(theta)**2 / (2*sigma_x**2) + np.sin(theta)**2 / (2*sigma_y**2)
    b = -np.sin(2*theta) / (4*sigma_x**2) + np.sin(2*theta) / (4*sigma_y**2)
    c = np.sin(theta)**2 / (2*sigma_x**2) + np.cos(theta)**2 / (2*sigma_y**2)
    xc = x - xo
    yc = y - yo
    g = offset + amplitude*np.exp(-(a*xc**2 + 2*b*xc*yc + c*yc**2))
    return g.ravel()


def fit_gauss(data):
    leftpos = map2plot['leftpos']
    rightpos = map2plot['rightpos']
    nleft = len(leftpos)
    nright = len(rightpos)
    leftmid = np.mean(leftpos)
    rightmid = np.mean(rightpos)
    leftrel = leftpos - leftmid
    rightrel = rightpos - rightmid
    if nleft > 1 and nright > 1:
        # Two-D Gauss
        p0 = [500,  # amplitude
              0.0,  # xo
              0.0,  # yo
              5.0,  # sigma_x
              5.0,  # sigma_y
              0.0,  # theta
              100]  # offset
        rm, lm = np.meshgrid(rightrel, leftrel)
        popt, pcov = curve_fit(twoD_Gaussian, (rm, lm), np.ravel(data), p0=p0)
        print popt
        fx0 = popt[1]
        fy0 = popt[2]
        fsigma_x = popt[3]
        fsigma_y = popt[4]
        print(('Towards {0}, {1}: Fitted Gaussian roff={2}deg, '
               'loff={3}, FWHM1={4}deg, FWHM2={5}deg.').format(
                   round(leftmid, 1), round(rightmid, 1), fx0, fy0,
                   fsigma_x*2.355, fsigma_y*2.355))
        npt = 100
        xv = np.linspace(np.min(rightrel), np.max(rightrel), npt)
        yv = np.linspace(np.min(leftrel), np.max(leftrel), npt)
        xi, yi = np.meshgrid(xv, yv)
        model = self.twoD_Gaussian((xi, yi), *popt)
        plt.contour(xi, yi, model.reshape(npt, npt), 8, colors='k')
    else:
        if nleft > 1 and nright == 1:
            xvals = leftrel
            yvals = data.flatten()
        if nleft == 1 and nright > 1:
            xvals = rightrel
            yvals = data.flatten()
        # p0 is the initial guess for the fitting coefficients
        # (A, mu,sigma, offset)
        wmean = np.average(xvals, weights=yvals)
        wvar = np.average((xvals-wmean)**2, weights=yvals)
        wstd = np.sqrt(wvar)
        p0 = [max(yvals), wmean, wstd, min(yvals)]
        popt, pcov = curve_fit(self.oneD_Gaussian, xvals, yvals, p0=p0)
        # Make nice grid for fitted data
        fitx = np.linspace(min(xvals), max(xvals), 500)
        # Get the fitted curve
        fity = self.oneD_Gaussian(fitx, *popt)
        fsigma = popt[2]
        fmu = popt[1]
        fbeam = 2.355*fsigma  # FWHM
        plt.plot(fitx, fity, '--', color='blue')
        print(('Towards {0}, {1}: Fitted Gaussian mean={2}deg and '
               'FWHM={3} deg.').format(round(leftmid, 1),
                                       round(rightmid, 1),
                                       fmu, fbeam))
"""
