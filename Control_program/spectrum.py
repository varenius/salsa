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
    def __init__(self, data, bandwidth, nchans, cfreq, site, alt, az, int_time, username, config, offset_alt, offset_az, coordsys, satellite = ""):
        # All units shall be S.I. (Hz, etc. not MHz)
        self.rest_freq = 1420.40575177e6 # Hz, from Wiki.
        self.obs_freq = float(cfreq)
        self.data = data[:]
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
        self.pointing = ephem.FixedBody()
        self.pointing._ra = ra
        self.pointing._dec = dec
        self.pointing._epoch = ephem.now()
        # NOTE: This will not be true for a long measurement
        self.pointing.compute(self.site)
        pos = ephem.Galactic(self.pointing)
        self.glon = pos.lon
        self.glat = pos.lat
        # Check what we are observing
        if coordsys == "Galactic":
            coord1 = str(round(float(repr(self.glon))*180/np.pi,1))
            coord2 = str(round(float(repr(self.glat))*180/np.pi,1))
            self.target = 'Galactic long=' + coord1 + ', lat=' + coord2
        elif coordsys == "GNSS":
            self.target = 'GNSS ' + satellite + ' (alt={:6.1f}, az={:6.1f})'.format(self.alt, self.az)
        elif coordsys == "The Sun":
            self.target = 'The Sun (alt={:6.1f}, az={:6.1f})'.format(self.alt, self.az)
        elif coordsys == "The Moon":
            self.target = 'The Moon (alt={:6.1f}, az={:6.1f})'.format(self.alt, self.az)
        elif coordsys == "Cas A":
            self.target = 'Cas A (alt={:6.1f}, az={:6.1f})'.format(self.alt, self.az)
        else:
            self.target = 'Obs. at alt={:6.1f}, az={:6.1f}'.format(self.alt, self.az)

        self.observer = username
        self.uploaded = False
        self.freq_vlsr_corr = 0
        self.vlsr_corr = 0
        self.config = config
        self.offset_alt = offset_alt
        self.offset_az = offset_az

    def auto_edit_bad_data(self):
        print("Autoflagging known RFI.")
        # Remove spikes at end channels
        self.data[0:1] = self.data[2]
        self.data[-2:] = self.data[-3]
        freq_res = self.bandwidth/self.nchans # Hz
        # List known RFI as center-frequency in MHz, and width in Mhz
        # This list contains peaks which are not properly picked by by the MWF filter.
        known_RFI = [[1420.4+4.595, 0.02],
                     [1420.4-0.392, 0.02],
                     [1420.4+0.022, 0.02],
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
        # Filter away rest of RFI with median window filter, assuming 4096 channels for 2MHz bandwidth
        self.data = signal.medfilt(self.data, kernel_size = 7)

    # NOT USED ANYMORE, replaced by median window filter function
    #def auto_edit_bad_data_OLD(self):
    #    #print "Autoflagging known RFI."
    #    freq_res = self.bandwidth/self.nchans # Hz
    #    # List known RFI as center-frequency in MHz, and width in Mhz
    #    known_RFI = [[1419.4-0.210, 0.02], 
    #                 [1419.4-1.937, 0.015], 
    #                 [1419.4-4.4, 0.015], 
    #                 [1419.4+3.0, 0.01], 
    #                 # remove dip in the center of band
    #                 [self.obs_freq*1e-6, 0.02], 
    #                 [1416.4-0.8, 0.04],
    #                 [1420.4-2, 0.01],
    #                 [1425, 0.01],
    #                 [1424.4-1.8, 0.01],
    #                 [1424.4+0.5845, 0.01],
    #                 [1424.4+0.483, 0.005],
    #                 [1420.4-1.38, 0.01],
    #                 [1420.4-1.042, 0.01],
    #                 [1424.4+0.61, 0.03],
    #                 [1420.4-0.3965, 0.005],
    #                 [1420.4+0.4465, 0.005],
    #                 [1420.4+3.405, 0.01],
    #                 [1420.4+4.299, 0.02],
    #                 [1420.4+4.61, 0.06],
    #                 [1420.4+4.67, 0.02],
    #                 [1420.4-3.197, 0.04],
    #                 [1420.4-2.39, 0.04],
    #                 [1420.4-0.395, 0.02],
    #                 [1420.4+6.21, 0.04],
    #                 [1420.4+4.535, 0.003],
    #                 [1420.4-0.38, 0.01],
    #                 [1420.4-0.209, 0.005],
    #                 [1420.4-0.084, 0.005],
    #                 [1420.4-0.523, 0.005],
    #                 [1420.4+4.56, 0.02],
    #                 ]
    #    for item in known_RFI:
    #        RFI_freq = item[0] *1e6 
    #        RFI_width = item[1]*1e6
    #        ch0_freq = self.obs_freq - 0.5*self.bandwidth
    #        ind_low = int(np.floor((RFI_freq-0.5*RFI_width - ch0_freq)/freq_res))
    #        ind_high = int(np.ceil((RFI_freq+0.5*RFI_width - ch0_freq)/freq_res))
    #        #print ind_low, ind_high
    #        if ind_low>0 and ind_high<self.nchans:
    #            #print 'Flagging', item
    #            margin = min(ind_high-ind_low, ind_low, self.nchans-ind_high)
    #            RFI_part = self.data[ind_low-margin:ind_high+margin]
    #            xdata = np.arange(len(RFI_part))
    #            weights = np.ones_like(RFI_part)
    #            weights[margin:-margin] = 0.0 # Ignore RFI when fitting
    #            pf = np.polyfit(xdata, RFI_part, deg=1, w=weights)
    #            interpdata = np.polyval(pf, xdata)
    #            self.data[ind_low:ind_high] = interpdata[margin:-margin]
    #        else:
    #            #print 'Skipping', item
    #            pass

    def shift_to_vlsr_frame(self):
        # From http://web.mit.edu/8.13/www/nsrt_software/documentation/vlsr.pdf
        ep_target = ephem.Equatorial(self.pointing)
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
        self.data = signal.decimate(self.data, int(self.nchans/outchans), axis=0, ftype = 'fir')
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
            date = YYYY.zfill(4)+'-'+MM.zfill(2)+'-'+DD.zfill(2)+'T'+hh.zfill(2)+':'+mm.zfill(2)+':'+ss.zfill(4)
            text_file.write("# DATE=" + date + "\n")
            text_file.write("# GLON and GLAT given in degrees\n")
            text_file.write("# GLON={0}\n".format(float(self.glon)*180/np.pi)) # Degrees
            text_file.write("# GLAT={0}\n".format(float(self.glat)*180/np.pi)) # Degrees
            text_file.write("# DATA in two columns below. Col. 1 is velocity relative to LSR [km/s]. Col. 2 is uncalibrated antenna temperature [K].\n")
            text_file.write("# ENDHEADER\n")
            for i, datum in enumerate(data):
                text_file.write("{0} {1}\n".format(vels[i], data[i]))

    def save_to_fits(self, outfile):
        # Instructions for writing FITS at https://python4astronomers.github.io/astropy/fits.html
        # Set of keywords chosen to match SalsaJ requirements.
        hdu = fits.PrimaryHDU()
        datamin = np.min(self.data)
        datamax = np.max(self.data)
        glon = float(self.glon)*180/np.pi # degrees
        glat = float(self.glat)*180/np.pi # degrees

        #Since using  int16 as datatype we use bscale and bzero to keep dynamic range. 
        # SalsaJ cannot read bitpix correctly except 16 bit. If SalsaJ could read bitpix, we could just have BITPIX -64 and skip Bscale, Bzero, i.e. just remove 
        # astype above.
        bscale = (datamax-datamin)/65534.0
        bzero = datamin+bscale*32767.0
        #hdu.header['BLANK']  = -32768
        scaledata = (self.data - bzero)/bscale
        hdu.data = scaledata.reshape(1, 1, self.nchans).astype(np.int16) # 16 bit for SalsaJ
        hdu.header['BSCALE']  = bscale
        hdu.header['BZERO']  = bzero
        hdu.header['BUNIT']  = 'K'
        hdu.header['CTYPE1'] = 'FREQ'
        hdu.header['CRPIX1'] = self.nchans/2 # number of channels
        hdu.header['CRVAL1'] = self.obs_freq
        hdu.header['CDELT1'] = self.bandwidth/self.nchans # Channel width
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
        hdu.header['RESTFREQ'] = self.rest_freq # Rest frequency of line
        hdu.header['VELO-LSR'] = (-1)*self.vlsr_corr/1000.0 # in km/s, sign as needed by SalsaJ
        hdu.header['VLSRUNIT']= 'km/s'
        dateobs = self.site.date.tuple()
        YYYY=str(dateobs[0]); MM=str(dateobs[1]); DD=str(dateobs[2]); hh = str(dateobs[3]); mm=str(dateobs[4]); ss=str(round(dateobs[5]))
        hdu.header['DATE-OBS'] = YYYY.zfill(4)+'-'+MM.zfill(2)+'-'+DD.zfill(2)+'T'+hh.zfill(2)+':'+mm.zfill(2)+':'+ss.zfill(4)
        datemade = ephem.now().tuple()
        YYYY=str(datemade[0]); MM=str(datemade[1]); DD=str(datemade[2]); hh = str(datemade[3]); mm=str(datemade[4]); ss=str(round(datemade[5]))
        hdu.header['DATE'] = YYYY.zfill(4)+'-'+MM.zfill(2)+'-'+DD.zfill(2)+'T'+hh.zfill(2)+':'+mm.zfill(2)+':'+ss.zfill(4)
        hdu.header['ORIGIN'] = 'ONSALA, SWEDEN'
        hdu.header['INSTRUME'] = self.config.get('SITE', 'name')
        hdu.header['OBSTIME'] = self.int_time
        hdu.header['OBSERVER'] = self.observer
        #header['OBJECT'] = 'Milky Way'
        #eq = self.target.epoch.triple()
        #header['EQUINOX'] = str(eq[0] + eq[1]/12.0 + eq[2]/(24*12.0)) # Epoch in decimal years.
        hdu.header['EQUINOX'] = 2000
        #hdu.header['DATAMAX']  = datamax
        #hdu.header['DATAMIN']  = datamin
        #header['LINE'] = 'HI(21CM)'           
        hdu.header['AZIMUTH'] = self.az # Degrees
        hdu.header['ELEVATIO'] = self.alt # Degrees
        hdu.header['INTTIME'] = self.int_time
        try:
            os.remove(outfile)
        except OSError:
            pass
        hdu.writeto(outfile)

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
            mysqlcmd = "INSERT INTO ".encode() + table.encode() + " SET file_fits=\'".encode() + con.escape_string(fitsdata) + "\',".encode()
            mysqlcmd = mysqlcmd + "observer=\'".encode() + self.observer.encode() + "\',".encode()
            glon = str(self.glon)
            glat = str(self.glat)
            mysqlcmd = mysqlcmd + "glon=\'".encode() + con.escape_string(glon) + "\',".encode()
            mysqlcmd = mysqlcmd + "glat=\'".encode() + con.escape_string(glat) + "\',".encode()
            unixtime_sec = math.floor((self.site.date.datetime() - datetime(1970, 1, 1)).total_seconds())
            mysqlcmd = mysqlcmd + "obsdate=".encode()+ str(unixtime_sec).encode() + ",".encode()
            mysqlcmd = mysqlcmd + "obsfreq=".encode() + str(1e-6*self.obs_freq).encode()+ ",".encode()
            mysqlcmd = mysqlcmd + "bandwidth=".encode() + str(1e-6*self.bandwidth).encode() + ",".encode()
            mysqlcmd = mysqlcmd + "int_time=".encode() + str(self.int_time).encode() + ",".encode()
            mysqlcmd = mysqlcmd + "telescope=\'".encode() + self.site.name.encode() + "\',".encode()
            mysqlcmd = mysqlcmd + "file_png=\'".encode() + con.escape_string(pngdata) + "\'".encode() + ",".encode()
            mysqlcmd = mysqlcmd + "file_txt=\'".encode() + con.escape_string(txtdata) + "\'".encode()
            cur.execute(mysqlcmd)
        self.uploaded = True

    def get_total_power(self):
        # Calculate total power (sum of values in spectra divided by number of channels)
        # Use only inner 75% to avoid band edge effects
        nchans = self.nchans
        totpow = np.sum(self.data[int(0.25*nchans):int(0.75*nchans)]) / (0.5*nchans)
        return totpow

    def print_total_power(self):
        #print "SPECTRUM INFO: Offset_alt={0} deg. Offset_az={1} deg. Total power = {2}".format(self.offset_alt, self.offset_az, round(self.get_total_power(),4))
        print("SPECTRUM INFO: Offset_alt={:6.1f} deg. Offset_az={:6.1f} deg. Total power = {:10.3f}, alt={:6.1f}, az={:6.1f}".format(self.offset_alt, self.offset_az, round(self.get_total_power(),4), self.alt, self.az))
