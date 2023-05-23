#!/usr/bin/python3
from telescope import *
import configparser
from measurement import *
import ephem
# Allow CTRL-C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

def getdata(tobs, conf, tel, alt, az):
    sig_freq = 1410e6
    ref_freq = 0
    switched = False
    int_time = 0
    sig_time = tobs # Seconds
    ref_time = 0
    bw = 2.5e6 # Hz
    calt_deg = alt
    caz_deg = az
    site = tel.site
    nchans = 256
    observer = "sunlog"
    conf = conf
    coff_alt = 0
    coff_az = 0
    usrp_gain = int(conf.get('USRP', 'usrp_gain'))
    coordsys =  "The Sun"
    satellite = ""
    measurement = Measurement(sig_freq, ref_freq, switched, int_time, sig_time, ref_time, bw, calt_deg, caz_deg, site, nchans, observer, conf, coff_alt, coff_az, usrp_gain, coordsys, satellite)
    measurement.measure()
    #time.sleep(sig_time + 2)

    sigspec = measurement.signal_spec
    sigspec.auto_edit_bad_data()
    # Average to desired number of channels
    nchans = measurement.noutchans
    sigspec.decimate_channels(nchans)
    global reflevel
    if reflevel <0:
        reflevel = sigspec.get_total_power()
        res = "REF at {} : Power= {:6.1f} alt= {:6.1f} az= {:6.1f}".format(ephem.now(), reflevel, alt, az)
    else:
        fglevel = sigspec.get_total_power()
        res = "SUN at {} : Power= {:6.1f} alt= {:6.1f} az= {:6.1f} REF(az-10)={:6.1f}".format(ephem.now(), fglevel, alt, az, reflevel)
        reflevel = -1
        of = open(outfile,"a")
        of.write(res+"\n")
        of.close()
    print(res)

def getsun(tel):
    tel.site.date = ephem.now()
    pos = ephem.Sun()
    pos.compute(tel.site) # Needed for the sun since depending on time
    eqpos = ephem.Equatorial(pos)
    fixedbody = ephem.FixedBody()
    fixedbody._ra = eqpos.ra
    fixedbody._dec = eqpos.dec
    fixedbody._epoch = eqpos.epoch
    fixedbody.compute(tel.site)
    alt = fixedbody.alt
    az = fixedbody.az
    alt_deg = round(float(alt)*180.0/np.pi,1)
    az_deg = round(float(az)*180.0/np.pi,1)
    return alt_deg, az_deg
    
def trackormeasure():
    tal, taz = getsun(telescope)
    cal, caz = telescope.get_current_alaz()
    if reflevel <0:
        tar = "Ref"
        #Measure background level, offset by 8 degrees
        taz = taz - 8
    else:
        tar = "The Sun"
    dist = telescope._get_angular_distance(cal, caz, tal, taz)
    if dist<0.2:
        print("Taking data at ", tar, ": alt ", round(cal,1), " az ", round(caz,1))
        getdata(2, config, telescope, cal, caz)
    else:
        print("SLEWING to ", tar, ": alt ", round(tal,1), " az ", round(taz,1), ". ", round(dist,1), " deg to go...")
        telescope.set_target_alaz(tal, taz)

if not len(sys.argv)==2:
    print("Please give outfile to store data as 'script.py OUTFILE'")
    sys.exit()
print("Starting SALSA Sun logging software...")
outfile = sys.argv[1]
app = QtWidgets.QApplication(sys.argv)
##### SET CONFIG FILE #######
#scriptpath = os.path.dirname(os.path.realpath(__file__))
#configfile = scriptpath + '/SALSA.config'
configfile = '/opt/salsa/controller/SALSA.config'
# Set config file location
config = configparser.ConfigParser()
config.read(configfile)
telescope = TelescopeController(config)
reflevel = -1

print("... loaded. Will track Sun and write output data to specified file ", outfile)
print("NOTE: Press CTRL-C to stop!")
# Create timer used to check tracking and do measurements
clock = QtCore.QTimer()
clock.timeout.connect(trackormeasure)
clock.start(5000) # ms.
sys.exit(app.exec_())

