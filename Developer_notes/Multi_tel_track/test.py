import ephem
import math
import configparser

class MD01():
    def __init__(self):
        configfile = "conf/vale.conf"
        # Set config file location
        config = configparser.ConfigParser()
        config.read(configfile)
        # Read telescope position details
        self.site = ephem.Observer()
        self.site.date = ephem.now()
        self.site.lat = ephem.degrees(config.get('SITE', 'latitude'))
        self.site.long = ephem.degrees(config.get('SITE', 'longitude'))
        self.site.elevation = config.getfloat('SITE', 'elevation')
        self.site.pressure = 0 # Do not correct for atmospheric refraction
        self.site.name = config.get('SITE', 'name')
    
    def get_desired_alaz(self, target):
        self.site.date = ephem.now()
        # Assume target is list, first is ID, second and third are coordinate values
        if target[0] == 'SUN':
            pos = ephem.Sun()
            pos.compute(self.site) # Needed for the sun since depending on time
        elif target[0] == 'GAL':
            pos = ephem.Galactic(ephem.degrees(str(target[1])), ephem.degrees(str(target[2])))
        # Calculate alt, az, via fixedbody since only fixed body has alt, az
        # First needs to make sure we have equatorial coordinates
        eqpos = ephem.Equatorial(pos)
        fixedbody = ephem.FixedBody()
        fixedbody._ra = eqpos.ra
        fixedbody._dec = eqpos.dec
        fixedbody._epoch = eqpos.epoch
        fixedbody.compute(self.site)
        alt = fixedbody.alt
        az = fixedbody.az
        alt_deg = float(alt)*180.0/math.pi
        az_deg = float(az)*180.0/math.pi
        print("\n NEW: \n")
        print(pos.lon, pos.lat)
        print(target[1], target[2])
        return round(alt_deg,3), round(az_deg,3)

tel = MD01()
tel.get_desired_alaz(["GAL", 100.01, 0])
#tel.get_desired_alaz(["SUN", 0, 0])
