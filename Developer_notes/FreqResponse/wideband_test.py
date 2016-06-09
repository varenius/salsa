import sys
import ephem
sys.path.append('/opt/salsa/controller/')
from measurement import *
from telescope import *
import numpy as np
import getpass # To find current username
import ConfigParser
import matplotlib.pyplot as plt

configfile = '/opt/salsa/controller/SALSA.config'
# Set current username, used for tmp files and spectrum uploads
observer = getpass.getuser()
# Set config file location
config = ConfigParser.ConfigParser()
config.read(configfile)
# Initialise telescope and UI
telescope = TelescopeController(config)
calt_deg, caz_deg = telescope.get_current_alaz()

calfact =  int(config.get('USRP', 'software_gain'))
print calfact
freqs = np.linspace(1000,2000,100)*1e6 # Hz
print freqs
sys.exit()
#freqs = np.array([1410, 1430])*1e6 # Hz
totpows = []
for freq in freqs:
    telescope.set_LNA(True)
    time.sleep(1)
    measurement = Measurement(freq, 2, 2.5*1e6, calt_deg, caz_deg, telescope.site, 4096, observer, config, 0, 0, calfact)
    measurement.measure()
    telescope.set_LNA(False)
    spec = measurement.spectrum
    spec.auto_edit_bad_data()
    totpow = spec.get_total_power()
    totpows.append(totpow)
    print freq, totpow
print freqs/1.0e9
print totpows
plt.plot(freqs, totpows)
plt.show()

