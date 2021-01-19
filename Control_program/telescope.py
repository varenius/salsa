import socket
import time
import ephem
import numpy as np

class TelescopeController:
    """ Provides functions to communicate with the MD01 telescope driver
    device. Communication via telnet using python socket. """

    def __init__(self, config):
        """ Creates a new object with a connection to driver."""
        # Create connection to MD01
        self.host = config.get('MD01', 'host')
        self.port = config.getint('MD01', 'port')
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.site = ephem.Observer()
        self.site.date = ephem.now()
        self.site.lat = ephem.degrees(config.get('SITE', 'latitude'))
        self.site.long = ephem.degrees(config.get('SITE', 'longitude'))
        self.site.elevation = config.getfloat('SITE', 'elevation')
        self.site.pressure = 0 # Do not correct for atmospheric refraction
        self.site.name = config.get('SITE', 'name')
        
        # Read stow position from config file
        self.stowal_deg = config.getfloat('MD01', 'stowal')
        self.stowaz_deg = config.getfloat('MD01', 'stowaz')

        self.close_enough_distance = config.getfloat('MD01', 'close_enough')
            
        self.target_alaz = (45, 45)

        ## Make sure Noise Diode is turned off until implemented in GUI etc.
        #self.set_noise_diode(False)

    def set_noise_diode(self, status):
        pass

    def reset(self):
        pass

    def stop(self):
        """Stops any movement of the telescope """
        #Format status request message as bytes
        msg = bytes.fromhex("57000000000000000000000F20")
        # Send message
        self.socket.send(msg)
        # Read response from MD-01
        data = self.socket.recv(1024)
        # Decode bytes to hex
        ans = data.hex()
        #print("STOP", ans)

    def can_reach(self, al, az):
        """Check if telescope can reach this position. Assuming input in degrees.
        
        All directions might not be possible due to telescope mechanics. Also,
        some angles such as pointing towards the earth, are not reachable. Some
        galactic coordinates for example will translate to unreachable
        directions at some times while OK directions at other times. 

        This function will shift the given coordinates to a local range for doing the
        comparison, since the local azimuth might be negative in the telescope
        configuration."""
        ## CHECK ALTITUDE
        #if (al > self.maxal_deg or al < self.minal_deg):
        #    al = round(al, 2)
        #    #print 'AL: Sorry, altitude' + str(al) + ' is not reachable by this telescope.'
        #    return False

        ## CHECK AZIMUTH
        #if (az > self.maxaz_deg):
        #    # This assumes that azimuth is always given in range 0 to 360,
        #    # something assured by the high-level system. But, here we need to
        #    # account for the fact that the telescope works in a range which
        #    # might be negative (for practical programming reasons).
        #    az = az-360.0
        ## If just comparing min_az with requested az, we get silly error for
        ## example that the minimum az itself is not allowed, since comparision
        ## of decimal numbers very close is tricky (floating point math...) So,
        ## instead check if difference (with right sign) is larger than the
        ## minimum error. Since the mininum error in the telescope will be
        ## larger than the floating point error, this comparison should work.
        #if (self.minaz_deg-az)>self.get_min_azerror_deg():
        #    az = round(az,2)
        #    #print 'AZ: Sorry, azimuth ' + str(az) + ' is not reachable by this telescope.'
        #    return False
        # 
        # All checks passed, so return True
        return True

    def move(self):
        tel, taz = self.target_alaz
        PH = 10 # Pulses per degree, 0A in hex
        PV = 10 # Pulses per degree, 0A in hex
        H = str(int(PH * (360+taz)))
        H1 = "3"+H[0]
        H2 = "3"+H[1]
        H3 = "3"+H[2]
        H4 = "3"+H[3]
        V = str(int(PV * (360+tel)))
        V1 = "3"+V[0]
        V2 = "3"+V[1]
        V3 = "3"+V[2]
        V4 = "3"+V[3]
        msg = bytes.fromhex("57"+H1+H2+H3+H4+"0A"+V1+V2+V3+V4+"0A2F20")
        # Send message
        self.socket.send(msg)
        # Read response from MD-01
        data = self.socket.recv(1024)
        # Decode bytes to hex
        ans = data.hex()
    
    def get_stow_alaz(self):
        """Returns the stow altitude and azimuth of the telescope as a tuple of decimal numbers [degrees]."""
        return (self.stowal_deg, self.stowaz_deg)

    def set_target_alaz(self, al, az):
        """Set the target altitude and azimuth of the telescope. Arguments in degrees."""
        if self.can_reach(al,az):
            self.target_alaz = (round(al,1), round(az,1))
        else: 
            raise TelescopeError('Cannot reach desired position')
            #raise TelescopeError('You requested the telescope to move to horizontal coordinates alt=' + str(round(al,2)) + ', az=' + str(round(az,2)) + '. Sorry, but this telescope cannot reach this position. In altitude the telescope cannot reach below ' + str(round(self.minal_deg,2)) + ' or above ' + str(round(self.maxal_deg,2)) + ' degrees. In azimuth, the telescope cannot reach values between ' + str(round(self.maxaz_deg%360,2)) + ' and ' + str(round(self.minaz_deg%360,2)) + ' degrees. If you are trying to reach a moving coordinate, such as the Sun or the galaxy, try later when your object have moved to an observable direction.')
    
    def get_current_alaz(self):
        """Returns the current altitude and azimuth of the telescope as a tuple of decimal numbers [degrees]."""
        #Format status request message as bytes
        msg = bytes.fromhex("57000000000000000000001F20")
        # Send message
        self.socket.send(msg)
        # Read response from MD-01
        data = self.socket.recv(1024)
        # Decode bytes to hex
        ans = data.hex()
        # Extract relevant data as floating point numbers
        H1 = float(ans[2:4])
        H2 = float(ans[4:6])
        H3 = float(ans[6:8])
        H4 = float(ans[8:10])
        V1 = float(ans[12:14])
        V2 = float(ans[14:16])
        V3 = float(ans[16:18])
        V4 = float(ans[18:20])
        # Calculate angles for Az/El
        az = H1 * 100 + H2 * 10 + H3 + H4 / 10 -360
        el = V1 * 100 + V2 * 10 + V3 + V4 / 10 -360
        return (el, az)

    def is_close_to_target(self):
        """Returns true if telescope is close enough to observe, else False."""
        cal, caz = self.get_current_alaz()
        tal, taz = self.target_alaz
        dist = self._get_angular_distance(cal, caz, tal, taz)
        if dist< self.close_enough_distance:
            return True
        else:
            return False
    
    def get_azimuth_distance(self, az1, az2):
        """ This function calculates the distance needed to move in azimuth to between two angles. This takes into account that the 
        telescope may need to go 'the other way around' to reach some positions, i.e. the distance to travel can be much larger than the 
        simple angular distance. This assumes that both azimuth positions are valid, something which can be checked first with the can_reach function."""
        
        ## CHECK AZIMUTH
        ## This assumes that azimuth is always given in range 0 to 360,
        ## something assured by the high-level system. But, here we need to
        ## account for the fact that the telescope works in a range which
        ## might be negative (for practical programming reasons).
        # if (az1 > self.maxaz_deg):
        #     az1 = az1-360.0
        # elif (az1 < self.minaz_deg):
        #     az1 = az1+360.0
        # # Second position
        # if (az2 > self.maxaz_deg):
        #     az2 = az2-360.0
        # elif (az2 < self.minaz_deg):
        #     az2 = az2+360.0
        # # Now return the distance needed to travel in degrees
        return np.abs(az1-az2)


    # Takes angular coordinates of two points and calculates the 
    # angular distance between them by converting to cartesian unit vectors and taking the dot product.
    def _get_angular_distance(self, ra1_in_deg, dec1_in_deg, ra2_in_deg, dec2_in_deg):
        ra1_in_rad = ra1_in_deg*np.pi/180.0
        dec1_in_rad = dec1_in_deg*np.pi/180.0
        ra2_in_rad = ra2_in_deg*np.pi/180.0
        dec2_in_rad = dec2_in_deg*np.pi/180.0
        x1 = 1.0*np.sin(0.5*np.pi-dec1_in_rad)*np.cos(ra1_in_rad)
        y1 = 1.0*np.sin(0.5*np.pi-dec1_in_rad)*np.sin(ra1_in_rad)
        z1 = 1.0*np.cos(0.5*np.pi-dec1_in_rad)
    
        x2 = 1.0*np.sin(0.5*np.pi-dec2_in_rad)*np.cos(ra2_in_rad)
        y2 = 1.0*np.sin(0.5*np.pi-dec2_in_rad)*np.sin(ra2_in_rad)
        z2 = 1.0*np.cos(0.5*np.pi-dec2_in_rad)
        dotprod = np.dot([x1,y1,z1], [x2, y2, z2])
        # I got warnings from arccos, so divided into
        # several lines surrounded by code which should catch the
        # RuntimeWarning and display the parameters used to generate
        # the code like this:
        #import warnings
        #with warnings.catch_warnings():
        #    warnings.filterwarnings('error')
        #    try:
        #        dotprod = np.dot([x1,y1,z1], [x2, y2, z2])
        #        distance_in_rad = np.arccos(dotprod)
        #    except Warning:
        #        print "warning"
        #        print dotprod, ra1_in_deg, dec1_in_deg, ra2_in_deg, dec2_in_deg
        # After testing, it seems that the RuntimeError is produced when using args
        # _get_angular_distance(35.25, 325.75, 35.25, 325.75) because np.dot
        # returns a value larger than 1 (!), namely:
        #print '{0:.16f}'.format(dotprod) = 1.0000000000000002
        # So, to solve this - since we do not need exactly the correct angle 
        # because of the large beam and angular resolution in the cogs,
        # we can just limit the arccos to be one here. I chose to
        # do this by a simple min-statement, should avoid the warning
        # and give correctly 0 as angular distance.
        distance_in_rad = np.arccos(min(dotprod,1.0))
        distance_in_deg = distance_in_rad * 180.0/np.pi
        return distance_in_deg

# Exceptions for this class
class TelescopeError(Exception):
    """ Used for telescope errors. """
    pass

