import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy as np
# The offset values in Az given to the telescope. Note that 
# This does not necesarily mean that the telescope was pointing in this 
# direction, since it might not move if the difference is too small.
xdata = [
-20,
-19,
-18,
-17,
-16,
-15,
-14,
-13,
-12,
-11,
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
11,
12,
13,
14,
15,
16,
17,
18,
19,
20,
]

# First I was measuring following the motion of the sun, i.e.
# increasing in Azimuth. This means that while measuring, the sun will move
# towards a higher az value. Here I was starting with -5 deg offset and moving to 5 deg
fdata = [
426.4892,
417.2378,
413.5343,
410.8377,
409.7647,
408.9738,
415.0654,
427.2815,
473.5249,
519.086,
549.9259,
557.2949,
522.2085,
468.8787,
445.6153,
522.589,
718.6798,
988.6602,
1328.0975,
1566.2021,
1605.5733,
1426.0575,
1136.0245,
861.9328,
627.0873,
485.5463,
459.839,
474.4248,
498.8185,
500.2032,
477.1168,
453.2831,
431.5507,
418.0383,
415.3673,
413.91,
411.7411,
410.3259,
411.06,
414.6461,
417.4226,
]

# remove continuum
fdata = np.array(fdata)-min(fdata)

# Define model function to be used to fit to the data above:
def gauss(x, *p):
    A, mu, sigma= p
    return A*np.exp(-(x-mu)**2/(2.*sigma**2))

# p0 is the initial guess for the fitting coefficients (A, mu and sigma above)
p0 = [1., 0., 0.1]

fres, var_matrix = curve_fit(gauss, xdata, fdata, p0=p0)

#Make nice grid for fitted data
fitx = np.linspace(min(xdata), max(xdata), 500)

# Get the fitted curve
ffit = gauss(fitx, *fres)

fsigma = fres[2]

fmu = fres[1]

fbeam = 2.355*fsigma # FWHM

plt.plot(xdata, fdata, '*')
plt.plot(fitx, ffit)
plt.title('Beam measurements of SALSA-Vale 2014-10-03 at 1410MHz. Fitted FWHM=' + str(round(fbeam,1)) + '$^\circ$' + ', offset = ' + str(round(fmu,1)) + '$^\circ$')
plt.ylabel('Continuum intensity [arbitrary units]')
plt.xlabel('Azimuth offset relative to the Sun [degrees]')
plt.legend(['Measurements', 'Fitted Gaussian'])

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
