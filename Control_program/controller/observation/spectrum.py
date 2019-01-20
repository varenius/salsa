from os import remove
from datetime import datetime

from numpy import (radians, degrees, floor, ceil, arange, ones_like,
                   polyfit, polyval, shape, where, cos, sin, pi,
                   array, min, max, int16, clip, sum, arange)
from scipy import signal as signal
from scipy.constants import c
from ephem import (FixedBody, now, Galactic, Equatorial,
                   Ecliptic, Sun, Observer, Date)
from astropy.io import fits
from MySQLdb import connect


class ArchiveConnection:
    def __init__(self, host_, db_, user_, passwd_, table_):
        self._host = host_
        self._db = db_
        self._user = user_
        self._passwd = passwd_
        self._table = table_

    def __enter__(self):
        self._conn = connect(host=self._host, passwd=self._passwd,
                             db=self._db, user=self._user)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._conn.close()
        return False

    def get_table(self):
        return self._table

    def escape_string(self, s):
        return self._conn.escape_string(s)

    def execute_query(self, query):
        with self._conn as cursor:
            cursor.execute(query)


class SALSA_spectrum:
    def __init__(self, logger_, site_, alt_, az_, username_,
                 offset_alt_, offset_az_, instrument_name_, db_conn_,
                 diode_on_):
        self._logger = logger_
        # All units shall be S.I. (Hz, etc. not MHz)
        self._rest_freq = 1420.40575177e6  # Hz, from Wiki.
        self._obs_freq = None
        self._data = None
        self._bandwidth = None
        self._nchans = None
        self._int_time = None

        self._site = self._clone_site(site_)

        self._alt = alt_  # deg
        self._az = az_  # deg
        pointing = FixedBody()
        pointing._ra, pointing._dec = self._site.radec_of(radians(self._az),
                                                          radians(self._alt))
        pointing._epoch = now()
        pointing.compute(self._site)

        # NOTE: This will not be true for a long measurement
        self._target = Galactic(pointing)
        self._observer = username_
        self._uploaded = False
        self._freq_vlsr_corr = 0
        self._vlsr_corr = 0

        self._instr_name = instrument_name_
        self._dbc = db_conn_

        self._diode_on = diode_on_

        self._offset_alt = offset_alt_
        self._offset_az = offset_az_

    def __sub__(self, other):
        """
        Creates a copy of self with the difference being that the
        spectrum data in then new copy is the spectrum data from
        self with the spectrum data from other removed from it.
        """
        out = SALSA_spectrum(self._logger, self._site, self._alt, self._az,
                             self._observer, self._offset_alt, self._offset_az,
                             self._instr_name, self._dbc, self._diode_on)
        if self._data is not None and other._data is not None:
            out.add_data(self._data - other._data, self._obs_freq,
                         self._bandwidth, self._nchans, self._int_time)
        return out

    def add_data(self, data_, f_center_, bandwidth_,
                 nchans_, int_time_):
        self._data = data_
        self._obs_freq = f_center_
        self._bandwidth = bandwidth_
        self._nchans = nchans_
        self._int_time = int_time_

    def auto_edit_bad_data(self):
        self._logger.info("Autoflagging known RFI.")
        freq_res = self._bandwidth/self._nchans  # Hz
        # List known RFI as center-frequency in MHz, and width in Mhz
        # This list contains peaks which are not properly picked by
        # by the MWF filter.
        known_RFI = [[1420.4+4.595, 0.02]]
        for item in known_RFI:
            RFI_freq = item[0] * 1e6
            RFI_width = item[1] * 1e6
            ch0_freq = self._obs_freq - 0.5*self._bandwidth
            ind_low = int(floor((RFI_freq-0.5*RFI_width - ch0_freq)/freq_res))
            ind_high = int(ceil((RFI_freq+0.5*RFI_width - ch0_freq)/freq_res))
            if ind_low > 0 and ind_high < self._nchans:
                self._logger.debug("Flagging " + str(item))
                margin = min((ind_high-ind_low, ind_low, self._nchans-ind_high))
                RFI_part = self._data[ind_low-margin:ind_high+margin]
                xdata = arange(len(RFI_part))
                weights = ones_like(RFI_part)
                weights[margin:-margin] = 0.0  # Ignore RFI when fitting
                pf = polyfit(xdata, RFI_part, deg=1, w=weights)
                interpdata = polyval(pf, xdata)
                self._data[ind_low:ind_high] = interpdata[margin:-margin]
            else:
                self._logger.debug("Skipping " + str(item))
        # Filter away rest of RFI with median window filter,
        # assuming 4096 channels for 2MHz bandwidth
        self._data = signal.medfilt(self._data, kernel_size=7)

        # In the future, remove receiver end dip. But now switch away instead
        # print shape(self._data)
        # print where(self._data<50)
        # self._data[0:10]=self._data[10] # Remove receiver dip

    def shift_to_vlsr_frame(self):
        # From http://web.mit.edu/8.13/www/nsrt_software/documentation/vlsr.pdf
        ep_target = Equatorial(self._target)
        # Sun velocity apex is at 18 hr, 30 deg; convert to x, y, z
        # geocentric celestial for dot product with source, multiply by speed
        x0 = 20.0 * cos(18.0*pi/12.0) * cos(radians(30.0))
        y0 = 20.0 * sin(18.0*pi/12.0) * cos(radians(30.0))
        z0 = 20.0 * sin(radians(30.0))

        # Make sure we have target angles in radians
        tg_ra_rad = float(ep_target.ra)
        tg_dec_rad = float(ep_target.dec)

        # Calculate sinces, cosines for dot product
        ctra = cos(tg_ra_rad)
        stra = sin(tg_ra_rad)
        ctdc = cos(tg_dec_rad)
        stdc = sin(tg_dec_rad)

        # Calculate correction due to movement of Sun with respect to LSR
        # dot product of target & apex vectors
        vsun = x0*ctra*ctdc + y0*stra*ctdc + z0*stdc

        # get target in geocentric ecliptic system
        ecl = Ecliptic(ep_target)
        tlon = ecl.lon
        tlat = ecl.lat

        # Get sun ecliptic coordinates, in radians
        sun = Sun()
        sun.compute(self._site)
        se = Ecliptic(sun)
        slong = float(se.lon)

        # Calculate correction due to earth movement relative to the Sun
        vorb = 30.0*cos(tlat)*sin(slong-tlon)

        # Combine both effects
        vlsr_kmps = vsun + vorb  # in km/s

        vlsr_corr = 1e3*vlsr_kmps  # in m/s

        self._vlsr_corr = vlsr_corr  # store for this spectrum
        # Convert and store shift also for frequency
        self._freq_vlsr_corr = -1*self._rest_freq*self._vlsr_corr/c

    def decimate_channels(self, outchans):
        self._data = signal.decimate(self._data,
                                     int(round(float(self._nchans)/float(outchans))),
                                     axis=0, ftype='fir')
        self._nchans = outchans

    def get_center_freq(self):
        return self._obs_freq + self._freq_vlsr_corr

    def get_observation_freq(self):
        return self._obs_freq

    def get_output_channels(self):
        return self._nchans

    def get_freqs(self):
        halffft = int(self._nchans / 2.0)
        f_c = self.get_center_freq()
        return f_c + self._bandwidth/2.0 * arange(-halffft, halffft)/halffft

    def get_vels(self):
        freqs = self.get_freqs()
        # The -1 sign is introduced by comparison with the LAB survey. Velocity
        # conversions... always the other one.
        return -1*(freqs-self._rest_freq)*c/self._rest_freq

    def format_date(self, ephem_date):
        return "%04d-%02d-%02dT%02d:%02d:%04.1f" % ephem_date.tuple()

    def _save_to_txt(self, outfile, vels, vel_col_text):
        with open(outfile, "w") as text_file:
            text_file.write("# BEGINHEADER\n")
            text_file.write("# This file contains data from the SALSA 2m "
                            "radio telescope.\n")
            text_file.write("# DATE=%s\n"
                            % self.format_date(self._site.date))
            text_file.write("# GLON and GLAT given in degrees\n")
            # Degrees
            text_file.write("# GLON={0}\n".format(degrees(float(self._target.lon))))
            text_file.write("# GLAT={0}\n".format(degrees(float(self._target.lat))))
            text_file.write(("# DATA in two columns below. "
                             "Col. 1 is %s. Col. 2 is %s.\n")
                            % (vel_col_text,
                               "uncalibrated antenna temperature [K]"))
            text_file.write("# ENDHEADER\n")
            for v, d in zip(vels, self._data):
                text_file.write("{0} {1}\n".format(v, d))

    def save_to_txt_vel(self, outfile):
        self._save_to_txt(outfile,
                          self.get_vels() * 1e-3,
                          "velocity relative to LSR [km/s]")

    def save_to_txt_freq(self, outfile, f_center):
        self._save_to_txt(outfile,
                          (self.get_freqs() - f_center) * 1e-6,
                          "frequency [MHz]")

    def save_to_fits(self, outfile):
        # Instructions for writing FITS at
        # https://python4astronomers.github.io/astropy/fits.html
        # Set of keywords chosen to match SalsaJ requirements.
        hdu = fits.PrimaryHDU()
        datamin = min(self._data)
        datamax = max(self._data)
        glon = degrees(float(self._target.lon))  # degrees
        glat = degrees(float(self._target.lat))  # degrees

        # Since using  int16 as datatype we use bscale and bzero to
        # keep dynamic range. SalsaJ cannot read bitpix correctly
        # except 16 bit. If SalsaJ could read bitpix, we could just
        # have BITPIX -64 and skip Bscale, Bzero, i.e. just remove
        # astype above.
        bscale = (datamax-datamin)/65534.0
        bzero = datamin+bscale*32767.0
        # hdu.header['BLANK']  = -32768
        scaledata = (self._data - bzero)/bscale
        # 16 bit for SalsaJ
        hdu.data = scaledata.reshape(1, 1, self._nchans).astype(int16)
        hdu.header['BSCALE'] = bscale
        hdu.header['BZERO'] = bzero
        hdu.header['BUNIT'] = 'K'
        hdu.header['CTYPE1'] = 'FREQ'
        hdu.header['CRPIX1'] = self._nchans/2  # number of channels
        hdu.header['CRVAL1'] = self._obs_freq
        hdu.header['CDELT1'] = self._bandwidth/self._nchans  # Channel width
        hdu.header['CUNIT1'] = 'Hz'
        hdu.header['CTYPE2'] = 'GLON'
        hdu.header['CRPIX2'] = 0
        hdu.header['CRVAL2'] = glon
        hdu.header['CDELT2'] = 1.0
        hdu.header['CUNIT2'] = 'DEGREE'
        hdu.header['CTYPE3'] = 'GLAT'
        hdu.header['CRPIX3'] = 0
        hdu.header['CRVAL3'] = glat
        hdu.header['CDELT3'] = 1.0
        hdu.header['CUNIT3'] = 'DEGREE'
        hdu.header['TELESCOP'] = 'SALSA 2m'
        # Rest frequency of line
        hdu.header['RESTFREQ'] = self._rest_freq
        # in km/s, sign as needed by SalsaJ
        hdu.header['VELO-LSR'] = (-1)*self._vlsr_corr/1000.0
        hdu.header['VLSRUNIT'] = 'km/s'
        hdu.header['DATE-OBS'] = self.format_date(self._site.date)
        hdu.header['DATE'] = self.format_date(now())
        hdu.header['ORIGIN'] = 'ONSALA, SWEDEN'
        hdu.header['INSTRUME'] = self._instr_name
        hdu.header['OBSTIME'] = self._int_time
        hdu.header['OBSERVER'] = self._observer
        # header['OBJECT'] = 'Milky Way'
        # eq = self._target.epoch.triple()
        # Epoch in decimal years.
        # header['EQUINOX'] = str(eq[0] + eq[1]/12.0 + eq[2]/(24*12.0))
        hdu.header['EQUINOX'] = 2000
        # hdu.header['DATAMAX']  = datamax
        # hdu.header['DATAMIN']  = datamin
        # header['LINE'] = 'HI(21CM)'
        hdu.header['AZIMUTH'] = self._az  # Degrees
        hdu.header['ELEVATIO'] = self._alt  # Degrees
        hdu.header['INTTIME'] = self._int_time
        try:
            remove(outfile)
        except OSError:
            pass
        hdu.writeto(outfile)

    def upload_to_archive(self, fitsfile, pngfile, txtfile):
        # Read fitsdata
        with open(fitsfile, 'rb') as f_fits:
            fitsdata = f_fits.read()
        with open(pngfile, 'rb') as f_png:
            pngdata = f_png.read()
        with open(txtfile, 'rb') as f_txt:
            txtdata = f_txt.read()

        # Insert to database
        pos = Galactic(self._target)
        unixtime_sec = floor((self._site.date.datetime() - datetime(1970, 1, 1)).total_seconds())

        with self._dbc:
            mysqlcmd = "INSERT INTO %s SET " % self._dbc.get_table()
            mysqlcmd += "file_fits='%s'," % self._dbc.escape_string(fitsdata)
            mysqlcmd += "observer='%s'," % self._observer
            mysqlcmd += "glon='%s'," % self._dbc.escape_string(str(pos.lon))
            mysqlcmd += "glat='%s'," % self._dbc.escape_string(str(pos.lat))
            mysqlcmd += "obsdate=%s," % str(unixtime_sec)
            mysqlcmd += "obsfreq=%s," % str(1e-6*self._obs_freq)
            mysqlcmd += "bandwidth=%s," % str(1e-6*self._bandwidth)
            mysqlcmd += "int_time=%s," % str(self._int_time)
            mysqlcmd += "telescope='%s'," % self._site.name
            mysqlcmd += "file_png='%s'," % self._dbc.escape_string(pngdata)
            mysqlcmd += "file_txt='%s'" % self._dbc.escape_string(txtdata)
            self._dbc.execute_query(mysqlcmd)
            self._uploaded = True

    def get_total_power(self, inner_frac=0.75):
        # Calculate total power (sum of values in spectra divided by
        # number of channels)
        # Use only inner 75% to avoid band edge effects
        skip_each = (1.0 - clip(inner_frac, 0, 1)) / 2.0
        bgn = skip_each
        end = 1.0-skip_each
        return sum(self._data[int(bgn*self._nchans):int(end*self._nchans)])

    def get_offset_el(self):
        return self._offset_alt

    def get_offset_az(self):
        return self._offset_az

    def get_elevation(self):
        return self._alt

    def get_azimuth(self):
        return self._az

    def get_diode_on(self):
        return self._diode_on

    def spectrum_info_str(self):
        return (("SPECTRUM INFO: Offset_alt=%.3f deg. Offset_az=%.3f deg. "
                "Total power = %e, alt=%.3f, az=%.3f")
                % (self._offset_alt, self._offset_az, self.get_total_power(),
                   self._alt, self._az))

    def get_vlsr_corr(self):
        return self._vlsr_corr

    def get_freq_vlsr_corr(self):
        return self._freq_vlsr_corr

    def is_uploaded(self):
        return self._uploaded

    def get_observer(self):
        return self._observer

    def get_target(self):
        return self._target

    def get_data(self):
        return self._data

    def get_site(self):
        return self._site

    def get_site_date(self):
        return self._site.date

    @staticmethod
    def _clone_site(site_):
        # Copy relevant properties from input site
        site = Observer()
        site.lat = site_.lat
        site.lon = site_.lon
        site.elev = site_.elev
        site.name = site_.name
        site.pressure = site_.pressure
        # Make sure we do not keep reference to old time
        site.date = Date(site_.date)
        return site
