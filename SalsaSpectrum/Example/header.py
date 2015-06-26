#Simple python script to show the header of a FITS file, used when debugging SalsaJ
import sys
import astropy.io.fits as fits
import numpy as np

data, header = fits.getdata(sys.argv[1], header=True)

print repr(header)
print np.min(data), np.max(data)
print data
