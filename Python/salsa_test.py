import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pyfits

# The serial numbers of our spectra
ids = range(1909, 1937+1)
ns = len(ids)

# Empty matrices for data and frequency vectors, one column per spectrum.
freq = np.zeros((256,ns))
data = np.zeros((256,ns))

# Create an empty data frame, one line per spectrum.
head = pd.DataFrame({'LII':[0.0]*ns, 'BII':[0.0]*ns, 'f0':[0.0]*ns, 'v_lsr':[0.0]*ns, 'dt':[0.0]*ns})

MHz = 1.0e6           # define a MHz in Hz
c_kms = 2.99792458e5  # the speed of light in km/s

# Loop over FITS files
for i in ids:
    fitsfile = "FITS/spectrum_%d.fits" % (i)
    print(fitsfile)
    hdulist = pyfits.open(fitsfile)
    hdr = hdulist[0].header
    ic = i-ids[0]
    off = np.arange(hdr['NAXIS1'])+1-hdr['CRPIX1']
    freq[:,ic] = (hdr['CRVAL1']+off)/MHz
    bzero = hdr['BZERO']
    bscale = hdr['BSCALE']
    d = hdulist[0].data[0,0,:]*bscale+bzero
    data[:,ic] = d
    onx = hdr['CRVAL2']
    ony = hdr['CRVAL3']
    dt = hdr['OBSTIME']
    f0 = hdr['CRVAL1']/MHz
    fr = hdr['RESTFREQ']/MHz
    df = hdr['CDELT1']
    vs = hdr['VELO-LSR']
    tstamp = hdr['DATE-OBS']
    head['LII'][ic] = onx
    head['BII'][ic] = ony
    head['f0'][ic] = f0
    head['v_lsr'][ic] = vs
    head['dt'][ic] = dt

# Print data frame, sorted by galactic longitude
print(head.sort_values('LII'))

# Plot spectra, offsetting each one by 10 K in order to get a stacked picture
dT = 0.0
for i in head.sort_values('LII').index:
    dv = -df/head['f0'][i]*c_kms/MHz
    v = dv*off-vs
    d = data[:,i] + dT
    plt.plot(v, d)
    plt.xlabel("velocity [km/s]")
    dT = dT + 10.0
    
plt.grid(True)
plt.show()
