import ephem
import numpy as np

#Input galactic coordinates: This is the position we want to observe.
glon = 80 # degrees
glat = 0 # degrees

# Define where you are. CHANGE IF NEEDED.
site = ephem.Observer()
site.date = ephem.now()
site.lat = '57:23:45' # ONSALA, SWEDEN
site.long = '11:55:34' # ONSALA, SWEDEN
site.elevation = 2 # ONSALA, SWEDEN, meters over the sea
site.pressure = 0 # Do not correct for atmospheric refraction

# Use the "ephem" module to convert from 
# galactic to local coordinates. 
# Note that ephem works in radians internally, 
# so we need to convert our galactic coordinates 
# from degrees to radians by multiplication with pi/180.
eqpos = ephem.Galactic(glon*np.pi/180.0,glat*np.pi/180.0)
eqpos = ephem.Equatorial(eqpos)
pos = ephem.FixedBody()
pos._ra = eqpos.ra
pos._dec = eqpos.dec
pos._epoch = eqpos.epoch
site.date = ephem.now()
pos.compute(site)

# Convert back from radians to degrees
alt_deg = float(pos.alt)*180.0/np.pi
az_deg = float(pos.az)*180.0/np.pi

# Print result
msg = 'Galactic coordinates glon=' + str(glon) + \
      ', glat='+str(glat) + ' is right now at local azimuth=' + \
      str(round(az_deg,2)) + 'deg, altitude=' + str(round(alt_deg,2)) + 'deg.'
print msg


