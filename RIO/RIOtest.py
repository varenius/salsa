import time
import sys
import ConfigParser
sys.path.append('../Control_program/')
from telescope import *

##### Use current system config file #######
configfile = '/opt/salsa/controller/SALSA.config'
#############################
config = ConfigParser.ConfigParser()
config.read(configfile)

tel = TelescopeController(config)
# Check if telescope knows where it is (position can be lost e.g. during powercut).
if tel.get_pos_ok():
    print "Welcome to SALSA. Telescope says it is ready to observe."
else:
    print "NOTE: Telescope needs reset!"

def pulse(ptime):
    cal = tel._get_current_al_cog()
    caz = tel._get_current_az_cog()
    tal = tel._get_target_al_cog()
    taz = tel._get_target_az_cog()
    #print 'Target', tal, taz
    print 'Current', cal, caz
    # Start el-motor
    print 'Starting el-motor'
    tel._cmd('SB0') # EL
    #tel._cmd('SB2') # AZ
    ans = tel._get_msg()
    #print ans
    print 'Sleeping for ' + str(ptime) + 's'
    time.sleep(ptime)
    print 'Stopping el-motor'
    tel._cmd('CB0') # EL
    #tel._cmd('CB2') # AZ
    ans = tel._get_msg()
    #print ans
    cal = tel._get_current_al_cog()
    caz = tel._get_current_az_cog()
    print 'Current', cal, caz

for i in range(5):
    pulse(0.05)
    time.sleep(1.0)
