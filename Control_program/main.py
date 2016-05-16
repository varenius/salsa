#!/usr/bin/env python
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar2QTAgg
import sys
import ephem
from PyQt4 import QtGui, QtCore
sys.path.append('./')
from telescope import *
from measurement import *
from UI import Ui_MainWindow
import numpy as np
import getpass # To find current username
import ConfigParser

# Make sure only one instance is running of this program
from tendo import singleton
me = singleton.SingleInstance() # will sys.exit(-1) if other instance is running

##### SET CONFIG FILE #######
configfile = os.path.dirname(__file__) + '/SALSA.config'
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
        # Dict used to store spectra observed in this session
        self.spectra = {}
        # Set current username, used for tmp files and spectrum uploads
        self.observer = getpass.getuser()
        # Set config file location
        self.config = ConfigParser.ConfigParser()
        self.config.read(configfile)
        # Initialise telescope and UI
        self.telescope = TelescopeController(self.config) 
        self.setupUi(self)
        self.init_Ui()

        # Check if telescope knows where it is (position can be lost e.g. during powercut).
        if self.telescope.get_pos_ok():
            print "Welcome to SALSA. Telescope says it is ready to observe."
        else:
            self.reset_needed()
    
    def init_Ui(self):
            
        # Set software gain
        self.gain.setText(self.config.get('USRP', 'software_gain'))

        self.listWidget_spectra.currentItemChanged.connect(self.change_spectra)

        # Define progresstimer
        self.clear_progressbar()
        self.progresstimer = QtCore.QTimer()
        self.progresstimer.timeout.connect(self.update_progressbar)

        # Define and run UiTimer
        self.uitimer = QtCore.QTimer()
        self.uitimer.timeout.connect(self.update_Ui)
        self.uitimer.start(1000) #ms

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
        self.tracking = False
        self.btn_track.clicked.connect(self.track_or_stop)
        self.btn_reset.clicked.connect(self.reset)

        # Make sure Ui is updated when changing target
        self.coordselector.currentIndexChanged.connect(self.update_Ui)
        # Make sure special targets like "The Sun" are handled correctly.
        self.coordselector.currentIndexChanged.connect(self.update_desired_target)

        # RECEIVER CONTROL
        self.btn_observe.clicked.connect(self.observe)
        self.btn_observe.clicked.connect(self.disable_receiver_controls)
        self.btn_abort.clicked.connect(self.abort_obs)
        self.btn_abort.setEnabled(False)

        # Plotting and saving
        self.btn_upload.clicked.connect(self.send_to_webarchive)

        # ADD MATPLOTLIB CANVAS, based on:
        # http://stackoverflow.com/questions/12459811/how-to-embed-matplotib-in-pyqt-for-dummies
        # a figure instance to plot on
        self.figure = plt.figure()
        self.figure.patch.set_facecolor('white')
        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self.groupBox_spectrum)
        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self.groupBox_spectrum)
        # set the layout
        # Position as left, top, width, height
        #self.canvas.setGeometry(QtCore.QRect(20, 20, 500, 380)
        plotwinlayout = QtGui.QVBoxLayout()
        plotwinlayout.addWidget(self.canvas)
        plotwinlayout.addWidget(self.toolbar)
        self.groupBox_spectrum.setLayout(plotwinlayout)
        self.radioButton_frequency.toggled.connect(self.change_spectra)
        

    def change_spectra(self):
        # Plot spectra of currently selected item
        spectrum = self.spectra[str(self.listWidget_spectra.currentItem().text())]
        self.plot(spectrum)
        spectrum.print_total_power()
        if spectrum.uploaded:
            self.btn_upload.setEnabled(False)
        else:
            self.btn_upload.setEnabled(True)

    def clear_progressbar(self):
        self.lapsedtime = 0
        target = int(self.IntegrationTimeInput.text())
        if self.mode_switched.isChecked():
            target *=2
        overhead = int(0.1*target) # Calculate extra time for processing, stacking etc.
        target +=  max(1,overhead) # Add extra time, at least 1 second
        self.expectedtime = target
        self.progressBar.setValue(100*self.lapsedtime/self.expectedtime)

    def update_progressbar(self):
        self.lapsedtime += 1
        self.progressBar.setValue(100*self.lapsedtime/self.expectedtime)

    def disable_receiver_controls(self):
        self.FrequencyInput.setReadOnly(True)
        self.RefFreqInput.setReadOnly(True)
        self.BandwidthInput.setReadOnly(True)
        self.IntegrationTimeInput.setReadOnly(True)
        self.ChannelsInput.setReadOnly(True)
        self.autoedit_bad_data_checkBox.setEnabled(False)
        self.mode_switched.setEnabled(False)
        self.mode_signal.setEnabled(False)
        self.LNA_checkbox.setEnabled(False)
        self.noise_checkbox.setEnabled(False)
        self.vlsr_checkbox.setEnabled(False)
        self.btn_observe.setEnabled(False)
        self.btn_abort.setEnabled(True)
    
    def enable_receiver_controls(self):
        self.FrequencyInput.setReadOnly(False)
        self.RefFreqInput.setReadOnly(False)
        self.BandwidthInput.setReadOnly(False)
        self.IntegrationTimeInput.setReadOnly(False)
        self.ChannelsInput.setReadOnly(False)
        self.autoedit_bad_data_checkBox.setEnabled(True)
        self.mode_switched.setEnabled(True)
        self.mode_signal.setEnabled(True)
        self.LNA_checkbox.setEnabled(True)
        self.noise_checkbox.setEnabled(True)
        self.vlsr_checkbox.setEnabled(True)
        self.btn_observe.setEnabled(True)
        self.btn_abort.setEnabled(False)

    def observation_finished(self):
        # Turn off LNA after observation
        self.telescope.set_LNA(False)
        self.telescope.set_noise_diode(False)
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
                sigspec.data = (sigspec.data - refspec.data)/(refspec.data)
            # Average to desired number of channels
            nchans = self.sigworker.measurement.noutchans
            sigspec.decimate_channels(nchans)
            # Correct VLSR
            if self.vlsr_checkbox.isChecked():
                print 'Translating freq/vel to LSR frame of reference.'
                sigspec.shift_to_vlsr_frame()
            # Store final spectra in list of observations
            date = str(sigspec.site.date.datetime().replace(microsecond=0))
            self.spectra[date] = sigspec
            item = QtGui.QListWidgetItem(date, self.listWidget_spectra)
            self.listWidget_spectra.setCurrentItem(item)
        self.aborting = False
        self.progresstimer.stop()
        self.clear_progressbar()
        self.enable_receiver_controls()

    def send_to_webarchive(self):
        date = str(self.listWidget_spectra.currentItem().text())
        spectrum = self.spectra[date]
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
        print "Aborting measurement."
        self.aborting = True
        if hasattr(self, 'sigthread'):
            self.sigworker.measurement.receiver.stop()
            self.sigthread.quit()
        # TODO: clean up temp data file.
        self.enable_receiver_controls()
    
    def observe(self):
        self.aborting = False
        self.btn_abort.setEnabled(True)
        self.btn_observe.setEnabled(False)
        self.clear_progressbar()
        self.progresstimer.start(1000) # ms
        
        # Use LNA if selected
        if self.LNA_checkbox.isChecked():
            self.telescope.set_LNA(True)
        # Use noise diode if selected
        if self.noise_checkbox.isChecked():
            self.telescope.set_noise_diode(True)
            
        sig_freq = float(self.FrequencyInput.text())*1e6 # Hz
        ref_freq = float(self.RefFreqInput.text())*1e6
        bw = float(self.BandwidthInput.text())*1e6 # Hz
        int_time = float(self.IntegrationTimeInput.text())
        nchans = int(self.ChannelsInput.text()) # Number of output channels
        calfact = float(self.gain.text()) # Gain for calibrating antenna temperature
        self.telescope.site.date = ephem.now()
        switched = self.mode_switched.isChecked()
        # Get ra, dec using radec_of. This function
        # has input order AZ, ALT, i.e. inverted to most other functions.
        # Then, make ephem object to pass to measurement
        (calt_deg, caz_deg) = self.telescope.get_current_alaz()
        (coff_alt, coff_az) = self.get_desired_alaz_offset()
        
        self.sigworker = Worker()
        self.sigthread = Thread() # Create thread to run GNURadio in background
        self.sigthread.setTerminationEnabled(True)
        self.sigworker.moveToThread(self.sigthread)
