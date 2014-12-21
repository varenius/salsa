import ephem
import numpy as np

# Define where you are. CHANGE IF NEEDED.
site = ephem.Observer()
site.date = ephem.now()
site.lat = '57:23:45' # ONSALA, SWEDEN
site.long = '11:55:34' # ONSALA, SWEDEN
site.elevation = 2 # ONSALA, SWEDEN, meters over the sea
site.pressure = 0 # Do not correct for atmospheric refraction

# Use the "ephem" module to calcualte
# the position of the sun
sun = ephem.Sun()
site.date = ephem.now()
sun.compute(site)

# Convert back from radians to degrees
alt_deg = float(sun.alt)*180.0/np.pi
az_deg = float(sun.az)*180.0/np.pi

# Print result
msg = 'The sun is right now at local azimuth=' + \
      str(round(az_deg,2)) + 'deg, altitude=' + str(round(alt_deg,2)) + 'deg.'
print msg
