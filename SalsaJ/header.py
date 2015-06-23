import sys
import astropy.io.fits as fits

data, header = fits.getdata(sys.argv[1], header=True)

print repr(header)