<<<<<<< HEAD
        self.sigworker.measurement = Measurement(sig_freq, ref_freq, switched, int_time, bw, calt_deg, caz_deg, self.telescope.site, nchans, self.observer, self.config, coff_alt, coff_az)
=======
        self.sigworker.measurement = Measurement(freq, int_time, bw, calt_deg, caz_deg, self.telescope.site, nchans, self.observer, self.config, coff_alt, coff_az, calfact)
>>>>>>> upstream/master
        self.sigthread.started.connect(self.sigworker.work)
        self.sigworker.finished.connect(self.sigthread.quit)
        self.sigworker.finished.connect(self.observation_finished)
        self.sigthread.start()
<<<<<<< HEAD
=======
    
    def observe_ref(self):
        if not hasattr(self, 'aborting'):
            self.aborting = False
        if not self.aborting:
            reffreq = float(self.RefFreqInput.text())*1e6 # Hz
            bw = float(self.BandwidthInput.text())*1e6 # Hz
            int_time = float(self.IntegrationTimeInput.text())
            nchans = int(self.ChannelsInput.text()) # Number of output channels
            calfact = float(self.gain.text()) # Gain for calibrating antenna temperature
            # Get ra, dec using radec_of. This function
            # has input order AZ, ALT, i.e. inverted to most other functions.
            # Then, make ephem object to pass to measurement
            (calt_deg, caz_deg) = self.telescope.get_current_alaz()
            (coff_alt, coff_az) = self.get_desired_alaz_offset()
            self.refworker = Worker()
            self.refthread = Thread() # Create thread to run GNURadio in background
            self.refthread.setTerminationEnabled(True)
            self.refworker.moveToThread(self.refthread)
            self.refworker.measurement = Measurement(reffreq, int_time, bw, calt_deg, caz_deg, self.telescope.site, nchans, self.observer, self.config, coff_alt, coff_az, calfact)
            self.refthread.started.connect(self.refworker.work)
            self.refworker.finished.connect(self.refthread.quit)
            # When obs is finished, process data and plot
            self.refthread.finished.connect(self.observation_finished)
            # Start ref when target is finished
            self.refthread.start()
        else:
            self.observation_finished()
