import socket
import time
import ephem
import numpy as np
import sys
from PyQt5 import QtWidgets, QtCore

class TelescopeController:
    """ Provides functions to communicate with the MD01 telescope driver
    device. Communication via telnet using python socket. """

    def __init__(self, config):
        """ Creates a new object with a connection to driver."""
        # Create connection to MD01
        self.host = config.get('MD01', 'host')
        self.port = config.getint('MD01', 'port')
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(2)
        self.connect_md01()
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

        self.offset_az_deg = config.getfloat('MD01', 'offset_az_deg')
        self.offset_al_deg = config.getfloat('MD01', 'offset_al_deg')
        
        self.minal_deg = config.getfloat('MD01', 'minal')
        self.maxal_deg = config.getfloat('MD01', 'maxal')

        # Create timer used to toggle (and update) tracking
        self.trackingtimer = QtCore.QTimer()
        self.trackingtimer.timeout.connect(self.do_action)
        self.trackingtimer.start(1000) # ms. VERY IMPORTANT: Never go quicker than once per second, else PULS TIMEOUT errors.
        self.action = ""
        self.target_alaz = (0,0)
        self.current_alaz = (0,0)

        ## Make sure Noise Diode is turned off until implemented in GUI etc.
        #self.set_noise_diode(False)

    def set_noise_diode(self, status):
        pass

    def isreset(self):
        return True

    def reset(self):
        pass

    def do_action(self):
        #print(self.action)
        if self.action=="MOVE":
            # If we are going to move to new position, first stop
            self._stop()
            # Then tell us to move as next action
            self.action="START"
        elif self.action=="START":
            self._start()
            self.action=""
        elif self.action=="STOP":
            self._stop()
            self.action=""
            # Remove local memory of previous target position, else we cannot stop and restart slew to same position.
            self.target_alaz = (-1,-1)
        elif self.action=="RESET":
            self._reset()
            self.action=""
        else:
            self._get_current_alaz()
            self.action=""

    def md01(self, m):
        # Send message to MD01
        self.socket.send(m)
        time.sleep(0.01) # Seconds, to ensure message is ready, just in case
        # Read response from MD01
        data = self.socket.recv(1024)
        # Decode bytes to hex
        return data.hex()
       
    def stop(self):
        self.action="STOP"

    def _stop(self):
        """Stops any movement of the telescope """
        #Format status request message as bytes
        msg = bytes.fromhex("57000000000000000000000F20")
        self.md01(msg)

    def can_reach(self, al, az):
        """Check if telescope can reach this position. Assuming input in degrees.
        
        All directions might not be possible due to telescope mechanics. Also,
        some angles such as pointing towards the earth, are not reachable. Some
        galactic coordinates for example will translate to unreachable
        directions at some times while OK directions at other times. 

        This function will shift the given coordinates to a local range for doing the
        comparison, since the local azimuth might be negative in the telescope
        configuration."""
        (al, az) = self.pcor(al,az)
        # CHECK ALTITUDE
        if (al > self.maxal_deg or al < self.minal_deg):
            al = round(al, 2)
            #print 'AL: Sorry, altitude' + str(al) + ' is not reachable by this telescope.'
            return False

        return True

    def _start(self):
        tel, taz = self.target_alaz
        #print("Moving to (pointing corrected) alt,az ",tel, taz)
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
        self.md01(msg)
    
    def get_stow_alaz(self):
        """Returns the stow altitude and azimuth of the telescope as a tuple of decimal numbers [degrees]."""
        return (self.stowal_deg, self.stowaz_deg)

    def set_target_alaz(self, al, az):
        """Set the target altitude and azimuth of the telescope. Arguments in degrees."""
        tal, taz = self.pcor(al, az)
        if self.can_reach(tal,taz):
            new_target_alaz = (round(tal,1), round(taz,1))
            #print("old target", self.target_alaz, "new target", new_target_alaz, "current", self.current_alaz)
            if not new_target_alaz==self.target_alaz:
                self.target_alaz=new_target_alaz
                #self.action="MOVE"
                self.action="START"
        else: 
            raise ValueError("Cannot reach desired position. Target outside altitude range " + str(round(self.minal_deg,2)) + " to "+ str(round(self.maxal_deg,2))+" degrees. Please adjust your desired position.")
    
    def _get_current_alaz(self):
        """Returns the current altitude and azimuth of the telescope as a tuple of decimal numbers [degrees]."""
        #Format status request message as bytes
        msg = bytes.fromhex("57000000000000000000001F20")
        ans = self.md01(msg)
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
        self.current_alaz = (el, az)

    def get_current_alaz(self):
        return self.invpcor(*self.current_alaz)

    def invpcor(self, al,az):
        return (al-self.offset_al_deg, az-self.offset_az_deg)
    
    def pcor(self, al,az):
        return (al+self.offset_al_deg, az+self.offset_az_deg)

    def is_tracking(self):
        """Returns true if telescope is close enough to observe, else False."""
        cal, caz = self.current_alaz
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

    def show_message(self, e):
        # Just print(e) is cleaner and more likely what you want,
        # but if you insist on printing message specifically whenever possible...
        if hasattr(e, 'message'):
            m = e.message
        else:
            m = str(e)
        print(m)
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText(m)
        #msg.setInformativeText(m)
        msg.setWindowTitle("Telescope error")
        msg.exec_()

    def connect_md01(self):
        try:
            self.socket.connect((self.host, self.port))
        except socket.error as e:
            self.show_message(e)
            sys.exit(1)
