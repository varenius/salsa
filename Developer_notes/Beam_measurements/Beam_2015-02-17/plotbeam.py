import matplotlib.pyplot as plt
import sys
from scipy.optimize import curve_fit
import numpy as np

# alaz files
try:
    alfile = sys.argv[1]
    azfile = sys.argv[2]
except IndexError:
    print 'Usage: python plotbeam.py alfile azfile'
    print 'Will then use offsets and power values in both files to fit and plot beam.'
    sys.exit()
# The offset values in Az given to the telescope. Note that 
# This does not necesarily mean that the telescope was pointing in this 
# direction, since it might not move if the difference is too small.
aldata = []
lines = [line.strip() for line in open(alfile)]
for line in lines:
    ldata = line.split()
    loff = float(ldata[2].split('=')[1])
    lamp = float(ldata[9])
    aldata.append([loff, lamp])
aldata = np.array(aldata)
aloffset = aldata[:,0] # offset
alamp = aldata[:,1] # Measured total power
# remove zero level
alamp = alamp -min(alamp)

azdata = []
lines = [line.strip() for line in open(azfile)]
for line in lines:
    ldata = line.split()
    loff = float(ldata[4].split('=')[1])
    lamp = float(ldata[9])
    azdata.append([loff, lamp])
azdata = np.array(azdata)
azoffset = azdata[:,0] # offset
azamp = azdata[:,1] # Measured total power
# remove zero level
azamp = azamp -min(azamp)

# Define model function to be used to fit to the data above:
def gauss(x, *p):
    A, mu, sigma= p
    return A*np.exp(-(x-mu)**2/(2.*sigma**2))

# Plot ALTITUDE
# p0 is the initial guess for the fitting coefficients (A, mu and sigma above)
p0 = [1., 0., 0.1]
fres, var_matrix = curve_fit(gauss, aloffset, alamp, p0=p0)
#Make nice grid for fitted data
fitx = np.linspace(min(aloffset), max(aloffset), 500)
# Get the fitted curve
ffit = gauss(fitx, *fres)
fsigma = fres[2]
fmu = fres[1]
fbeam = 2.355*fsigma # FWHM
print 'Fitted FWHM=' + str(round(fbeam,1)) + 'deg.' + ', AL offset = ' + str(round(fmu,6))
plt.figure()
plt.plot(aloffset, alamp, '*')
plt.plot(fitx, ffit)
plt.title('Beam measurements of SALSA-Vale at 1410MHz. \nFitted FWHM=' + str(round(fbeam,2)) + '$^\circ$' + ', offset = ' + str(round(fmu,4)) + '$^\circ$')
plt.ylabel('Continuum intensity [arbitrary units]')
plt.xlabel('AL offset relative to the Sun [degrees]')
plt.legend(['Measurements', 'Fitted Gaussian'])

# PLOT AZIMUTH
# p0 is the initial guess for the fitting coefficients (A, mu and sigma above)
p0 = [1., 0., 0.1]
fres, var_matrix = curve_fit(gauss, azoffset, azamp, p0=p0)
#Make nice grid for fitted data
fitx = np.linspace(min(azoffset), max(azoffset), 500)
# Get the fitted curve
ffit = gauss(fitx, *fres)
fsigma = fres[2]
fmu = fres[1]
fbeam = 2.355*fsigma # FWHM
print 'Fitted FWHM=' + str(round(fbeam,1)) + 'deg.' + ', AZ offset = ' + str(round(fmu,6))
plt.figure()
plt.plot(azoffset, azamp, '*')
plt.plot(fitx, ffit)
plt.title('Beam measurements of SALSA-Vale at 1410MHz. \nFitted FWHM=' + str(round(fbeam,2)) + '$^\circ$' + ', offset = ' + str(round(fmu,4)) + '$^\circ$')
plt.ylabel('Continuum intensity [arbitrary units]')
plt.xlabel('AZ offset relative to the Sun [degrees]')
plt.legend(['Measurements', 'Fitted Gaussian'])

plt.tight_layout()
## SINC FITTING
#def sincSquare_mod(x, A, mu, sigma):
#    x=np.array(x)
#    return A * (np.sin(np.pi*(x[:]-mu)*sigma) / (np.pi*(x[:]-mu)*sigma))**2
#
## p0 is the initial guess for the fitting coefficients (A, mu and sigma above)
#p0 = [1., 0., 0.1]
#
#fres, var_matrix = curve_fit(sincSquare_mod, xdata, fdata, p0=p0)
#
##Make nice grid for fitted data
#fitx = np.linspace(min(xdata), max(xdata), 500)
#
## Get the fitted curve
#ffit = sincSquare_mod(fitx, *fres)
#
#fsigma = fres[2]
#
#fmu = fres[1]
#
#fbeam = 2.355*fsigma # FWHM
#plt.figure()
#plt.plot(xdata, fdata, '*')
#plt.plot(fitx, ffit)
#plt.title('Sinc fit')
plt.show()
