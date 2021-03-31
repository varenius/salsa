# Functions coping with GNSS tracking for SALSA

import configparser
import ephem
import TLEephem
import os 
import sys
import math

sys.path.append('./')

# Load the config file
abspath = os.path.abspath(__file__)
configfile = os.path.dirname(abspath) + '/SALSA.config'
if not os.path.exists(configfile):
    print("Config file not found at" + configfile)
    print("Exiting...")
    sys.exit(1)

config=configparser.ConfigParser()
config.read(configfile)

# Get site coordinates
lat = ephem.degrees(config.get('SITE', 'latitude'))
lon = ephem.degrees(config.get('SITE', 'longitude'))
h = config.getfloat('SITE', 'elevation')

# load TLE files
TLEdir=config.get('TLE','tledir_name')
tleEphem=TLEephem.TLEephem(TLEdir, config)
tleEphem.SetObserver(lat,lon,h)

def SatCompute(visibility, constellation):
    """
    Provides a list of available satellites and their position over the local horizon in polar coordinates
    Args:
	visibility:
	    'visible' or 'VISIBLE' - get a list of satellites visible over the local horizon
	    'all'     or 'ALL'     - get a list of all satellites
	constellation:
	     'all' or 'ALL' - all constellations
	     'GPS'         - GPS satellites only
	     'GSAT'        - GALILEO satellites only
	     'COSMOS'      - GLONASS satellites only
	     'BEIDOU'      - BEIDOU satellites only
   Returns:
	GNSSname - list of satellites' names 
	phi      - list of polar coordinates: angle
	r        - list of polar coordinates: distance
    """

    if visibility =='visible' or visibility == 'VISIBLE' : GNSSAzEl=tleEphem.ComputeAzEl(constellation,True)
    if visibility=='all' or visibility == 'ALL' : GNSSAzEl=tleEphem.ComputeAzEl(constellation)
    n=len(GNSSAzEl)
    GNSSname=GNSSAzEl[0:n:3]
    az=GNSSAzEl[1:n:3]
    el=GNSSAzEl[2:n:3]
    x=[]
    y=[]
    r=[]
    phi=[]
    for i in range(0,len(az)):
        az[i]*=math.pi/180.0
        el[i]*=math.pi/180.0
        x.append(-1*(math.pi/2-abs(el[i]))/(math.pi/2)*math.cos(az[i]-math.pi/2))
        y.append(-1*(math.pi/2-abs(el[i]))/(math.pi/2)*math.sin(az[i]-math.pi/2))
        r.append(math.sqrt(x[i]**2+y[i]**2)*90)
        phi.append(math.atan2(y[i],x[i])-0.5*math.pi)

    return GNSSname,phi,r


def SatComputeAzElSingle(satName):
	"""
	Computes Azimuth and Elevation angles for a given satellite
    	Args:
		satName - name of the requested satellite
   	Returns:
		Azimuth   - in degrees
		Elevation - in degrees
	"""
	return tleEphem.ComputeAzElSingle(satName)
