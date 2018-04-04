#!/usr/bin/env python
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar2QTAgg
import satellites # to cope with GNSS tracking
import sys
import ephem
from PyQt4 import QtGui, QtCore
sys.path.append('./')
from telescope import *
from measurement import *
from UI import Ui_MainWindow
from UI_LH import Ui_GNSSAzElWindow # to import Az-El View window
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure,show,rc,ion,draw
from matplotlib.figure import Figure

import getpass # To find current username
import ConfigParser

# Make sure only one instance is running of this program
from tendo import singleton
me = singleton.SingleInstance() # will sys.exit(-1) if other instance is running

##### SET CONFIG FILE #######
abspath = os.path.abspath(__file__)
configfile = os.path.dirname(abspath) + '/SALSA.config'
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
        self.setWindowTitle("SALSA Controller: " + self.telescope.site.name)

        # Check if telescope knows where it is (position can be lost e.g. during powercut).
        if self.telescope.get_pos_ok():
            msg = "Welcome to SALSA. If this is your first measurement for today, please reset the telscope to make sure that it tracks the sky correctly. A small position error can accumulate if using the telescope for multiple hours, but this is fixed if you press the reset button and wait until the telescope is reset."
            print (msg)
            self.show_message(msg)
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
        self.tracking = False
        self.btn_track.clicked.connect(self.track_or_stop)
        self.btn_reset.clicked.connect(self.reset)

        # Make sure Ui is updated when changing target
        self.coordselector.currentIndexChanged.connect(self.update_Ui)
        # Make sure special targets like "The Sun" are handled correctly.
        self.coordselector.currentIndexChanged.connect(self.update_desired_target)

        # Set the GNSS-related parts of GUI to non-visible
	self.GNSS_GUI_visible(False)
        # Set the current GNSStarget to none
	self.currentGNSStarget="none"
        # Connect the activated signal on the coordselector to our handler which turns on/off the GNSS-related parts of GUI
        self.connect(self.coordselector, QtCore.SIGNAL('activated(QString)'), self.coordselector_chosen)
        # Connect the activated signal on the GNSSselector to our handler which sets the currentGNSStarget
        self.connect(self.GNSSselector, QtCore.SIGNAL('activated(QString)'), self.GNSSselector_chosen)

	# opens GNSS AzEl window after clicking the btn_GNSS_lh button
        self.btn_GNSS_lh.clicked.connect(self.open_GNSSAzEl)

        # RECEIVER CONTROL
        self.btn_observe.clicked.connect(self.observe)
        self.btn_observe.clicked.connect(self.disable_receiver_controls)
        self.btn_abort.clicked.connect(self.abort_obs)
        self.btn_abort.setEnabled(False)

        # Plotting and saving
        self.btn_upload.clicked.connect(self.send_to_webarchive)
	# store position of the telescope during measurements; used for plotting
	self.azAtMeasurementTime=0.0
	self.elAtMeasurementTime=0.0
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
        plotwinlayout = QtGui.QVBoxLayout()
        plotwinlayout.addWidget(self.canvas)
        plotwinlayout.addWidget(self.toolbar)
        self.groupBox_spectrum.setLayout(plotwinlayout)
	# replot spectra in case status of freq, dBScale or normalized has changed
        self.radioButton_frequency.toggled.connect(self.change_spectra)
        self.checkBox_dBScale.toggled.connect(self.change_spectra)
        self.checkBox_normalized.toggled.connect(self.change_spectra)
 
    def change_spectra(self):
        # Plot spectra of currently selected item
        if self.listWidget_spectra.count() >0 :
            spectrum = self.spectra[str(self.listWidget_spectra.currentItem().text())]
            self.plot(spectrum)
            spectrum.print_total_power()
            if spectrum.uploaded:
                self.btn_upload.setEnabled(False)
            else:
                self.btn_upload.setEnabled(True)

    def clear_progressbar(self):
        self.lapsedtime = 0
        if self.cycle_checkbox.isChecked():
            sig_time = int(self.sig_time_spinbox.text()) # [s]
            ref_time = int(self.ref_time_spinBox.text()) # [s]
            loops = int(self.loops_spinbox.text())
            target = int((sig_time+ref_time)*loops) 
        else:
            target = int(self.int_time_spinbox.text())
        overhead = int(0.1*target) # Calculate extra time for processing, stacking etc.
        target +=  max(1.5,overhead) #Add extra time, at least 2 second
        self.expectedtime = target
        self.progressBar.setValue(100*self.lapsedtime/self.expectedtime)

    def update_progressbar(self):
        self.lapsedtime += 1
        self.progressBar.setValue(100*self.lapsedtime/self.expectedtime)

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
        self.btn_observe.setEnabled(True)
        self.btn_abort.setEnabled(False)
        self.sig_time_spinbox.setEnabled(True)
        self.ref_time_spinBox.setEnabled(True)

    def coordselector_chosen(self, text):
        """
        The handler called when a target is chosen from the coordselector combobox.
        Turns on the GNSS-related parts of GUI if target is 'GNSS'.
        """
        if text == "GNSS":
            self.GNSS_GUI_visible(True)
        else:
            self.GNSS_GUI_visible(False)

    def GNSSselector_chosen(self, text):
        """
        Sets the currentGNSStarget based on the selected GNSS target from the GNSSselector combobox

        """
        self.currentGNSStarget=str(text)

    def GNSS_GUI_visible(self,visibility):
        """
        The handler turning on/off all GNSS-related items of GUI
        """
        if visibility == True:
	    self.GNSS_createCombobox()
	    self.GNSSselector.setVisible(True)
            self.btn_GNSS_lh.setVisible(True)
	    self.GNSS_hide_guiobjects(True)
        else:
	    self.GNSSselector.setVisible(False)
            self.btn_GNSS_lh.setVisible(False)
	    self.GNSS_hide_guiobjects(False)
	    self.GNSS_clearCombobox() 
	    self.close_GNSSAzEl()

    def GNSS_hide_guiobjects(self,visibility):
        """
        The handler turning on/off some original SALSA's GUI objects when switching to GNSS tracking
        """
        if visibility == True:
            self.inputleftcoord.setVisible(False)
            self.inputrightcoord.setVisible(False)
            self.coordlabel_left.setVisible(False)
            self.coordlabel_right.setVisible(False)
        else:
            self.inputleftcoord.setVisible(True)
            self.inputrightcoord.setVisible(True)
            self.coordlabel_left.setVisible(True)
            self.coordlabel_right.setVisible(True)

    def GNSS_createCombobox(self):
	"""
	Creates a GNSSselector combobox using a list of visible GNSS satellites
	"""
	[GNSSname,phi,r]=satellites.SatCompute('visible','ALL') # fills the list with all GNSS satellites
        self.GNSSselector.addItem('None')
	for i in range(0,len(GNSSname)):
                self.GNSSselector.addItem(GNSSname[i])
	self.GNSSselector.setCurrentIndex(0) # Sets the target in the GNSS selector to None

    def GNSS_clearCombobox(self):
	"""
	Resets the list of visible GNSS satellites
	"""
	self.GNSSselector.clear()

    def open_GNSSAzEl(self):
	"""
	Opens the GNSS Azimuth-Elevation Window
	"""

     	self.GNSSAzElWd = GNSSAzEl_window()
        self.GNSSAzElWd.show()

    def close_GNSSAzEl(self):
	"""
	Closes the GNSS Azimuth-Elevation Window
	"""

     	self.GNSSAzElWd = GNSSAzEl_window()
        self.GNSSAzElWd.hide()

    def closeEvent(self, event):
	"""
	Confirmation whether one would like to quit SALSA
	"""
        reply = QtGui.QMessageBox.question(self, 'Quit',
        "Are you sure you want to quit?", QtGui.QMessageBox.Yes |
        QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            event.accept()
	    self.close_GNSSAzEl()
        else:
            event.ignore()

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
                sigspec.data -= refspec.data
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
        (self.elAtMeasurementTime,self.azAtMeasurementTime) =self.telescope.get_current_alaz()
        self.aborting = False
        self.progresstimer.stop()
        self.clear_progressbar()
        #Make sure receiver and current thread is stopped
        if hasattr(self, 'sigthread'):
            self.sigworker.measurement.abort = True
            self.sigworker.measurement.receiver.stop()
            self.sigthread.quit()
        # TODO: clean up temp data file.
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
            self.sigworker.measurement.abort = True
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

        if self.cycle_checkbox.isChecked():
            sig_time = float(self.sig_time_spinbox.text()) # [s]
            ref_time = float(self.ref_time_spinBox.text()) # [s]
            loops = int(self.loops_spinbox.text()) #
            int_time = (sig_time+ref_time)*loops
        else:
            if self.mode_switched.isChecked():
                sig_time = float(self.int_time_spinbox.text())/2
                #print 'sig_time', sig_time 
                ref_time = float(self.int_time_spinbox.text())/2
                loops = 1;
                while sig_time > 20:
                     sig_time = sig_time/2.0
                     ref_time = ref_time/2.0
                     loops = loops*2
                     #print sig_time, loops
                int_time = (sig_time+ref_time)*loops
                #print 'int_time', int_time
            else:
                sig_time = float(self.int_time_spinbox.text())
                ref_time = 0
                loops = 1
                int_time = sig_time

        if self.mode_switched.isChecked():
            print "Signal cycle time per loop: ", sig_time
            print "Reference cycle time per loop: ", ref_time
            print "Loops: ", loops

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
        self.sigworker.measurement = Measurement(sig_freq, ref_freq, switched, int_time, sig_time, ref_time, bw, calt_deg, caz_deg, self.telescope.site, nchans, self.observer, self.config, coff_alt, coff_az, calfact)

        self.sigthread.started.connect(self.sigworker.work)
        self.sigworker.finished.connect(self.sigthread.quit)
        self.sigworker.finished.connect(self.observation_finished)
        self.sigthread.start()
        
    def plot(self, spectpl):
        plt.clf()
        ax = self.figure.add_subplot(111)
	# Get the target type from the coordselector
	target = self.coordselector.currentText()
        # create an axis
        preephem = time.time()
        # Get the reference frequency
        referenceFreq=float(self.FrequencyInput.text())
	if (spectpl.vlsr_corr!=0):
            if self.radioButton_velocity.isChecked():
                x = 1e-3 * (spectpl.get_vels())
            else:
                x = 1e-6*(spectpl.get_freqs() )-referenceFreq
        else:
            if self.radioButton_velocity.isChecked():
                x = 1e-3 * (spectpl.get_vels() - spectpl.vlsr_corr)
            else:
                x = 1e-6*(spectpl.get_freqs() - spectpl.freq_vlsr_corr )-referenceFreq
        y = spectpl.data

        if (spectpl.vlsr_corr!=0):
            if self.radioButton_velocity.isChecked():
                ax.set_xlabel('Velocity shifted to LSR [km/s]')
            else:
		labelX='Freq. shifted to LSR -'+ str("{:6.1f}".format(referenceFreq)) +'[MHz]'
                ax.set_xlabel(labelX)
        else:
            if self.radioButton_velocity.isChecked():
                ax.set_xlabel('Velocity relative to observer [km/s]')
            else:
		labelX='Measured freq.-'+ str("{:6.1f}".format(referenceFreq))+' [MHz]'
          	ax.set_xlabel(labelX)
	#normalize and/or convert to dB
        if self.checkBox_normalized.isChecked() and self.checkBox_dBScale.isChecked(): 
            ax.set_ylabel('Uncalibrated normalized antenna temperature [dB]')
	    # avoid values at the edge of the band
	    x=x[5:-5]
	    y=y[5:-5]
	    y=10*np.log10(np.abs(y/np.max(y)))
	elif self.checkBox_dBScale.isChecked():        
            ax.set_ylabel('Uncalibrated antenna temperature [dBK]')
	    # avoid values at the edge of the band
	    x=x[5:-5]
	    y=y[5:-5]
	    y=10*np.log10(np.abs(y))
        elif self.checkBox_normalized.isChecked(): 
            ax.set_ylabel('Uncalibrated normalized antenna temperature [-]')
	    # avoid values at the edge of the band
	    y=y[5:-5]
	    x=x[5:-5]
	    y=y/np.max(y)
	else:
            ax.set_ylabel('Uncalibrated antenna temperature [K]')
	ax.plot(x,y, '-')
        ax.minorticks_on()
        ax.tick_params('both', length=6, width=0.5, which='minor')
	
	if not ( target == "GNSS" or target == "Horizontal"):
		# Get galactic coordinates
	        pos = ephem.Galactic(spectpl.target)
	        coord1 = str(pos.lon)
       	        coord2 = str(pos.lat)
        	ax.set_title('Galactic long=' + coord1 + ', lat='+coord2)
	else:
        	# Get azimuth and elevation
		coord1="{:-6.2f}".format(self.azAtMeasurementTime)
		coord2="{:-6.2f}".format(self.elAtMeasurementTime)
		ax.set_title('Azimuth=' + str(coord1) + ', Elevation='+ str(coord2))
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

        if ((not self.telescope.is_moving()) and (not self.trackingtimer.isActive())):
            self.btn_track.setEnabled(True)
            self.btn_reset.setEnabled(True)
            self.btn_track.setText('Track')
            style = "QWidget {}"
            self.btn_track.setStyleSheet(style)

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
        elif target == 'GNSS':
            az_deg,alt_deg= satellites.SatComputeAzElSingle(self.currentGNSStarget)
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
        self.GNSSselector.setEnabled(False)
        self.btn_track.setText('Stop')
        style = "QWidget { background-color:red;}"
        self.btn_track.setStyleSheet(style)

    def enable_movement_controls(self):
        self.inputleftcoord.setReadOnly(False)
        self.inputrightcoord.setReadOnly(False)
        self.offset_left.setReadOnly(False)
        self.offset_right.setReadOnly(False)
        self.trackingtimer.stop()
        #Tracking button text is handeled by the update_UI-function to check that the telescope is still before offering new track position
        self.coordselector.setEnabled(True)
        self.GNSSselector.setEnabled(True)
        self.btn_track.setText('Stopping...')
        style = "QWidget { background-color:orange;}"
        self.btn_track.setStyleSheet(style)
        self.btn_track.setEnabled(False)

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



class GNSSAzEl_window(QtGui.QMainWindow, Ui_GNSSAzElWindow ):
    def __init__(self):
        super(GNSSAzEl_window, self).__init__()
        self.setupUi(self)
        self.init_Ui()
 
    def init_Ui(self):

        self.create_menuActions()
        self.btn_close.clicked.connect(self.close)

        self.dpi = 100
        self.fig = Figure((6.6, 6.6), dpi=self.dpi)
        self.fig.patch.set_facecolor('none')
        self.canvas = FigureCanvas(self.fig)
        # Position as left, top, width, height
        self.canvas.setGeometry(QtCore.QRect(40,60, 600, 600))  
        self.canvas.setParent(self)
        self.drawAzElPlt()

        self.checkBoxGPS.clicked.connect(self.refreshAzElPlt)
        self.checkBoxGLONASS.clicked.connect(self.refreshAzElPlt)
        self.checkBoxGALILEO.clicked.connect(self.refreshAzElPlt)
        self.checkBoxBEIDOU.clicked.connect(self.refreshAzElPlt)

        self.refreshtimer = QtCore.QTimer()
        self.refreshtimer.start(5000) #ms
        self.refreshtimer.timeout.connect(self.refreshAzElPlt)

        self.btn_close.clicked.connect(self.refreshtimer.stop)
            
    def drawAzElPlt(self):
	"""
	Draws the GNSS Az-El plot.

	"""
 
        self.grid=rc('grid', color='green', linewidth=0.5, linestyle='-')
        self.grid=rc('xtick', labelsize=15)
        self.grid=rc('ytick', labelsize=10)

        self.ax = self.fig.add_axes([0.1, 0.1, 0.8, 0.8], projection='polar', axisbg='#d5de9c')
        self.ax.set_rmax(90)

        self.ax.set_rgrids([10,20,30,40,50,60,70,80,90], angle=0)
        self.ax.set_theta_offset(0.5*math.pi)
        self.ax.set_theta_direction(-1)

        self.ax.set_title("GNSS satellites on the local horizon",va='bottom', )
        self.ax.set_yticklabels(map(str, range(80, 0, -10)))
        self.ax.set_xticklabels(['N', '', 'E', '', 'S', '', 'W', ''])

        self.ax.set_autoscalex_on(False)
        self.ax.set_autoscaley_on(False)

        if self.checkBoxGPS.isChecked() == True :
            [GPSname, phi_GPS, r_GPS] = satellites.SatCompute('visible', 'GPS')  # fills the list with all GPS satellites
            GPSname = [j.split()[-2].replace("(","" ) + j.split()[-1].replace(")" ,"") for j in GPSname] # shortens the displayed satellites' names on the plot
            self.ax.plot(phi_GPS,r_GPS, 'ro',label='GPS')
            for i,txt in enumerate(GPSname):
                self.ax.annotate(txt,(phi_GPS[i],r_GPS[i]))

        if self.checkBoxGLONASS.isChecked() == True:
            [GLONASSname, phi_GLONASS, r_GLONASS] = satellites.SatCompute('visible', 'COSMOS')  # fills the list with all GLONASS satellites
            GLONASSname = [j[13:16] for j in GLONASSname]
            self.ax.plot(phi_GLONASS, r_GLONASS, 'bo', label='GLONASS')
            for i, txt in enumerate(GLONASSname):
                self.ax.annotate(txt, (phi_GLONASS[i], r_GLONASS[i]))

        if self.checkBoxGALILEO.isChecked() == True:
            [GALILEOname, phi_GALILEO, r_GALILEO] = satellites.SatCompute('visible', 'GSAT')  # fills the list with all GALILEO satellites
            GALILEOname = [j.split()[-2].replace("(","" ) + j.split()[-1].replace(")" ,"") for j in GALILEOname]
            self.ax.plot(phi_GALILEO, r_GALILEO, 'go', label='GALILEO')
            for i, txt in enumerate(GALILEOname):
                self.ax.annotate(txt, (phi_GALILEO[i], r_GALILEO[i]))
        if self.checkBoxBEIDOU.isChecked() == True:
            [BEIDOUname, phi_BEIDOU, r_BEIDOU] = satellites.SatCompute('visible','BEIDOU')  # fills the list with all BEIDOU satellites
            BEIDOUname = [ j.split()[-1] for j in BEIDOUname]
            self.ax.plot(phi_BEIDOU, r_BEIDOU, 'ko', label='BEIDOU')
            for i, txt in enumerate(BEIDOUname):
                self.ax.annotate(txt, (phi_BEIDOU[i], r_BEIDOU[i]))

        self.canvas.draw()

    def refreshAzElPlt(self):
        """
	    Refreshes the drawn plot
	"""
        self.ax.clear()
        self.drawAzElPlt()

        
    def create_menuActions(self):
        """
        Creates actions for the menubar of the GNSS Az-El window.
        :return: Nothing
        """
        save_file_action = self.create_action("&Save current view",
            shortcut="Ctrl+S", slot=self.save_AzElPlot, 
            tip="Saves current Azimuth-Elevation view as an image.")

        quit_action = self.create_action("&Quit", slot=self.close, 
            shortcut="Ctrl+Q", tip="Closes current window")

        about_action = self.create_action("&About", 
            shortcut='F1', slot=self.on_about, 
            tip='Displays additional information.')

        self.add_actions(self.file_menu, 
            (save_file_action, None, quit_action))
        
        self.add_actions(self.help_menu, (about_action,))
        
    def add_actions(self, target, actions):

        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(  self, text, slot=None, shortcut=None, 
                        icon=None, tip=None, checkable=False, 
                        signal="triggered()"):

        action = QtGui.QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, QtCore.SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action

    def save_AzElPlot(self):
        """
        Saves the current GNSS Az-El plot
        """
        file_choices = "PNG (*.png)|*.png"

        path = unicode(QtGui.QFileDialog.getSaveFileName(self, 
                        'Save file', '', 
                        file_choices))
        if path:
            self.canvas.print_figure(path, dpi=self.dpi)
            self.statusBar().showMessage('Saved to %s' % path, 2000)

    def on_about(self):
        """
        A message of the help option
        """
        msg = """

        This window displays current positions of GNSS satellites on the local horizon. Positions computed using two-line element set (TLE) data.
        """
        QtGui.QMessageBox.about(self, "GNSS Az-El view", msg.strip())

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
