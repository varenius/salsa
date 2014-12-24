import ephem
import numpy as np
import matplotlib.pyplot as pngplt
from scipy import signal as signal
from astropy.io import fits
import math, os
from scipy.constants import c
import MySQLdb as mdb
from datetime import datetime


class SALSA_spectrum:
    def __init__(self, data, bandwidth, nchans, cfreq, site, alt, az, int_time, username, config, offset_alt, offset_az):
        # All units shall be S.I. (Hz, etc. not MHz)
        self.rest_freq = 1420.40575177e6 # Hz, from Wiki.
        self.obs_freq = float(cfreq)
        self.data = np.copy(data)
        self.bandwidth = float(bandwidth)
        self.nchans = int(nchans)
        self.int_time = int(int_time)
        # Copy relevant properties from input site
        self.site = ephem.Observer()
        self.site.name = site.name
        self.site.lat = site.lat
        self.site.long = site.long
        self.site.elevation = site.elevation
        self.site.pressure = site.pressure
        self.site.date = ephem.Date(site.date) # Make sure we do not keep reference to old time
        self.alt = alt # deg
        self.az = az # deg
        alt_rad = self.alt*np.pi/180.0
        az_rad = self.az*np.pi/180.0
        (ra, dec) = self.site.radec_of(az_rad, alt_rad)
        pointing = ephem.FixedBody()
        pointing._ra = ra
        pointing._dec = dec
        pointing._epoch = ephem.now()
        pointing.compute(self.site)
        # NOTE: This will not be true for a long measurement
        self.target = ephem.Galactic(pointing)
        self.observer = username
        self.uploaded = False
        self.freq_vlsr_corr = 0
        self.vlsr_corr = 0
        self.config = config
        self.offset_alt = offset_alt
        self.offset_az = offset_az

    def auto_edit_bad_data(self):
        #print "Autoflagging known RFI."
        freq_res = self.bandwidth/self.nchans # Hz
        # List known RFI as center-frequency in MHz, and width in Mhz
        known_RFI = [[1419.4-0.210, 0.02], 
                     [1419.4-1.937, 0.015], 
                     [1419.4-4.4, 0.015], 
                     [1419.4+3.0, 0.01], 
                     # remove dip in the center of band
                     [self.obs_freq*1e-6, 0.02], 
                     [1416.4-0.8, 0.04],
                     [1420.4-2, 0.01],
                     [1425, 0.01],
                     [1424.4-1.8, 0.01],
                     [1424.4+0.5845, 0.01],
                     [1424.4+0.483, 0.005],
                     [1420.4-1.38, 0.01],
                     [1420.4-1.042, 0.01],
                     [1424.4+0.61, 0.03],
                     [1420.4-0.3965, 0.005],
                     [1420.4+0.4465, 0.005],
                     [1420.4+3.405, 0.01],
                     [1420.4+4.299, 0.02],
                     [1420.4+4.61, 0.06],
                     [1420.4+4.67, 0.02],
                     [1420.4-3.197, 0.04],
                     [1420.4-2.39, 0.04],
                     [1420.4-0.395, 0.02],
                     [1420.4+6.21, 0.04],
                     ]
        for item in known_RFI:
            RFI_freq = item[0] *1e6 
            RFI_width = item[1]*1e6
            ch0_freq = self.obs_freq - 0.5*self.bandwidth
            ind_low = int(np.floor((RFI_freq-0.5*RFI_width - ch0_freq)/freq_res))
            ind_high = int(np.ceil((RFI_freq+0.5*RFI_width - ch0_freq)/freq_res))
            #print ind_low, ind_high
            if ind_low>0 and ind_high<self.nchans:
                #print 'Flagging', item
                margin = min(ind_high-ind_low, ind_low, self.nchans-ind_high)
                RFI_part = self.data[ind_low-margin:ind_high+margin]
                xdata = np.arange(len(RFI_part))
                weights = np.ones_like(RFI_part)
                weights[margin:-margin] = 0.0 # Ignore RFI when fitting
                pf = np.polyfit(xdata, RFI_part, deg=1, w=weights)
                interpdata = np.polyval(pf, xdata)
                self.data[ind_low:ind_high] = interpdata[margin:-margin]
            else:
                #print 'Skipping', item
                pass

    def shift_to_vlsr_frame(self):
        # From http://web.mit.edu/8.13/www/nsrt_software/documentation/vlsr.pdf
        ep_target = ephem.Equatorial(self.target)
        # Sun velocity apex is at 18 hr, 30 deg; convert to x, y, z
        # geocentric celestial for dot product with source, multiply by speed
        x0 = 20.0 * math.cos(18.0 * np.pi / 12.0) * math.cos(30.0 * np.pi / 180.0)
        y0 = 20.0 * math.sin(18.0 * np.pi / 12.0) * math.cos(30.0 * np.pi / 180.0)
        z0 = 20.0 * math.sin(30.0 * np.pi / 180.0)
    
        # Make sure we have target angles in radians
        tg_ra_rad = float(ep_target.ra)
        tg_dec_rad = float(ep_target.dec)
       
        # Calculate sinces, cosines for dot product
        ctra = math.cos(tg_ra_rad)
        stra = math.sin(tg_ra_rad)
        ctdc = math.cos(tg_dec_rad)
        stdc = math.sin(tg_dec_rad)
    
        # Calculate correction due to movement of Sun with respect to LSR
        # dot product of target & apex vectors
        vsun = x0*ctra*ctdc + y0*stra*ctdc + z0*stdc
    
        # get target in geocentric ecliptic system
        ecl =  ephem.Ecliptic(ep_target)
        tlon = ecl.lon
        tlat = ecl.lat
    
        # Get sun ecliptic coordinates, in radians
        sun = ephem.Sun()
        sun.compute(self.site)
        se = ephem.Ecliptic(sun)
        slong = float(se.lon)
    
        # Calculate correction due to earth movement relative to the Sun
        vorb = 30.0*math.cos(tlat)*math.sin(slong-tlon)
    
        # Combine both effects
        vlsr_kmps = vsun + vorb # in km/s
        
        vlsr_corr = 1e3*vlsr_kmps # in m/s

        self.vlsr_corr = vlsr_corr # store for this spectrum
        # Convert and store shift also for frequency
        self.freq_vlsr_corr = -1*self.rest_freq*self.vlsr_corr/c

    def decimate_channels(self, outchans):
        self.data = signal.decimate(self.data, self.nchans/outchans, axis=0, ftype = 'fir')
        self.nchans = outchans

    def get_center_freq(self):
        return self.obs_freq + self.freq_vlsr_corr

    def get_freqs(self):
        halffft = int(0.5*self.nchans)
        freqs = self.get_center_freq() + 0.5*self.bandwidth*np.array(range(-halffft,halffft))/(halffft)
        return freqs

    def get_vels(self):
        freqs = self.get_freqs()
        # The -1 sign is introduced by comparison with the LAB survey. Velocity
        # conversions... always the other one.
        vels = -1*(freqs-self.rest_freq)*c/self.rest_freq 
        return vels

    def save_to_txt(self, outfile):
        vels = self.get_vels() * 1e-3 # km/s
        data = self.data
        with open(outfile, "w") as text_file:
            text_file.write("# BEGINHEADER\n")
            text_file.write("# This file contains data from the SALSA 2m radio telescope.\n")
            dateobs = self.site.date.tuple()
            YYYY=str(dateobs[0]); MM=str(dateobs[1]); DD=str(dateobs[2]); hh = str(dateobs[3]); mm=str(dateobs[4]); ss=str(round(dateobs[5]))
            date = YYYY.zfill(4)+'-'+MM.zfill(2)+'-'+DD.zfill(2)+'T'+hh.zfill(2)+':'+mm.zfill(2)+':'+ss.zfill(2)
            text_file.write("# DATE=" + date + "\n")
            text_file.write("# GLON and GLAT given in degrees\n")
            text_file.write("# GLON={0}\n".format(float(self.target.lon)*180/np.pi)) # Degrees
            text_file.write("# GLAT={0}\n".format(float(self.target.lat)*180/np.pi)) # Degrees
            text_file.write("# DATA in two columns below. Col. 1 is velocity relative to LSR [km/s]. Col. 2 is uncalibrated antenna temperature [K].\n")
            text_file.write("# ENDHEADER\n")
            for i, datum in enumerate(data):
                text_file.write("{0} {1}\n".format(vels[i], data[i]))

    def save_to_fits(self, outfile):
        # Standard according to old SALSA files from Qradio and from http://archive.stsci.edu/fits/fits_standard/node39.html
        header = fits.Header()
        header['SIMPLE']  = 'T'
        # The NAXIS keywords are set by pyfits automatically
        # Written to work with XS, as decribed in mace.fits shipped with XS.
        header['RESTFREQ'] = self.rest_freq # Rest frequency of center channel
        header['CTYPE1'] = 'FREQ'
        header['CRPIX1'] = self.nchans/2 # number of channels
        header['CRVAL1'] = self.freq_vlsr_corr # Offset from RESTFREQ, i.e. doppler shift for center freq.
        header['CDELT1'] = self.bandwidth/self.nchans # Channel width
        header['VLSR'] = self.vlsr_corr
        header['CTYPE2'] = 'GLON'
        header['CRPIX2'] = 0
        header['CRVAL2'] = float(self.target.lon)*180/np.pi # Degrees
        header['CDELT2'] = 1.0
        header['CTYPE3'] = 'GLAT'
        header['CRPIX3'] = 0
        header['CRVAL3'] = float(self.target.lat)*180/np.pi # Degrees
        header['CDELT3'] = 1.0
        dateobs = self.site.date.tuple()
        YYYY=str(dateobs[0]); MM=str(dateobs[1]); DD=str(dateobs[2]); hh = str(dateobs[3]); mm=str(dateobs[4]); ss=str(round(dateobs[5]))
        header['DATE-OBS'] = YYYY.zfill(4)+'-'+MM.zfill(2)+'-'+DD.zfill(2)+'T'+hh.zfill(2)+':'+mm.zfill(2)+':'+ss.zfill(2)
        datemade = ephem.now().tuple()
        YYYY=str(datemade[0]); MM=str(datemade[1]); DD=str(datemade[2]); hh = str(datemade[3]); mm=str(datemade[4]); ss=str(round(datemade[5]))
        header['DATE'] = YYYY.zfill(4)+'-'+MM.zfill(2)+'-'+DD.zfill(2)+'T'+hh.zfill(2)+':'+mm.zfill(2)+':'+ss.zfill(2)
        header['ORIGIN'] = 'ONSALA, SWEDEN'
        header['TELESCOP'] = 'SALSA 2m'
        header['INSTRUME'] = self.config.get('SITE', 'name')
        header['OBSTIME'] = self.int_time
        header['OBSERVER'] = self.observer
        #header['OBJECT'] = 'Milky Way'
        #eq = self.target.epoch.triple()
        #header['EQUINOX'] = str(eq[0] + eq[1]/12.0 + eq[2]/(24*12.0)) # Epoch in decimal years.
        header['EQUINOX'] = 2000
        header['BUNIT']  = 'K'
        header['DATAMAX']  = np.max(self.data)
        header['DATAMIN']  = np.min(self.data)
        #header['LINE'] = 'HI(21CM)'           
        header['AZIMUTH'] = self.az # Degrees
        header['ELEVATIO'] = self.alt # Degrees
        header['INTTIME'] = self.int_time
        try:
            os.remove(outfile)
        except OSError:
            pass
        # Include dummy indices to get glon, glat coordinates correct in 
        # FITS header, else pyfits will overwrite naxis to 1.
        hdu = fits.PrimaryHDU(data = self.data.reshape(1, 1, self.nchans).astype(np.int16), header = header)
        hdulist = fits.HDUList([hdu])
        hdulist.writeto(outfile)

    def upload_to_archive(self, fitsfile, pngfile, txtfile):
        host = self.config.get('ARCHIVE', 'host')
        db = self.config.get('ARCHIVE', 'database')
        user = self.config.get('ARCHIVE', 'user')
        passwd = self.config.get('ARCHIVE', 'password')
        table = self.config.get('ARCHIVE', 'table')
        con=mdb.connect(host = host, passwd=passwd, db=db, user = user)
        # Read fitsdata
        f_fits = open(fitsfile, 'rb')
        fitsdata = f_fits.read()
        f_fits.close()

        f_png = open(pngfile, 'rb')
        pngdata = f_png.read()
        f_png.close()
        
        f_txt = open(txtfile, 'rb')
        txtdata = f_txt.read()
        f_txt.close()

        # Insert to database
        with con:
            cur = con.cursor()
            mysqlcmd = "INSERT INTO " + table + " SET file_fits=\'{0}\'".format(con.escape_string(fitsdata)) + ","
            mysqlcmd = mysqlcmd + "observer=\'" + self.observer + "\',"
            pos = ephem.Galactic(self.target)
            glon = str(pos.lon)
            glat = str(pos.lat)
            mysqlcmd = mysqlcmd + "glon=\'" + con.escape_string(glon) + "\',"
            mysqlcmd = mysqlcmd + "glat=\'" + con.escape_string(glat) + "\',"
            unixtime_sec = math.floor((self.site.date.datetime() - datetime(1970, 1, 1)).total_seconds())
            mysqlcmd = mysqlcmd + "obsdate="+ str(unixtime_sec) + ","
            mysqlcmd = mysqlcmd + "obsfreq=" + str(1e-6*self.obs_freq)+ ","
            mysqlcmd = mysqlcmd + "bandwidth=" + str(1e-6*self.bandwidth) + ","
            mysqlcmd = mysqlcmd + "int_time=" + str(self.int_time) + ","
            mysqlcmd = mysqlcmd + "telescope=\'" + self.site.name + "\',"
            mysqlcmd = mysqlcmd + "file_png=\'{0}\'".format(con.escape_string(pngdata)) + ","
            mysqlcmd = mysqlcmd + "file_txt=\'{0}\'".format(con.escape_string(txtdata))
            cur.execute(mysqlcmd)
        con.close()
        self.uploaded = True

    def get_total_power(self):
        # Calculate total power (sum of values in spectra divided by number of channels)
        # Use only inner 75% to avoid band edge effects
        nchans = self.nchans
        totpow = np.sum(self.data[0.25*nchans:0.75*nchans]) / (0.5*nchans)
        return totpow

    def print_total_power(self):
        print "SPECTRUM INFO: Offset_alt={0} deg. Offset_az={1} deg. Total power = {2}".format(self.offset_alt, self.offset_az, round(self.get_total_power(),4))
