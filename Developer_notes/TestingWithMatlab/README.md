This folder contains some FITS files taken with SALSA in december 2014. 
Included are also three Matlab script files:
- batch_fit.m: This file can be used to run semi-automatic interactive fitting
               of the FITS files to extract velocities and save to an output file.
- rotcurve.m: This file can be used to read the file produced by batch_fit and 
              make a rotation curve.
- map.m: This file can be used, assuming a flat rotation curve, to make
         a map of the Milky Way from the output data produced by batch_fit.
		 Note tht this script does not resolve distance ambiguities, i.e.
		 directions in quadrant 1 (or 4) where two solutions are possible.
		 In these cases, both solutions are plotted with different colors.
