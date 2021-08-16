import socket
import time
import ephem
import numpy as np
import sys
from PyQt5 import QtWidgets, QtCore
import threading

class resetThread(threading.Thread):
    """ Class used to run the reset algorithm in a separate thread, otherwise time.sleep will block main excecution."""

    def __init__(self, tel):
        threading.Thread.__init__(self)
        self.tel = tel

    def run(self):
        # Must be Az, then Al order, for reset logic to set correct position
        self._reset_az()
        self._reset_al()
        if self.tel.alresetok and self.tel.azresetok:
            print("INFO: Both AL and AZ resets OK. Setting position.")
            self.tel.action="RESET"
        else:
            print("INFO: AL or AZ reset FAILED! Not setting position!")

    def _reset_az(self):
        # RESET AZ
        self.tel.stop()
        time.sleep(3) # Ensure we have stopped properly
        resetaz = self.tel.resetaz_deg
        search = 3 # Search region for reset region, degrees
        step = 0.5 # Stepsize to find reset region, degrees
        naz = 10 # Number of reset enlargments. First try +-search, then from +-(2*search to search), then...
                   # So example: First -3 to +3 deg, then -6 to -3 and +3 to +6, then -9 to -6 and +6 to +9...
        azfound = False
        for i in range(naz): 
            # Define points to check in first half of reset region
            s1 = np.arange(i*search,(i+1)*search+step, step)
            # Second half is just the negated range (will double count 0 for i=0, but that's OK)
            s2 = -1*s1
            # Create one range of azimuth angles to check, relative to resetaz
            az2check = np.sort(np.concatenate((s1,s2))) + resetaz
            print("RESET: Checking azimuth angles {0} ...".format(az2check))
            ral = 90 # Use altitude during azimuth checks
            for raz in az2check:
                self.tel.set_target_alaz(ral, raz)
                time.sleep(2) # Allow for some slewing for small angles
                while not self.tel.is_tracking():
                    cal, caz = self.tel.get_current_alaz()
                    print("RESET: Slewing to (az,el) = ({0:5.1f},{1:5.1f}) from ({2:5.1f},{3:5.1f})...".format(raz,ral,caz,cal))
                    self.tel.set_target_alaz(ral, raz)
                    time.sleep(2)
                # Arrived at desired position. Check for reset signal
                if self.tel._readio()==1:
                    print("RESET: Found az region! Searching for edge ...")
                    # Found reset region. Now find edge from negative direction
                    while self.tel._readio()==1:
                        cal, caz = self.tel.get_current_alaz()
                        # Go in negative az until io signal lost
                        tal = cal
                        taz = caz-step
                        self.tel.set_target_alaz(tal, taz) 
                        time.sleep(2) # Allow for some slewing for small angles
                        while not self.tel.is_tracking():
                            cal, caz = self.tel.get_current_alaz()
                            print("RESET: Slewing to (az,el) = ({0:5.1f},{1:5.1f}) from ({2:5.1f},{3:5.1f})...".format(taz,tal,caz,cal))
                            self.tel.set_target_alaz(tal, taz) 
                            time.sleep(2)
                    print("RESET: Found edge, refining...")
                    while self.tel._readio()==0:
                        cal, caz = self.tel.get_current_alaz()
                        # Go in pos az until io signal found again
                        tal = cal
                        taz = taz+0.1 # 
                        self.tel.set_target_alaz(tal, taz) 
                        time.sleep(2) # Allow for some slewing for small angles
                        while not self.tel.is_tracking():
                            print("RESET: Slewing to (az,el) = ({0:5.1f},{1:5.1f}) from ({2:5.1f},{3:5.1f})...".format(taz,tal,caz,cal))
                            cal, caz = self.tel.get_current_alaz()
                            self.tel.set_target_alaz(tal, taz) 
                            time.sleep(2)
                    # We should now be at the proper azimuth reference place!
                    azfound = True
                    break
            if azfound:
                time.sleep(2) # Wait for variables to settle to new state
                cal, caz = self.tel.get_current_alaz()
                self.tel.azresetok = True
                print("RESET: Found reset signal edge at {0:5.1f}, while resetaz is {1:5.1f}, so diff {2:5.1f}".format(caz,resetaz, resetaz-caz))
                time.sleep(2) # Wait for variables to settle to new state
                break
        if not azfound:
            self.tel.azresetok = False #
            print("RESET: AZIMUTH RESET FAILED!")

    def _reset_al(self):
        # RESET AL
        self.tel.stop()
        alfound = False
        # First go to high altitude to prepare that we always do the same movement
        cal, caz = self.tel.get_current_alaz()
        tal = 45
        taz = caz
        self.tel.set_target_alaz(tal, taz) 
        while not self.tel.is_tracking():
            cal, caz = self.tel.get_current_alaz()
            #print(self.tel.target_alaz, self.tel.current_alaz)
            print("RESET: AL: Slewing to (az,el) = ({0:5.1f},{1:5.1f}) from ({2:5.1f},{3:5.1f})...".format(taz,tal,caz,cal))
            self.tel.set_target_alaz(tal, taz) 
            time.sleep(2)
        # Initialise position memory to see if we are stuck
        oldal, oldaz = self.tel.get_current_alaz()
        print(self.tel.get_current_alaz(), self.tel.action)
        # Now, go until we hit the limits in al
        tal = -5
        self.tel.set_target_alaz(tal, caz)
        time.sleep(2) # Allow for some slewing to make sure we start moving
        # Keep counting for how long we have been stuck
        stuckcount = 0
        while not self.tel.is_tracking():
            cal, caz = self.tel.get_current_alaz()
            if round(cal,1) == round(oldal,1):
                stuckcount +=1
            else:
                stuckcount = 0
            print("RESET: AL: Slewing to (az,el) = ({0:5.1f},{1:5.1f}) from ({2:5.1f},{3:5.1f})...".format(taz,tal,caz,cal))
            print("RESET: AL: Stuckcount at ", stuckcount)
            if stuckcount >3:
                alfound = True
                # Important to stop, otherwise we get PULS TIMEOUT lock and need to reboot MD01
                self.tel.stop()
                time.sleep(3) # Wait for commands to finish
                break
            # If no limit, continue
            oldal, oldaz = self.tel.get_current_alaz()
            self.tel.set_target_alaz(tal, caz)
            time.sleep(1)
        if alfound:
            self.tel.alresetok = True #
            print("RESET: ALTITUDE RESET APPEARS TO HAVE WORKED!")
        else:
            self.tel.alresetok = False #
            print("RESET: ALTITUDE RESET FAILED!")