>>>>>>> upstream/master
        
    def plot(self, spectpl):
        plt.clf()
        ax = self.figure.add_subplot(111)
        # create an axis
        preephem = time.time()
        # Get data and info
        pos = ephem.Galactic(spectpl.target)
        glon = str(pos.lon)
        glat = str(pos.lat)
        if (spectpl.vlsr_corr!=0):
            if self.radioButton_velocity.isChecked():
                x = 1e-3 * (spectpl.get_vels())
            else:
                x = 1e-6*(spectpl.get_freqs() )-1420.4
        else:
            if self.radioButton_velocity.isChecked():
                x = 1e-3 * (spectpl.get_vels() - spectpl.vlsr_corr)
            else:
                x = 1e-6*(spectpl.get_freqs() - spectpl.freq_vlsr_corr )-1420.4
        y = spectpl.data
        ax.plot(x,y, '-')
        if (spectpl.vlsr_corr!=0):
            if self.radioButton_velocity.isChecked():
                ax.set_xlabel('Velocity shifted to LSR [km/s]')
            else:
                ax.set_xlabel('Freq. shifted to LSR - 1420.4 [Mhz]')
        else:
            if self.radioButton_velocity.isChecked():
                ax.set_xlabel('Velocity relative to observer [km/s]')
            else:
                ax.set_xlabel('Measured freq.-1420.4 [MHz]')
        ax.set_ylabel('Uncalibrated antenna temperature [K]')
        ax.minorticks_on()
        ax.tick_params('both', length=6, width=0.5, which='minor')
        ax.set_title('Galactic long=' + glon + ', lat='+glat)
        #ax.autoscale_view('tight')
        ax.grid(True, color='k', linestyle='-', linewidth=0.5)
        # refresh canvas
        self.canvas.draw()

    def clear_plot(self):
        self.figure.clf()

    def update_Ui(self):
        self.update_desired_altaz()
        self.update_current_altaz()
        self.update_coord_labels()

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

    def update_desired_altaz(self):
        (alt, az) = self.calculate_desired_alaz()
        leftval = str(ephem.degrees(alt*np.pi/180.0))
        rightval = str(ephem.degrees(az*np.pi/180.0))
        self.calc_des_left.setText(leftval)
        self.calc_des_right.setText(rightval)
    
    def update_current_altaz(self):
        (alt, az) = self.telescope.get_current_alaz()
        leftval = str(ephem.degrees(alt*np.pi/180.0))
        rightval = str(ephem.degrees(az*np.pi/180.0))
        self.cur_alt.setText(leftval)
        self.cur_az.setText(rightval)
        # Color coding works, but what about color blind people?
        # Should perhaps use blue and yellow?
        if self.telescope.is_close_to_target():
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

    def get_desired_alaz_offset(self):
        # Read specified offset
        # Convert from QString to String to not confuse ephem,then to decimal degrees in case the string had XX:XX:XX.XX format.
        try:
            offset_alt_deg = float(ephem.degrees(str(self.offset_left.text())))*180.0/np.pi
            offset_az_deg= float(ephem.degrees(str(self.offset_right.text())))*180.0/np.pi
        except ValueError:
            offset_alt_deg = 0.0
            offset_az_deg = 0.0
       
        return (offset_alt_deg, offset_az_deg)

    def calculate_desired_alaz(self):
	"""Calculates the desired alt/az for the current time based on current desired target position."""
        target = self.coordselector.currentText()

        # Convert from QString to String to not confuse ephem
        leftcoord = str(self.inputleftcoord.text())
        rightcoord= str(self.inputrightcoord.text())
        
        # Get current offset
        (offset_alt_deg, offset_az_deg) = self.get_desired_alaz_offset()

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
        elif target == 'Stow':
            # Read stow position from file
            (alt_deg,az_deg)=self.telescope.get_stow_alaz()
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
        
        # Include possible offset, e.g. for beam observations on the Sun
        fin_alt_deg = alt_deg + offset_alt_deg
        fin_az_deg = az_deg + offset_az_deg

        if target == 'Horizontal':
            return (fin_alt_deg, fin_az_deg)
        elif target=='Stow':
            # Ignore offset
            return (alt_deg, az_deg)
        else:
            # Check if the desired direction is best reached via simple alt, az
            # or at 180-alt, az+180.
            flip_alt_deg = 180-fin_alt_deg
            flip_az_deg = (fin_az_deg+180)%360
            # Check if directions are reachable
            finreach = self.telescope.can_reach(fin_alt_deg, fin_az_deg) 
            flipreach = self.telescope.can_reach(flip_alt_deg, flip_az_deg) 
            # If flip direction cannot be reached, return original one.
            # (even if this one may not be reached)
            if not flipreach:
                return (fin_alt_deg, fin_az_deg)
            # But, if flip direction can be reached, but not original one,
            # then we have to go to flipdirection to point to this position
            # E.g. in mecanically forbidden azimuth range
            elif flipreach and (not finreach):
                return (flip_alt_deg, flip_az_deg)
            # If both directions are valid, which is the most common case,
            # then we find the closest one (in azimuth driving, not in angular distance)
            # to the current pointing
            elif flipreach and finreach: 
                (calt_deg, caz_deg) = self.telescope.get_current_alaz()
                flipd = self.telescope.get_azimuth_distance(caz_deg, flip_az_deg)
                find = self.telescope.get_azimuth_distance(caz_deg, fin_az_deg)
                if flipd<find:
                    return (flip_alt_deg, flip_az_deg)
                else:
                    return (fin_alt_deg, fin_az_deg)

    def set_telescope_target(self):
	"""Set the target position of the telescope from chosen values and
        coordinate system."""
        (alt_deg, az_deg) = self.calculate_desired_alaz()
        self.telescope.set_target_alaz(alt_deg, az_deg)

    def track_or_stop(self):
        if self.trackingtimer.isActive():
            self.stop()
        else:
            self.start_tracking()
    
    def disable_movement_controls(self):
        self.inputleftcoord.setReadOnly(True)
        self.inputrightcoord.setReadOnly(True)
        self.offset_left.setReadOnly(True)
        self.offset_right.setReadOnly(True)
        self.btn_reset.setEnabled(False)
        self.coordselector.setEnabled(False)
        self.btn_track.setText('Stop')
        style = "QWidget { background-color:red;}"
        self.btn_track.setStyleSheet(style)
    
    def enable_movement_controls(self):
        self.inputleftcoord.setReadOnly(False)
        self.inputrightcoord.setReadOnly(False)
        self.offset_left.setReadOnly(False)
        self.offset_right.setReadOnly(False)
        self.trackingtimer.stop()
        self.btn_track.setEnabled(True)
        self.btn_reset.setEnabled(True)
        self.coordselector.setEnabled(True)
        self.btn_track.setText('Track')
        style = "QWidget {}"
        self.btn_track.setStyleSheet(style)

    def start_tracking(self):
        try:
            # This includes a check if position is reachable
            self.set_telescope_target()
            self.update_desired_altaz()
            # Toggle tracking on
            self.trackingtimer.start(1000) # ms
            # Do not wait for tracking timer first time, 
            # start tracking directly.
            self.disable_movement_controls()
            self.track()
        except Exception as e: 
            self.show_message(e.message)

    def show_message(self, m):
        QtGui.QMessageBox.about(self, "Message from telescope:", m)

    def track(self):
        try:
            self.set_telescope_target()
        except Exception as e: 
            print e.message
            self.stop()

    def stop(self):
        self.telescope.stop()
        self.enable_movement_controls()

    def reset_needed(self):
        # Telescope must apparently be resetted
        self.btn_track.setEnabled(False)
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
        self.btn_track.setEnabled(False)
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
