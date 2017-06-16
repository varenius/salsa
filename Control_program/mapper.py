#!/usr/bin/env python
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar2QTAgg
import sys
import ephem
from PyQt4 import QtGui, QtCore
sys.path.append('./')
from telescope import *
from measurement import *
from mapper_UI import Ui_MainWindow
import numpy as np
import getpass # To find current username
import ConfigParser
from scipy.optimize import curve_fit

# Make sure only one instance is running of this program
from tendo import singleton
me = singleton.SingleInstance() # will sys.exit(-1) if other instance is running

##### SET CONFIG FILE #######
configfile = os.path.dirname(__file__) + '/SALSA.config'
#configfile = './SALSA.config'
#############################

# Customize NavigatinoToolBarcalsss
class NavigationToolbar(NavigationToolbar2QTAgg):
    # only display the buttons we need/want
    toolitems = [t for t in NavigationToolbar2QTAgg.toolitems if
                 t[0] in ('Home','Pan','Zoom')]

# Define object used to run GNUradio in a separate QThread, according to:
# http://stackoverflow.com/questions/6783194/background-thread-with-qthread-in-pyqt
# TODO: Move to measurement class?
class Worker(QtCore.QObject):
    finished = QtCore.pyqtSignal()

    @QtCore.pyqtSlot()
    def work(self):
        self.measurement.measure()
        self.finished.emit()

# Implement custom Thread class, according to:
# http://stackoverflow.com/questions/6783194/background-thread-with-qthread-in-pyqt
class Thread(QtCore.QThread):
    def __init__(self, parent=None):
        QtCore.QThread.__init__(self, parent)

    def start(self):
        QtCore.QThread.start(self)

    def run(self):
        QtCore.QThread.run(self)

