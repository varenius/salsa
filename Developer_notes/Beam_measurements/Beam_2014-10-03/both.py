import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy as np
# The offset values in Az given to the telescope. Note that 
# This does not necesarily mean that the telescope was pointing in this 
# direction, since it might not move if the difference is too small.
xdata = [
-10,
-9,
-8,
-7,
-6,
-5,
-4,
-3,
-2,
-1,
0,
1,
2,
3,
4,
5,
6,
7,
8,
9,
10,
]

# First I was measuring following the motion of the sun, i.e.
# increasing in Azimuth. This means that while measuring, the sun will move
# towards a higher az value. Here I was starting with -5 deg offset and moving to 5 deg
fdata = [
523.1025,
532.3567,
513.7081,
467.7899,
444.9493,
494.3307,
715.9436,
965.5539,
1199.073,
1391.0013,
1409.8726,
1236.3143,
1014.0361,
752.7029,
554.2451,
468.1915,
443.3187,
460.7711,
470.8325,
468.2912,
446.9268,
]

# Here I was measuring backwards, i.e. starting with the 5 deg offset and moving to -5
bdata = [
525.58,
526.467,
502.3903,
493.7022,
466.8653,
455.9669,
700.1087,
726.7405,
1197.4687,
1244.8659,
1383.362,
1387.2706,
1191.3525,
963.2498,
710.7194,
545.1701,
442.9739,
435.6519,
455.3411,
472.3609,
449.0051,
]

# remove continuum
fdata = np.array(fdata)-500
bdata = np.array(bdata)-500

# Define model function to be used to fit to the data above:
def gauss(x, *p):
    A, mu, sigma= p
    return A*np.exp(-(x-mu)**2/(2.*sigma**2))

# p0 is the initial guess for the fitting coefficients (A, mu and sigma above)
p0 = [1., 0., 0.1]

fres, var_matrix = curve_fit(gauss, xdata, fdata, p0=p0)
bres, var_matrix = curve_fit(gauss, xdata, bdata, p0=p0)

#Make nice grid for fitted data
fitx = np.linspace(min(xdata), max(xdata), 100)

# Get the fitted curve
ffit = gauss(fitx, *fres)
bfit = gauss(fitx, *bres)

fsigma = fres[2]
bsigma = bres[2]

fmu = fres[1]
bmu = bres[1]

fbeam = 2.355*fsigma # FWHM
bbeam = 2.355*bsigma # FWHM


plt.plot(xdata, fdata, '*')
plt.plot(fitx, ffit)
plt.title('Minus to plus: FWHM=' + str(round(fbeam,1)) + '$^\circ$' + 'offset = ' + str(round(fmu,1)) + '$^\circ$')
plt.figure()
plt.plot(xdata, bdata, '*')
plt.plot(fitx, bfit)
plt.title('Plus to minus: FWHM=' + str(round(bbeam,1)) + '$^\circ$' + 'offset = ' + str(round(bmu,1)) + '$^\circ$')
plt.show()
