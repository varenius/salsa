import socket
import time
import ephem
import configparser
import math

class MD01():
    """ Provides functions to communicate with the MD01 telescope driver
    device. Communication via telnet using python socket. """

    def __init__(self, configfile):
        """ Creates a new object with a connection to driver. Requires a configfile for telescope parameters."""
        self._read_config(configfile)
        self._connect()
            
    def stop(self):
        """Stops any movement of the telescope """
        #Format status request message as bytes
        msg = bytes.fromhex("57000000000000000000000F20")
        self._md01(msg)
    
    def move(self, al, az):
        # Round to 0.1 deg precision
        tal = round(al+self.offset_al, 1)
        taz = round(az+self.offset_az, 1)
        PH = 10 # Pulses per degree, 0A in hex
        PV = 10 # Pulses per degree, 0A in hex
        H = str(int(PH * (360+taz)))
        H1 = "3"+H[0]
        H2 = "3"+H[1]
        H3 = "3"+H[2]
        H4 = "3"+H[3]
        V = str(int(PV * (360+tal)))
        V1 = "3"+V[0]
        V2 = "3"+V[1]
        V3 = "3"+V[2]
        V4 = "3"+V[3]
        msg = bytes.fromhex("57"+H1+H2+H3+H4+"0A"+V1+V2+V3+V4+"0A2F20")
        self._md01(msg)

    def get_current_alaz(self):
        """Get current altitude and azimuth of the telescope as a tuple of decimal numbers [degrees]."""
        #Format status request message as bytes
        msg = bytes.fromhex("57000000000000000000001F20")
        ans = self._md01(msg)
        # Extract relevant data as floating point numbers
        H1 = float(ans[2:4])
        H2 = float(ans[4:6])
        H3 = float(ans[6:8])
        H4 = float(ans[8:10])
        V1 = float(ans[12:14])
        V2 = float(ans[14:16])
        V3 = float(ans[16:18])
        V4 = float(ans[18:20])
        # Calculate angles for Az/Al
        az = round(H1 * 100 + H2 * 10 + H3 + H4 / 10 -360, 1)
        al = round(V1 * 100 + V2 * 10 + V3 + V4 / 10 -360, 1)
        return (al, az)
    
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
        return round(alt_deg,3), round(az_deg,3)

    ### 
    ### Functions below starting with underscore are not intended to be called outside this script.
    ### 

    def _read_config(self, configfile):
        # Set config file location
        config = configparser.ConfigParser()
        config.read(configfile)
        # Read MD01 details
        self.ipaddr = config.get('MD01', 'host')
        self.port = config.getint('MD01', 'port')
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(2)
        self.connected=False

        # Read telescope position details
        self.site = ephem.Observer()
        self.site.date = ephem.now()
        self.site.lat = ephem.degrees(config.get('SITE', 'latitude'))
        self.site.long = ephem.degrees(config.get('SITE', 'longitude'))
        self.site.elevation = config.getfloat('SITE', 'elevation')
        self.site.pressure = 0 # Do not correct for atmospheric refraction
        self.site.name = config.get('SITE', 'name')

        # Read telescope pointing offsets
        # These values will be added to any target position
        self.offset_al = config.getfloat('POINTING', 'offset_al')
        self.offset_az = config.getfloat('POINTING', 'offset_az')

    def _connect(self):
        try:
            self.socket.connect((self.ipaddr, self.port))
            self.connected = True
        except:
            print("ERROR: Could not connect to {} port {}".format(self.ipaddr, self.port))
            self.connected = False

    def _md01(self, m):
        if self.connected:
            # Send message to MD01
            self.socket.sendall(m)
            time.sleep(0.01) # Seconds, to ensure message is ready, just in case
            # Read response from MD01
            data = self.socket.recv(1024)
            # Decode bytes to hex
            return data.hex()
        else:
            print("Ignoring MDO1 command since not connected.")