class TelescopeController():
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
        # Read reset position from config file
        self.resetaz_deg = config.getfloat('MD01', 'resetaz')
        self.resetal_deg = config.getfloat('MD01', 'resetal')

        self.close_enough_distance = config.getfloat('MD01', 'close_enough')

        self.offset_az_deg = config.getfloat('MD01', 'offset_az_deg')
        self.offset_al_deg = config.getfloat('MD01', 'offset_al_deg')
        
        self.minal_deg = config.getfloat('MD01', 'minal')
        self.maxal_deg = config.getfloat('MD01', 'maxal')
        self.io_host = config.get('I/O', 'host')
        self.io_port = config.getint('I/O', 'port')
        self.io_azport = config.getint('I/O', 'azport')

        # Create timer used to toggle (and update) tracking
        self.trackingtimer = QtCore.QTimer()
        self.trackingtimer.timeout.connect(self.do_action)
        self.trackingtimer.start(1000) # ms. VERY IMPORTANT: Never go quicker than once per second, else PULS TIMEOUT errors.
        self.action = ""
        self.target_alaz = (0,0)
        self.current_alaz = (0,0)

        self.isresetting = False
        self.alresetok = False
        self.azresetok = False

        ## Make sure Noise Diode is turned off until implemented in GUI etc.
        #self.set_noise_diode(False)

    def set_noise_diode(self, status):
        pass

    def _readio(self):
        # Create connection object
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.io_host, self.io_port)) 
        msg = "read:ttl:{}?\n".format(self.io_azport)
        # Send message
        sock.sendall(msg.encode("ascii"))
        # Wait to for I/O box to generate answer
        time.sleep(0.1)
        # Read response
        ans = sock.recv(8192).decode("ascii").strip()
        print("IO reply: ", ans)
        return int(ans[-1])

    def reset(self):
        self.isresetting = True
        self.alresetok = False
        self.azresetok = False
        self.thread = resetThread(self)
        self.thread.start()

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
            self._set_current_azel(self.resetaz_deg,self.resetal_deg)
            print("RESET: Current position has been set to reset position.")
            self.isresetting = False # Done with resetting
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
    
    def _set_current_azel(self,taz,tel):
        """ Set the current az el position of MD01 to the given values. NOTE: This is the actual current position reading, not the target pos.!"""
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
        msg = bytes.fromhex("57"+H1+H2+H3+H4+"0A"+V1+V2+V3+V4+"0AF920")
        self.md01(msg)
       
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
        # CHECK ALTITUDE, if not resetting
        if not self.isresetting:
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
        print("SET", al, az)
        """Set the target altitude and azimuth of the telescope. Arguments in degrees."""
        tal, taz = self.pcor(al, az)
        if self.can_reach(tal,taz):
            print("SET", tal, taz)
            new_target_alaz = (round(tal,1), round(taz,1))
            if (new_target_alaz!=self.target_alaz):
                print("SET CHANGE")
                print("CHANGING TARGET TO (el,az) = ({0:5.1f},{1:5.1f}) from ({2:5.1f},{3:5.1f})...".format(*new_target_alaz, *self.target_alaz))
                self.target_alaz=new_target_alaz
                #self.action="MOVE"
                self.action="START"
                print("SET ACTION", self.action)
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
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText(m)
        #msg.setInformativeText(m)
        msg.setWindowTitle("Telescope message:")
        msg.exec_()

    def connect_md01(self):
        try:
            self.socket.connect((self.host, self.port))
        except socket.error as e:
            self.show_message(e)
            sys.exit(1)