class main_window(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(main_window, self).__init__()
        # Dict used to store maps observed in this session
        self.maps = {}
        # Set current username, used for tmp files and spectrum uploads
        self.observer = getpass.getuser()
        # Set config file location
        self.config = ConfigParser.ConfigParser()
        self.config.read(configfile)
        # Initialise telescope and UI
        self.telescope = TelescopeController(self.config)
        self.setupUi(self)
        self.init_Ui()
        self.setWindowTitle("SALSA mapper: " + self.telescope.site.name)
        self.leftpos = [0,]
        self.rightpos = [0,]
        self.leftiter = 0
        self.rightiter = 0
        self.recording = False

        # Check if telescope knows where it is (position can be lost e.g. during powercut).
        if self.telescope.get_pos_ok():
            print "Welcome to SALSA. Telescope says it is ready to observe."
        else:
            self.reset_needed()
    
    def init_Ui(self):
            
        # Set software gain
        self.gain.setText(self.config.get('USRP', 'software_gain'))

        self.listWidget_measurements.currentItemChanged.connect(self.change_measurement)

        # Define progresstimer
        self.clear_progressbar()
        self.progresstimer = QtCore.QTimer()
        self.progresstimer.timeout.connect(self.update_progressbar)

        # Define and run UiTimer
        self.uitimer = QtCore.QTimer()
        self.uitimer.timeout.connect(self.update_Ui)
        self.uitimer.start(250) #ms

        # Create timer used to toggle (and update) tracking
        # Do not start this, started by user on Track button.
        self.trackingtimer = QtCore.QTimer()
        self.trackingtimer.timeout.connect(self.track) 
        
        # Reset needs its own timer to be able
        # to check if reset position has been reached
        # and then, only then, enable GUI input again.
        self.resettimer = QtCore.QTimer()
        self.resettimer.timeout.connect(self.resettimer_action)

        # Initialise buttons and tracking status.
        self.btn_reset.clicked.connect(self.reset)
        self.btn_fit.clicked.connect(self.fit_gauss)

        # Make sure Ui is updated when changing target
        self.coordselector.currentIndexChanged.connect(self.update_Ui)
        # Make sure special targets like "The Sun" are handled correctly.
        self.coordselector.currentIndexChanged.connect(self.update_desired_target)
        self.update_desired_target()

        # Measurement control
        self.btn_observe.clicked.connect(self.measure_grid)
        self.btn_observe.clicked.connect(self.disable_receiver_controls)
        self.btn_abort.clicked.connect(self.abort_obs)
        self.btn_abort.setEnabled(False)

        # Plotting and saving
        #self.btn_upload.clicked.connect(self.send_to_webarchive)

        # ADD MATPLOTLIB CANVAS, based on:
        # http://stackoverflow.com/questions/12459811/how-to-embed-matplotib-in-pyqt-for-dummies
        # a figure instance to plot on
        self.figure = plt.figure()
        self.figure.patch.set_facecolor('white')
        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self.groupBox_plot)
        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self.groupBox_plot)
        # set the layout
        # Position as left, top, width, height
        #self.canvas.setGeometry(QtCore.QRect(20, 20, 500, 380)
        plotwinlayout = QtGui.QVBoxLayout()
        plotwinlayout.addWidget(self.canvas)
        plotwinlayout.addWidget(self.toolbar)
        self.groupBox_plot.setLayout(plotwinlayout)

    def disable_receiver_controls(self):
        self.FrequencyInput.setReadOnly(True)
        self.RefFreqInput.setReadOnly(True)
        self.BandwidthInput.setReadOnly(True)
        self.ChannelsInput.setReadOnly(True)
        self.autoedit_bad_data_checkBox.setEnabled(False)
        self.mode_switched.setEnabled(False)
        self.mode_signal.setEnabled(False)
        self.LNA_checkbox.setEnabled(False)
        self.noise_checkbox.setEnabled(False)
        self.cycle_checkbox.setEnabled(False)
        self.vlsr_checkbox.setEnabled(False)
        self.btn_observe.setEnabled(False)
        self.btn_abort.setEnabled(True)
        self.sig_time_spinbox.setEnabled(False)
        self.ref_time_spinBox.setEnabled(False)
    
    def enable_receiver_controls(self):
        self.FrequencyInput.setReadOnly(False)
        self.RefFreqInput.setReadOnly(False)
        self.BandwidthInput.setReadOnly(False)
        self.ChannelsInput.setReadOnly(False)
        self.autoedit_bad_data_checkBox.setEnabled(True)
        self.cycle_checkbox.setEnabled(True)
        self.mode_switched.setEnabled(True)
        self.mode_signal.setEnabled(True)
        self.LNA_checkbox.setEnabled(True)
        self.noise_checkbox.setEnabled(True)
        self.vlsr_checkbox.setEnabled(True)
        self.sig_time_spinbox.setEnabled(True)
        self.ref_time_spinBox.setEnabled(True)
    
    def disable_movement_controls(self):
        self.inputleftcoord.setReadOnly(True)
        self.inputrightcoord.setReadOnly(True)
        self.offset_left.setReadOnly(True)
        self.offset_right.setReadOnly(True)
        self.nsteps_left.setReadOnly(True)
        self.nsteps_right.setReadOnly(True)
        self.btn_reset.setEnabled(False)
        self.coordselector.setEnabled(False)
        self.coordselector_steps.setEnabled(False)
    
    def enable_movement_controls(self):
        self.inputleftcoord.setReadOnly(False)
        self.inputrightcoord.setReadOnly(False)
        self.offset_left.setReadOnly(False)
        self.offset_right.setReadOnly(False)
        self.nsteps_left.setReadOnly(False)
        self.nsteps_right.setReadOnly(False)
        self.coordselector.setEnabled(True)
        self.coordselector_steps.setEnabled(True)

    def clear_progressbar(self):
        self.progressBar.setValue(0)

    def update_progressbar(self):
        nleft = len(self.leftpos)
        nright = len(self.rightpos)
        if self.leftiter % 2 == 0:
            rightprog = self.rightiter
        else:
            rightprog = (nright-self.rightiter)
        ratio = ((self.leftiter*nright) + rightprog)*1.0/(nleft*nright)
        self.progressBar.setValue(100*ratio)

    def update_desired_altaz(self):
        (alt, az) = self.calculate_desired_alaz()
        leftval = str(ephem.degrees(alt*np.pi/180.0))
        rightval = str(ephem.degrees(az*np.pi/180.0))
        self.calc_des_left.setText(leftval)
        self.calc_des_right.setText(rightval)
    
    def calculate_desired_alaz(self):
	"""Calculates the desired alt/az for the current time based on current desired target position."""
        target = self.coordselector.currentText()

        # Convert from QString to String to not confuse ephem
        leftcoord = str(self.inputleftcoord.text())
        rightcoord= str(self.inputrightcoord.text())
	
	# Calculate offset values in desired unit
        offsetsys = self.coordselector_steps.currentText()
        # Read specified offset grid
        # Convert from QString to String to not confuse ephem,then to decimal degrees in case the string had XX:XX:XX.XX format.
        try:
            offset_left = float(ephem.degrees(str(self.offset_left.text())))*180.0/np.pi
            offset_right= float(ephem.degrees(str(self.offset_right.text())))*180.0/np.pi
            nsteps_left = max(float(self.nsteps_left.text()),1)
            nsteps_right= max(float(self.nsteps_right.text()),1)
	    gs_left = offset_left*(nsteps_left-1)
	    gs_right = offset_right*(nsteps_right-1)
            if gs_left ==0:
                offsets_left = np.array([0.0])
            else:
	        offsets_left = np.linspace(-0.5*gs_left,0.5*gs_left,num=nsteps_left)
            if gs_right ==0:
                offsets_right = np.array([0.0])
            else:
	        offsets_right = np.linspace(-0.5*gs_right,0.5*gs_right,num=nsteps_right)
        except ValueError, IndexError:
            offsets_left = np.array([0.0])
            offsets_right = np.array([0.0])
        
        # Reset values in case they are "The Sun"
        # since otherwise errors appear when switchin from "The Sun"-mode 
        # to something else
        try:
            ephem.degrees(leftcoord)
            ephem.degrees(rightcoord)
        except ValueError:
            leftcoord = 0.0
            rightcoord = 0.0

        self.telescope.site.date = ephem.now()
        if target == 'Horizontal':
            alt = ephem.degrees(leftcoord)
            az = ephem.degrees(rightcoord)
            # Make sure azimut is given in interval 0 to 360 degrees.
            #az = (float(rightcoord) %360.0)* np.pi/180.0
            # Save as targetpos, will be minor offset because of radec_of conversion
            # Note reverse order of az, alt in this radec_of-function.
            #(ra, dec) = self.telescope.site.radec_of(az, alt)
            #pos = ephem.FixedBody()
            #pos._ra = ra
            #pos._dec = dec
            #pos._epoch = self.telescope.site.date
            #pos.compute(self.telescope.site)
            # Do not set position to tracking target in this case, because of radec_of discrepancy.
            # Instead set to given values manually
            alt_deg = float(alt)*180.0/np.pi
            az_deg = float(az)*180.0/np.pi
            
            # Assume offset values are given in Horizontal system
            self.leftpos = alt_deg + offsets_left
            self.rightpos = az_deg + offsets_right
            return (self.leftpos[self.leftiter], self.rightpos[self.rightiter])

        elif target == 'Stow':
            # Read stow position from file
            (alt_deg,az_deg)=self.telescope.get_stow_alaz()
            # Assume offset values are given in Horizontal system
            self.leftpos = alt_deg + offsets_left
            self.rightpos = az_deg + offsets_right
            return (self.leftpos[self.leftiter], self.rightpos[self.rightiter])

        else:
            # If given system is something else, we do not have to use radec_of and we get
            # http://stackoverflow.com/questions/11169523/how-to-compute-alt-az-for-given-galactic-coordinate-glon-glat-with-pyephem
            if target == 'The Sun':
                pos = ephem.Sun()
                pos.compute(self.telescope.site) # Needed for the sun since depending on time
            elif target == 'The Moon':
                pos = ephem.Moon()
                pos.compute(self.telescope.site) # Needed for the moon since depending on time
            elif target == 'Cas. A':
                pos = ephem.Equatorial(ephem.hours('23:23:26'), ephem.degrees('58:48:0'), epoch=ephem.J2000)
                # Coordinate from http://en.wikipedia.org/wiki/Cassiopeia_A
            elif target == 'Galactic':
                pos = ephem.Galactic(ephem.degrees(leftcoord), ephem.degrees(rightcoord))
            elif target == 'Eq. J2000':
                pos = ephem.Equatorial(ephem.hours(leftcoord), ephem.degrees(rightcoord), epoch=ephem.J2000)
            elif target == 'Eq. B1950':
                pos = ephem.Equatorial(ephem.hours(leftcoord), ephem.degrees(rightcoord), epoch=ephem.B1950)
            elif target == 'Ecliptic':
                pos = ephem.Ecliptic(ephem.degrees(leftcoord), ephem.degrees(rightcoord)) # Use some epoch?
                #pos = ephem.Ecliptic(ephem.degrees(leftcoord), ephem.degrees(rightcoord), epoch=ephem.J2000)
            # Calculate alt, az, via fixedbody since only fixed body has alt, az
            # First needs to make sure we have equatorial coordinates
            eqpos = ephem.Equatorial(pos)
            fixedbody = ephem.FixedBody()
            fixedbody._ra = eqpos.ra
            fixedbody._dec = eqpos.dec
            fixedbody._epoch = eqpos.epoch
            fixedbody.compute(self.telescope.site)
            alt = fixedbody.alt
            az = fixedbody.az
            alt_deg = float(alt)*180.0/np.pi
            az_deg = float(az)*180.0/np.pi
        
            # Assume offset values are given in Horizontal system
            leftpos = alt_deg + offsets_left
            rightpos = az_deg + offsets_right
            self.leftpos = leftpos
            self.rightpos = rightpos
            return (self.leftpos[self.leftiter], self.rightpos[self.rightiter])

            #flipleft = [180-lp for lp in leftpos]
            #flipright = [(rp+180)%360 for rp in rightpos]
            # 
            ## Check if directions are reachable
            #can_reach_all = True
            #can_flipreach_all = True
            #for i in range(len(leftpos)):
            #    for j in range(len(rightpos)):
            #        # Check if the desired direction is best reached via simple alt, az
            #        # or at 180-alt, az+180.
            #        reach = self.telescope.can_reach(leftpos[i], rightpos[j]) 
            #        flipreach = self.telescope.can_reach(flipleft, flipright) 
            #        if not reach:
            #            can_reach_all = False
            #        if not flipreach:
            #            can_flipreach_all = False

            ## If flip direction cannot be reached, return original one.
            ## (even if this one may not be reached)
            #if not can_flipreach_all:
            #    self.leftpos = leftpos
            #    self.rightpos = rightpos
            #    return (self.leftpos[self.leftiter], self.rightpos[self.rightiter])

            ## But, if flip direction can be reached, but not original one,
            ## then we have to go to flipdirection to point to this position
            ## E.g. in mecanically forbidden azimuth range
            #elif flipreach and (not finreach):
            #    self.leftpos = flipleft
            #    self.rightpos = flipright
            #    return (self.leftpos[self.leftiter], self.rightpos[self.rightiter])
            ## If both directions are valid, which is the most common case,
            ## then we find the closest one (in azimuth driving, not in angular distance)
            ## to the current pointing
            #elif flipreach and finreach: 
            #    (calt_deg, caz_deg) = self.telescope.get_current_alaz()
            #    flipd = self.telescope.get_azimuth_distance(caz_deg, flip_az_deg)
            #    find = self.telescope.get_azimuth_distance(caz_deg, fin_az_deg)
            #    if flipd<find:
            #        return (flip_alt_deg, flip_az_deg)
            #    else:
            #        return (fin_alt_deg, fin_az_deg)
    
    def measure_grid(self):
        self.disable_movement_controls()
        self.disable_receiver_controls()
        self.progresstimer.start(1000) # ms
        self.aborting = False
        
        # Use LNA if selected
        if self.LNA_checkbox.isChecked():
            self.telescope.set_LNA(True)
        # Use noise diode if selected
        if self.noise_checkbox.isChecked():
            self.telescope.set_noise_diode(True)
            
        self.leftiter = 0
        self.rightiter = 0
        self.current_map = {}
        (alt_deg, az_deg) = self.calculate_desired_alaz()
	print('Moving to grid position [{0},{1}] at alt={2}, az={3}'.format(self.leftiter,self.rightiter, alt_deg, az_deg))
        self.update_desired_altaz()
        # Do not wait for tracking timer first time, 
        # start tracking directly.
        self.track()

    def track(self):
        (alt_deg, az_deg) = self.calculate_desired_alaz()
        try:
            self.telescope.set_target_alaz(alt_deg, az_deg)
            if not self.trackingtimer.isActive():
                    self.trackingtimer.start(1000) # ms
            if not self.telescope.is_moving() and not self.recording:
                    print('Position reached, starting recording...')
                    self.measure_pointing()
                    self.recording = True
        except Exception as e: 
            print e.message
            self.show_message(e.message)
            self.stop()

    def stop(self):
        self.trackingtimer.stop()
        self.telescope.stop()
        self.enable_movement_controls()
        self.enable_receiver_controls()
        self.progresstimer.stop()
        self.clear_progressbar()
        self.leftiter = 0
        self.rightiter = 0
        self.current_map = {}
        style = "QWidget { background-color:orange;}"
        self.btn_abort.setStyleSheet(style)
        self.btn_abort.setEnabled(False)
        self.btn_abort.setText('Stopping...')

    def measure_pointing(self):
        sig_freq = float(self.FrequencyInput.text())*1e6 # Hz
        ref_freq = float(self.RefFreqInput.text())*1e6
        bw = float(self.BandwidthInput.text())*1e6 # Hz
        switched = self.mode_switched.isChecked()
        if self.cycle_checkbox.isChecked():
            sig_time = float(self.sig_time_spinbox.text()) # [s]
            ref_time = float(self.ref_time_spinBox.text()) # [s]
            loops = int(self.loops_spinbox.text()) #
            int_time = (sig_time+ref_time)*loops
        else:
            if switched:
                sig_time = float(self.int_time_spinbox.text())/2
                ref_time = float(self.int_time_spinbox.text())/2
                print 'SWITCHED mode selected with cycle times of {0} seconds (signal) and {1} seconds (reference).'.format(sig_time, ref_time)
                loops = 1;
                while sig_time > 20:
                     sig_time = sig_time/2
                     ref_time = ref_time/2
                     loops = loops + 1
                int_time = (sig_time+ref_time)*loops
            else:
                sig_time = float(self.int_time_spinbox.text())
                ref_time = 0
                loops = 1
                int_time = sig_time

        nchans = int(self.ChannelsInput.text()) # Number of output channels
        calfact = float(self.gain.text()) # Gain for calibrating antenna temperature
        self.telescope.site.date = ephem.now()

        self.sigworker = Worker()
        self.sigthread = Thread() # Create thread to run GNURadio in background
        self.sigthread.setTerminationEnabled(True)
        self.sigworker.moveToThread(self.sigthread)
        (alt_deg, az_deg) = self.calculate_desired_alaz()
        self.sigworker.measurement = Measurement(sig_freq, ref_freq, switched, int_time, sig_time, ref_time, bw, alt_deg, az_deg, self.telescope.site, nchans, self.observer, self.config, 0, 0, calfact)

        self.sigthread.started.connect(self.sigworker.work)
        self.sigworker.finished.connect(self.sigthread.quit)
        self.sigworker.finished.connect(self.gridpoint_finished)
        self.sigthread.start()

    def grid_is_finished(self):
        ri = self.rightiter
        li = self.leftiter
        nr = len(self.rightpos)
        nl = len(self.leftpos)
        # If only one dim in "left", or if both nl and nr are 1
        if nl==1:
            if ri==nr-1:
                return True
            else:
                return False
        # If only one dim in "right" (and we know we have more than 1 in left)
        elif nr==1:
            if li==nl-1:
                return True
            else:
                return False
        else:
            # We have nl>1 and nr>l. Now check if even or odd number of "rows", i.e. nl.
            if nl % 2 == 0:
            # If nl is even we will end in bottom left corner, since we go leftrow by leftrow in direction +, -, +, -...
                if (ri == 0) and (li == nl-1):
                    return True
                else:
                    return False
            else:
                # nl is odd, and we will end in bottom right corner...
                if (ri == nr-1) and (li == nl-1):
                    return True
                else:
                    return False
       
    def gridpoint_finished(self):
        print('...recording finished.')
        if not self.aborting:
            # Post-process data
            sigspec = self.sigworker.measurement.signal_spec
            if self.autoedit_bad_data_checkBox.isChecked():
                print "Removing RFI from signal..."
                sigspec.auto_edit_bad_data()
            if self.mode_switched.isChecked():
                refspec = self.sigworker.measurement.reference_spec
                if self.autoedit_bad_data_checkBox.isChecked():
                    print "Removing RFI from reference..."
                    refspec.auto_edit_bad_data()
                print "Removing reference from signal..."
                sigspec.data -= refspec.data
            # Average to desired number of channels
            nchans = self.sigworker.measurement.noutchans
            sigspec.decimate_channels(nchans)
            # Correct VLSR
            if self.vlsr_checkbox.isChecked():
                print 'Translating freq/vel to LSR frame of reference.'
                sigspec.shift_to_vlsr_frame()
            # Store spectrum in current map dictionary
            self.current_map['L'+str(self.leftiter)+'R'+str(self.rightiter)] = sigspec

        if self.grid_is_finished():
            # We have reached the end of the grid! Terminate grid measurement
            # Turn off LNA after observation
            self.telescope.set_LNA(False)
            self.telescope.set_noise_diode(False)
            self.trackingtimer.stop()
            self.recording = False
            self.aborting = False
            self.enable_receiver_controls()
            self.current_map['leftpos'] = self.leftpos
            self.current_map['rightpos'] = self.rightpos
            date = str(sigspec.site.date.datetime().replace(microsecond=0))
            self.current_map['date'] = date
            self.maps[date] = self.current_map
            print self.maps.keys()
            print self.maps[date].keys()
            item = QtGui.QListWidgetItem(date, self.listWidget_measurements)
            self.listWidget_measurements.setCurrentItem(item)
            self.progresstimer.stop()
            self.clear_progressbar()
            #Make sure receiver and current thread is stopped
            if hasattr(self, 'sigthread'):
                self.sigworker.measurement.abort = True
                self.sigworker.measurement.receiver.stop()
                self.sigthread.quit()
	    print('Grid finished!')
            self.stop()
        else:
            # Check if we have finished all observations in this "left-row"
            # If so, go to next row
            if (self.rightiter == len(self.rightpos)-1) and (self.leftiter % 2 == 0):
	        self.leftiter +=1
            elif (self.rightiter == 0) and (self.leftiter % 2 != 0):
	        self.leftiter +=1
            # If we are within a row, continue alon the row
            # For even row, increase rightiter
            elif (self.leftiter % 2 == 0):
	        self.rightiter +=1
            elif (self.leftiter % 2 != 0):
	        self.rightiter -=1
	    print('Moving to grid position [{0},{1}] at alt={2}, az={3}'.format(self.leftiter,self.rightiter, self.leftpos[self.leftiter], self.rightpos[self.rightiter]))
            self.recording = False


    def send_to_webarchive(self):
        date = str(self.listWidget_measurements.currentItem().text())
        spectrum = self.maps[date]
        if not spectrum.uploaded:
            tmpdir = self.config.get('USRP', 'tmpdir')
            tmpfile = tmpdir + '/tmp_vale_' + spectrum.observer
            # Save temporary files
            txtfile = tmpfile + '.txt'
            spectrum.save_to_txt(txtfile)
            fitsfile = tmpfile + '.fits'
            spectrum.save_to_fits(fitsfile)
            pngfile = tmpfile + '.png'
            plt.savefig(pngfile) # current item
            spectrum.upload_to_archive(fitsfile, pngfile, txtfile)
            self.btn_upload.setEnabled(False)

    def abort_obs(self):
        print "Aborting measurement..."
        self.aborting = True
        if hasattr(self, 'sigthread'):
            self.sigworker.measurement.abort = True
            self.sigworker.measurement.receiver.stop()
            self.sigthread.quit()
        self.stop()
        # TODO: clean up temp data file.
        
    def change_measurement(self):
        # Plot spectra of currently selected item
        map2plot = self.maps[str(self.listWidget_measurements.currentItem().text())]
        self.plot(map2plot)
        #if spectrum.uploaded:
        #    self.btn_upload.setEnabled(False)
        #else:
        #    self.btn_upload.setEnabled(True)

    def plot(self, map2plot):
        leftpos = map2plot['leftpos']
        rightpos = map2plot['rightpos']
        nleft = len(leftpos)
        nright = len(rightpos)
        data = np.zeros((nleft,nright))
        for i in range(nleft):
            for j in range(nright):
                num = map2plot['L'+str(i)+'R'+str(j)].get_total_power()
                data[i,j] = num
        leftmid = np.mean(leftpos)
        rightmid = np.mean(rightpos)
        leftrel = leftpos - leftmid
        rightrel = rightpos - rightmid
        print 'leftrel', leftrel
        print 'rightrel',rightrel
        print 'data', data
        plt.clf()
        ax = self.figure.add_subplot(111)
        extent = [min(rightrel), max(rightrel), min(leftrel), max(leftrel)]
        if nleft>1 and nright>1:
            ax.imshow(data, origin = 'lower', interpolation = 'none', extent = extent)
            ax.set_xlabel('Relative offset [deg]')
            ax.set_ylabel('Relative offset [deg]')
        if nleft>1 and nright==1:
            ax.plot(leftrel, data.flatten(),'*')
            ax.plot(leftrel, data.flatten(),'-')
            ax.set_xlabel('Relative offset left [deg]')
            ax.set_ylabel('Arbitrary amplitude')
        if nleft==1 and nright>1:
            ax.plot(rightrel, data.flatten(),'*')
            ax.plot(rightrel, data.flatten(),'-')
            ax.set_xlabel('Relative offset right [deg]')
            ax.set_ylabel('Arbitrary amplitude')
        ax.set_title('Total power towards left={0} right={1}'.format(round(leftmid,1),round(rightmid,1)))
        ax.autoscale_view('tight')
        # refresh canvas
        self.canvas.draw()

    # Define model function to be used to fit measured beam data:
    def oneD_Gaussian(self, x, *p):
        A, mu, sigma, offset = p
        return offset + A*np.exp(-(x-mu)**2/(2.*sigma**2))
        
    # Define 2D Gaussian according to http://stackoverflow.com/questions/21566379/fitting-a-2d-gaussian-function-using-scipy-optimize-curve-fit-valueerror-and-m/21566831#21566831
    def twoD_Gaussian(self, (x, y), amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
        xo = float(xo)
        yo = float(yo)    
        a = (np.cos(theta)**2)/(2*sigma_x**2) + (np.sin(theta)**2)/(2*sigma_y**2)
        b = -(np.sin(2*theta))/(4*sigma_x**2) + (np.sin(2*theta))/(4*sigma_y**2)
        c = (np.sin(theta)**2)/(2*sigma_x**2) + (np.cos(theta)**2)/(2*sigma_y**2)
        g = offset + amplitude*np.exp( - (a*((x-xo)**2) + 2*b*(x-xo)*(y-yo) 
                            + c*((y-yo)**2)))
        return g.ravel()

    def fit_gauss(self):
        map2plot = self.maps[str(self.listWidget_measurements.currentItem().text())]
        leftpos = map2plot['leftpos']
        rightpos = map2plot['rightpos']
        nleft = len(leftpos)
        nright = len(rightpos)
        data = np.zeros((nleft,nright))
        for i in range(nleft):
            for j in range(nright):
                num = map2plot['L'+str(i)+'R'+str(j)].get_total_power()
                data[i,j] = num
        leftmid = np.mean(leftpos)
        rightmid = np.mean(rightpos)
        leftrel = leftpos - leftmid
        rightrel = rightpos - rightmid
        ax = plt.gca()
        extent = [min(rightrel), max(rightrel), min(leftrel), max(leftrel)]
        if nleft>1 and nright>1:
            # Two-D Gauss
            #ax.imshow(data, origin = 'lower', interpolation = 'none', extent = extent)
            p0 = [500, 0.0, 0.0, 5.0, 5.0, 0.0, 100] #amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
            rm, lm = np.meshgrid(rightrel, leftrel)
            popt, pcov = curve_fit(self.twoD_Gaussian, (rm, lm), np.ravel(data), p0=p0)
            fx0 = popt[1]
            fy0 = popt[2]
            fsigma_x = popt[3]
            fsigma_y = popt[4]
            print('Towards {0}, {1}: Fitted Gaussian roff={2}deg, loff={3}, FWHM1={4}deg, FWHM2={5}deg.'.format(round(leftmid,1), round(rightmid,1), fx0, fy0, fsigma_x*2.355, fsigma_y*2.355)) 
            npt = 100
            xv = np.linspace(np.min(rightrel), np.max(rightrel), npt)
            yv = np.linspace(np.min(leftrel), np.max(leftrel), npt)
            xi, yi = np.meshgrid(xv, yv)
            model = self.twoD_Gaussian((xi, yi), *popt)
            plt.contour(xi, yi, model.reshape(npt, npt), 8, colors='k')
        else:
            if nleft>1 and nright==1:
                xvals = leftrel
                yvals = data.flatten()
            if nleft==1 and nright>1:
                xvals = rightrel
                yvals = data.flatten()
            # p0 is the initial guess for the fitting coefficients (A, mu,sigma, offset)
            p0 = [max(yvals), xvals[np.where(yvals==max(yvals))], 5.0, min(yvals)]
            popt, pcov = curve_fit(self.oneD_Gaussian, xvals, yvals, p0=p0)
            #Make nice grid for fitted data
            fitx = np.linspace(min(xvals), max(xvals), 500)
            # Get the fitted curve
            fity = self.oneD_Gaussian(fitx, *popt)
            fsigma = popt[2]
            fmu = popt[1]
            fbeam = 2.355*fsigma # FWHM
            plt.plot(fitx, fity,'--', color = 'blue')
            print('Towards {0}, {1}: Fitted Gaussian mean={2}deg and FWHM={3}deg.'.format(round(leftmid,1), round(rightmid,1), fmu, fbeam)) 

        # refresh canvas
        self.canvas.draw()
        
    def clear_plot(self):
        self.figure.clf()

    def update_Ui(self):
        self.update_desired_altaz()
        self.update_current_altaz()
        self.update_coord_labels()
        if self.mode_switched.isChecked():
            self.cycle_checkbox.setEnabled(True)
            self.sig_time_spinbox.setEnabled(True)
            self.ref_time_spinBox.setEnabled(True)
            self.loops_spinbox.setEnabled(True)
            self.int_time_spinbox.setEnabled(True)
        if not self.mode_switched.isChecked():
            self.cycle_checkbox.setEnabled(False)
            self.sig_time_spinbox.setEnabled(False)
            self.ref_time_spinBox.setEnabled(False)
            self.loops_spinbox.setEnabled(False)
            self.int_time_spinbox.setEnabled(True)
            self.cycle_checkbox.setChecked(False)
        if self.cycle_checkbox.isChecked():
            self.sig_time_spinbox.setEnabled(True)
            self.ref_time_spinBox.setEnabled(True)
            self.loops_spinbox.setEnabled(True)
            self.int_time_spinbox.setEnabled(False)
        if not self.cycle_checkbox.isChecked():
            self.sig_time_spinbox.setEnabled(False)
            self.ref_time_spinBox.setEnabled(False)
            self.loops_spinbox.setEnabled(False)
            self.int_time_spinbox.setEnabled(True)

        t = float(self.int_time_spinbox.text())*len(self.leftpos)*len(self.rightpos)
        s = float(5)*len(self.leftpos)*len(self.rightpos)
        ts = 'INFO: Your grid implies {0}min recording plus slewing (estimated to {1}min assuming 5 sec/point).'.format(round(t/60.0,1), round(s/60.0,1))
        self.infolabel.setText(ts)
        if ((not self.telescope.is_moving()) and (not self.trackingtimer.isActive()) and (not self.recording)):
            self.btn_reset.setEnabled(True)
            self.btn_observe.setEnabled(True)
            self.btn_abort.setEnabled(False)
            self.btn_abort.setText('Abort')
            style = "QWidget {}"
            self.btn_abort.setStyleSheet(style)

    def update_desired_target(self):
        target = self.coordselector.currentText()
        if target == 'The Sun':
            self.inputleftcoord.setReadOnly(True)
            self.inputrightcoord.setReadOnly(True)
            self.inputleftcoord.setText('The Sun')
            self.inputrightcoord.setText('The Sun')
        elif target == 'The Moon':
            self.inputleftcoord.setReadOnly(True)
            self.inputrightcoord.setReadOnly(True)
            self.inputleftcoord.setText('The Moon')
            self.inputrightcoord.setText('The Moon')
        elif target == 'Cas. A':
            self.inputleftcoord.setReadOnly(True)
            self.inputrightcoord.setReadOnly(True)
            self.inputleftcoord.setText('Cas. A')
            self.inputrightcoord.setText('Cas. A')
        elif target == 'Stow':
            self.inputleftcoord.setReadOnly(True)
            self.inputrightcoord.setReadOnly(True)
            self.inputleftcoord.setText('Stow')
            self.inputrightcoord.setText('Stow')
        else:
            # Convert from QString to String to not confuse ephem
            leftcoord = str(self.inputleftcoord.text())
            rightcoord= str(self.inputrightcoord.text())
            # Reset values in case they are not numbers, i.e. Sun/Cas A mode.
            try:
                ephem.degrees(leftcoord)
                ephem.degrees(rightcoord)
            except ValueError:
                self.inputleftcoord.setText('0.0')
                self.inputrightcoord.setText('0.0')
            # Unlock input if not in Sun/Cas A mode.
            if not self.trackingtimer.isActive():
                self.inputleftcoord.setReadOnly(False)
                self.inputrightcoord.setReadOnly(False)

    def update_current_altaz(self):
        (alt, az) = self.telescope.get_current_alaz()
        leftval = str(ephem.degrees(alt*np.pi/180.0))
        rightval = str(ephem.degrees(az*np.pi/180.0))
        self.cur_alt.setText(leftval)
        self.cur_az.setText(rightval)
        # Color coding works, but what about color blind people?
        # Should perhaps use blue and yellow?
        if not self.telescope.is_moving():
            style = "QWidget {}"
        else:
            style = "QWidget { background-color:yellow;}"
        self.cur_alt.setStyleSheet(style)
        self.cur_az.setStyleSheet(style)
    
    def update_coord_labels(self):
        target = self.coordselector.currentText()
        if target == 'Horizontal':
            leftval = 'Altitude [deg]'
            rightval = 'Azimuth [deg]'
        elif (target == 'Galactic' or target == 'Ecliptic'):
            leftval = 'Longitude [deg]'
            rightval = 'Latitude [deg]'
        elif (target == 'Eq. J2000' or target == 'Eq. B1950'):
            leftval = 'R.A. [H:M:S]'
            rightval = 'Dec. [D:\':\"]'
        else:
            leftval = 'Object:'
            rightval = 'Object:'
        self.coordlabel_left.setText(leftval)
        self.coordlabel_right.setText(rightval)

    def show_message(self, m):
        QtGui.QMessageBox.about(self, "Message from telescope:", m)

    def reset_needed(self):
        # Telescope must apparently be resetted
        self.btn_reset.setEnabled(True)
        self.btn_observe.setEnabled(False)
        msg = "Dear user. The telescope is lost, this may happen when there is a power cut. A reset is needed for SALSA to know where it is pointing. Please press reset and wait until reset is finished."
        self.show_message(msg)
    
    def reset(self):
        # Show a message box
        qmsg = "You have asked for a system reset. This process may take a few minutes if the telescope is far from its starting position so please be patient. Do you really want to reset the telescope?"
        result = QtGui.QMessageBox.question(QtGui.QWidget(), 'Confirmation', qmsg, QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        if result==QtGui.QMessageBox.Yes:
            self.telescope.reset()
            self.resettimer.start(1000)

    def resettimer_action(self):
        self.inputleftcoord.setReadOnly(True)
        self.inputleftcoord.setText("Resetting...")
        self.inputrightcoord.setReadOnly(True)
        self.inputrightcoord.setText("Resetting...")
        self.btn_reset.setEnabled(False)
        self.coordselector.setEnabled(False)
        self.disable_receiver_controls()
        self.btn_abort.setEnabled(False)

        if self.telescope.isreset():
            self.resettimer.stop()
            # Set default values for input fields
            self.inputleftcoord.setText("140.0")
            self.inputrightcoord.setText("0.0")
            self.enable_movement_controls()
            self.enable_receiver_controls()
            # Make sure labels are properly updated again, will change input values for fixed objects like the Sun etc.
            self.update_desired_target()
            self.telescope.set_pos_ok() # Know we know where we are
            msg = "Dear user: The telescope has been reset and now knows its position. Thank you for your patience."
            self.show_message(msg)

def main():
    app = QtGui.QApplication(sys.argv)
    #app.setStyle(QtGui.QStyleFactory.create("plastique"))
    # Do not use default GTK, strange low level warnings. Others see this as well.
    app.setStyle(QtGui.QStyleFactory.create("cleanlooks"))
    window = main_window()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()    
