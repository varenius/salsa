import socket
import time
import ephem
import numpy as np

class TelescopeController:
    """ Provides functions to communicate with the RIO telescope driver
    device.  This uses the DMC language communicated via telnet using
    python socket connections.  """

    def __init__(self, config):
        """ Creates a new object with a connection to the RIO driver
        device."""
        # Create connection to RIO
        self.host = config.get('RIO', 'host')
        self.port = config.getint('RIO', 'port')
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Given by Galil support
        self.socket.connect((self.host, self.port)) # Given by Galil support
        self.site = ephem.Observer()
        self.site.date = ephem.now()
        self.site.lat = ephem.degrees(config.get('SITE', 'latitude'))
        self.site.long = ephem.degrees(config.get('SITE', 'longitude'))
        self.site.elevation = config.getfloat('SITE', 'elevation')
        self.site.pressure = 0 # Do not correct for atmospheric refraction
        self.site.name = config.get('SITE', 'name')
        
        # Get cog number limits from RIO device
        self.minal_cog = self._get_minal_cog()
        self.maxal_cog = self._get_maxal_cog()
        self.minaz_cog = self._get_minaz_cog()
        self.maxaz_cog = self._get_maxaz_cog()
        self.nsteps_al = self.maxal_cog - self.minal_cog
        self.nsteps_az = self.maxaz_cog - self.minaz_cog
        
        # Set stepsize, TODO: should be in RIO?
        # Smallest step separation in degrees, i.e. half cog-cog distance.
        self.cogstep_al_deg = 0.125
        self.cogstep_az_deg = 0.125

        # Read stepsize and angles from configfile
        self.minaz_deg = config.getfloat('RIO', 'minaz')
        self.maxaz_deg = self.minaz_deg + self.nsteps_az*self.cogstep_az_deg
        self.minal_deg = config.getfloat('RIO', 'minal')
        self.maxal_deg = self.minal_deg + self.nsteps_al*self.cogstep_al_deg
        self.close_enough_distance = config.getfloat('RIO', 'close_enough')

        # TODO: test if new RIO box allows smaller margins.
        self._set_azerror_cog(4) # Set tolerance in az, default is 4
        self._set_alerror_cog(4) # set tolerance in al, default is 4

    def set_LNA(self, status):
        if status:
            self._cmd('SB8') # Turn on LNA
            if self._get_msg()==':':
                print 'RIO: LNA is now ON.'
        else:
            self._cmd('CB8') # Turn on LNA
            if self._get_msg()==':':
                print 'RIO: LNA is now OFF.'

    def reset(self):
        # Print message reset is starting
        print "RIO: Resetting telescope control system..."
        # Reset hardware to power-on (EEPROM) state
        self._cmd('RS')
        if self._get_msg()=='\r\n:':
            time.sleep(1.0)
            print "RIO: Control hardware reset to power-on state."

        # Move telescope to end position to reset pointing
        self._cmd('XQ #INIT')
        if self._get_msg()==':':
            time.sleep(0.5)
            print 'RIO: Moving telescope to end position. Please wait...'

    def isreset(self):
        """Check if telescope has reached reset position."""
        if (self.minal_cog == self._get_current_al_cog() and  self.minaz_cog == self._get_current_az_cog()):
            return True
        else:
            return False

    def set_pos_ok(self):
        """ Tell telescope that it now knows where it is, i.e. the reset worked. Unfortunately, the telescope 
        does not realise this itself, rather this is checked from the GUI using the function "isreset" here. """
        self._cmd('knowpos = 1')
        if self._get_msg()==':':
            time.sleep(0.5)
            print "RIO: The telescope now knows where it is. Thanks for resetting me!"
    
    def get_pos_ok(self):
        """ Check if the telescope knows where it is, i.e. if there has been a power cut. If "knowpos"=1, then
        all is well. If knowpos = 0, then the telscope has been reset due to a power cut, and is currently in its 
        power-on state where it does not know the position. A reset is needed. here. """
        knowpos = self._get_value_from_telescope("knowpos")
        if knowpos == 0:
            return False
        else:
            return True

    def _get_msg(self):
        """ Reads the output of the socket connection, i.e. the RIO
        output.""" 
        #TODO: Adjust timeout for recv not to block in case of
        #      missing output. If no output should instead 
        #      throw exception.
        return self.socket.recv(1024)

    def _cmd(self, cmdstring):
        """ Sends a command to the RIO device."""
        self.socket.sendall(cmdstring+'\r')
        # TODO: else throw communication exception?
    
    def _get_value_from_telescope(self, value):
        """Return the value of a variable stored in the telescope memory
        as an integer.""" 
        self._cmd('MG '+value+'{F4.0}')
        ans = self._get_msg()
        # TODO: else throw communication exception?
        return int(ans[0:5])

    # The following 4 static cog variable get functions could be omitted
    # and just put directly as get_value commands in the reset-function.
    def _get_minal_cog(self):
        """Return the minimum altitude cog number from the telescope as
        an integer.""" 
        return self._get_value_from_telescope('minel')

    def _get_maxal_cog(self):
        """Return the maximum altitude cog number from the telescope as
        an integer.""" 
        return self._get_value_from_telescope('maxel')

    def _get_minaz_cog(self):
        """Return the minimum azimuth cog number from the telescope as an integer."""
        return self._get_value_from_telescope('minaz')
    
    def _get_maxaz_cog(self):
        """Return the maximum azimuth cog number from the telescope as an integer."""
        return self._get_value_from_telescope('maxaz')

    ##

    def _get_target_al_cog(self):
        """Return the target altitude cog number from the telescope as an integer."""
        return self._get_value_from_telescope('t_el')

    def _get_target_az_cog(self):
        """Return the target azimuth cog number from the telescope as an integer."""
        return self._get_value_from_telescope('t_az')
    
    def _get_current_al_cog(self):
        """Return the current altitude cog number from the telescope as an integer."""
        return self._get_value_from_telescope('c_el')
    
    def _get_current_az_cog(self):
        """Return the current azimuth cog number from the telescope as an integer."""
        return self._get_value_from_telescope('c_az')
    
    def _set_target_al_cog(self, new_al_cog):
        """Set the target altitude of the telescope. Argument in cognr."""
        self._cmd('t_el='+str(new_al_cog))
        if self._get_msg()==':':
            pass
    
    def _set_azerror_cog(self, azerror):
        """Set tolerance in azimuth in number. Argument in cogsteps."""
        self._cmd('err_az='+str(azerror))
        if self._get_msg()==':':
            pass
    
    def _set_alerror_cog(self, alerror):
        """Set tolerance in azimuth in number. Argument in cogsteps."""
        self._cmd('err_al='+str(alerror))
        if self._get_msg()==':':
            pass
    
    def _set_target_az_cog(self, new_az_cog):
        """Set the target azimuth of the telescope. Argument in cognr."""
        self._cmd('t_az='+str(new_az_cog))
        if self._get_msg()==':':
            pass
    
    def _get_current_al(self):
        """Return the current altitude in degrees."""
        result = self.minal_deg + self._get_current_al_cog()*(self.maxal_deg-self.minal_deg)/self.maxal_cog
        # Make sure result is returned in range 0 to 90
        result = result % 90.0
        return result
    
    def _get_current_az(self):
        """Return the current azimuth in degrees."""
        result = self.minaz_deg + self._get_current_az_cog()*(self.maxaz_deg-self.minaz_deg)/self.maxaz_cog
        # Make sure result is returned in range 0 to 360
        result = result % 360.0
        return result
    
    def _get_target_al(self):
        """Return the target altitude in degrees."""
        result =  self.minal_deg + self._get_target_al_cog()*(self.maxal_deg-self.minal_deg)/self.maxal_cog
        # Make sure result is returned in range 0 to 90
        result = result % 90.0
        return result
    
    def _get_target_az(self):
        """Return the target azimuth in degrees."""
        result =  self.minaz_deg + self._get_target_az_cog()*(self.maxaz_deg-self.minaz_deg)/self.maxaz_cog
        # Make sure result is returned in range 0 to 360
        result = result % 360.0
        return result

    def _set_target_al(self, al):
        """Set the target altitude of the telescope. Argument in degrees."""
        new_al_cog = int(self.maxal_cog*al/self.maxal_deg)
        self._set_target_al_cog(new_al_cog)
    
    def _set_target_az(self, az):
        """Set the target azimuth of the telescope. Argument in range 0 to 360 degrees relative to NORTH."""
        # Check if azimuth needs to be translated to local 
        # range. Local range can be negative to less than 360 deg but still
        # cover a whole 360 degrees. 
        if az > self.maxaz_deg:
            az = az-360.0
        new_az_cog = int(self.maxaz_cog * (az-self.minaz_deg)/(self.maxaz_deg-self.minaz_deg))
        self._set_target_az_cog(new_az_cog)

    def move(self):
        """Move the telescope from the current position to target position."""
        curaz = self._get_current_az_cog()
        curalt = self._get_current_al_cog()
        taraz = self._get_target_az_cog()
        taralt = self._get_target_al_cog()
        self._cmd('XQ #MOVE')
        if self._get_msg()==':':
            #print 'RIO: Telescope moving to target position...'
            #print 'RIO: Moving from cogs ALT='+str(curalt) + '->'+str(taralt) + ', AZ='+str(curaz) + '->'+str(taraz)
            #print 'RIO: Moving from DEG ALT='+str(self._get_current_al()) + '->'+str(self._get_target_al()) + ', AZ='+str(self._get_current_az()) + '->'+str(self._get_target_az())
            pass
    
    def stop(self):
        """Stops any movement of the telescope and reset all indicators to off. """
        self._cmd('XQ #STOP')
        if self._get_msg()==':':
            print 'RIO: Telescope halted.'

    def is_moving(self):
        """Check if telescope is moving or not."""
        # TODO, maybe check the two motors instead, i.e. OUT0 and OUT2?
        self._cmd('TB')
        status = self._get_msg()[1:-3]
        if status=='1':
            # Telescope is resting.
            return False
        elif status=='129':
            # Telescope is moving (with echo on).
            return True
        else:
            # raise exception
            pass

    def can_reach(self, al, az):
        """Check if telescope can reach this position. Assuming input in degrees.
        
        All directions might not be possible due to telescope mechanics. Also,
        some angles such as pointing towards the earth, are not reachable. Some
        galactic coordinates for example will translate to unreachable
        directions at some times while OK directions at other times. 

        This function will shift the given coordinates to a local range for doing the
        comparison, since the local azimuth might be negative in the telescope
        configuration."""
        # CHECK ALTITUDE
        if (al > self.maxal_deg or al < self.minal_deg):
            al = round(al, 2)
            #print 'AL: Sorry, altitude' + str(al) + ' is not reachable by this telescope.'
            return False

        # CHECK AZIMUTH
        if (az > self.maxaz_deg):
            # This assumes that azimuth is always given in range 0 to 360,
            # something assured by the high-level system. But, here we need to
            # account for the fact that the telescope works in a range which
            # might be negative (for practical programming reasons).
            az = az-360.0
        # If just comparing min_az with requested az, we get silly error for
        # example that the minimum az itself is not allowed, since comparision
        # of decimal numbers very close is tricky (floating point math...) So,
        # instead check if difference (with right sign) is larger than the
        # minimum error. Since the mininum error in the telescope will be
        # larger than the floating point error, this comparison should work.
        if (self.minaz_deg-az)>self.get_min_azerror_deg():
            az = round(az,2)
            #print 'AZ: Sorry, azimuth ' + str(az) + ' is not reachable by this telescope.'
            return False
        
        # All checks passed, so return True
        return True
    
    def get_min_azerror_deg(self):
        return self._get_value_from_telescope('err_az')*self.cogstep_az_deg
    
    def get_min_alerror_deg(self):
        return self._get_value_from_telescope('err_al')*self.cogstep_al_deg

    def set_target_alaz(self, al, az):
        """Set the target altitude and azimuth of the telescope. Arguments in degrees."""
        if self.can_reach(al,az):
            self._set_target_al(al)
            self._set_target_az(az)
        else: 
            raise TelescopeError('You requested the telescope to move to horizontal coordinates alt=' + str(round(al,2)) + ', az=' + str(round(az,2)) + '. Sorry, but this telescope cannot reach this position. If you are trying to reach a moving coordinate, such as the Sun or the galaxy, try later when your object have moved to another horizontal coordinate.')
    
    def get_target_alaz(self):
        """Returns the target altitude and azimuth of the telescope as a tuple of decimal numbers [degrees]."""
        return (self._get_target_al(), self._get_target_az())
    
    def get_current_alaz(self):
        """Returns the current altitude and azimuth of the telescope as a tuple of decimal numbers [degrees]."""
        return (self._get_current_al(), self._get_current_az())

    def is_close_to_target(self):
        """Returns true if telescope is close enough to observe, else False."""
        cal, caz = self.get_current_alaz()
        tal, taz = self.get_target_alaz()
        dist = self._get_angular_distance(cal, caz, tal, taz)
        if dist< self.close_enough_distance:
            return True
        else:
            return False
        

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

