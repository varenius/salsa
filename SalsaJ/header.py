#Simple python script to show the header of a FITS file, used when debugging SalsaJ
import sys
import astropy.io.fits as fits

data, header = fits.getdata(sys.argv[1], header=True)

print repr(header)
