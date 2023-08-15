#!/usr/bin/env python3
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar2QTAgg
import satellites # to cope with GNSS tracking
import sys
import ephem
from PyQt5 import QtGui, QtCore, QtWidgets
sys.path.append('./')
from telescope import *
from measurement import *
from UI import Ui_MainWindow
from UI_LH import Ui_GNSSAzElWindow # to import Az-El View window
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure,show,rc,ion,draw
from matplotlib.figure import Figure
import matplotlib.ticker as mticker
import urllib.request
import time
import webbrowser

import argparse

import getpass # To find current username
import configparser
from os.path import expanduser

# Make sure only one instance is running of this program
from tendo import singleton
me = singleton.SingleInstance() # will sys.exit(-1) if other instance is running

##### SET CONFIG FILE #######
scriptpath = os.path.dirname(os.path.realpath(__file__))
configfile = scriptpath + '/SALSA.config'
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

class main_window(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(main_window, self).__init__()
        # Dict used to store spectra observed in this session
        self.spectra = {}
        # Set current username, used for tmp files and spectrum uploads
        self.observer = getpass.getuser()
        # Set config file location
        self.config = configparser.ConfigParser()
        self.config.read(configfile)
        # Initialise telescope and UI
        self.translator = QtCore.QTranslator(self)
        self.telescope = TelescopeController(self.config)
        self.setupUi(self)
        self.init_Ui()
        self.setWindowTitle("SALSA Controller: " + self.telescope.site.name)

        self.settings = QtCore.QSettings(expanduser("~")+"/.SALSA.settings", QtCore.QSettings.IniFormat)
        self.restore()

    def init_Ui(self):

        # Set software gain
        self.gain.setValue(int(self.config.get('USRP', 'usrp_gain')))

        self.listWidget_spectra.currentItemChanged.connect(self.change_spectra)

        # Define progresstimer
        self.clear_progressbar()
        self.progresstimer = QtCore.QTimer()
        self.progresstimer.timeout.connect(self.update_progressbar)

        # Define and run UiTimer
        self.uitimer = QtCore.QTimer()
        self.uitimer.timeout.connect(self.update_Ui)
        uiint = 250
        self.uitimer.start(uiint) #ms


        # Initialise buttons and tracking status.
        self.btn_track.clicked.connect(self.track_or_stop)
        self.btn_GO.clicked.connect(self.track_or_stop)
        self.btn_webcam.clicked.connect(lambda: webbrowser.open('http://129.16.208.198/view/#view'))
        self.btn_reset.clicked.connect(self.unfreeze)
        self.btn_reset.setText('Unfreeze')

        # Make sure Ui is updated when changing target
        self.coordselector.currentIndexChanged.connect(self.update_Ui)
        # Make sure special targets like "The Sun" are handled correctly.
        self.coordselector.currentIndexChanged.connect(self.update_desired_target)

        # Make sure Ui is updated when changing target
        self.objectselector.currentIndexChanged.connect(self.update_Ui)
        # Make sure special targets like "The Sun" are handled correctly.
        self.objectselector.currentIndexChanged.connect(self.update_desired_object)


        # Set the GNSS-related parts of GUI to non-visible
        self.GNSS_GUI_visible(False)
        # Set the current GNSStarget to none
        self.currentGNSStarget="none"
        # Connect the activated signal on the coordselector to our handler which turns on/off the GNSS-related parts of GUI
        self.coordselector.currentIndexChanged.connect(self.coordselector_chosen)
        # Connect the activated signal on the GNSSselector to our handler which sets the currentGNSStarget
        self.GNSSselector.activated.connect(self.GNSSselector_chosen)
        self.GNSSselector.currentIndexChanged.connect(self.GNSSselector_chosen)

        # opens GNSS AzEl window after clicking the btn_GNSS_lh button
        self.btn_GNSS_lh.clicked.connect(self.open_GNSSAzEl)

        # RECEIVER CONTROL
        self.btn_observe.clicked.connect(self.observe)
        self.btn_observe.clicked.connect(self.disable_receiver_controls)
        self.btn_abort.clicked.connect(self.abort_obs)
        self.btn_abort.setEnabled(False)

        #RECEIVER CONTROL EZ
        self.btn_start_obs_ez.clicked.connect(self.observe_ez)
        self.btn_start_obs_ez.clicked.connect(self.disable_receiver_controls)
        self.btn_stop_obs_ez.clicked.connect(self.abort_obs)
        self.btn_stop_obs_ez.setEnabled(False)


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
        plotwinlayout = QtWidgets.QVBoxLayout()
        plotwinlayout.addWidget(self.canvas)
        plotwinlayout.addWidget(self.toolbar)
        self.groupBox_spectrum.setLayout(plotwinlayout)
        # replot spectra in case status of freq, dBScale or normalized has changed
        self.radioButton_frequency.toggled.connect(self.change_spectra)
        self.checkBox_dBScale.toggled.connect(self.change_spectra)
        self.checkBox_normalized.toggled.connect(self.change_spectra)
        '''
        For Easy "ez" basic plotting on first tab
        '''
        self.figure_ez = plt.figure()
        self.figure_ez.patch.set_facecolor('white')
        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas_ez = FigureCanvas(self.figure_ez)
        self.canvas_ez.setParent(self.groupBox_spectrum_ez)
        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar_ez = NavigationToolbar(self.canvas_ez, self.groupBox_spectrum_ez)
        #set ez layout
        plotwinlayout_ez = QtWidgets.QVBoxLayout()
        plotwinlayout_ez.addWidget(self.canvas_ez)
        plotwinlayout_ez.addWidget(self.toolbar_ez)
        self.groupBox_spectrum_ez.setLayout(plotwinlayout_ez)

        # Language
        self.languageselector.currentIndexChanged.connect(self.change_language)

    def change_language(self):
        #Stop UI update while changing language
        self.uitimer.stop()
        # Store coordinate values and tracking status
        leftcoord = str(self.inputleftcoord.text())
        rightcoord= str(self.inputrightcoord.text())
        trackstat = str(self.btn_track.text())
        olt = str(self.offset_left.text())
        ort = str(self.offset_right.text())
        # get index of item in coordselector list, used to set as current
        cind = self.coordselector.currentIndex()
        oind = self.objectselector.currentIndex()
        if self.coordselector.currentText() == "GNSS":
            gind = self.GNSSselector.currentIndex()

        app = QtWidgets.QApplication.instance()
        l = self.languageselector.currentText()
        if l == "Svenska":
            #Set Swedish locale
            QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.Swedish, QtCore.QLocale.Sweden))
            # Load Swedish translation
            load = self.translator.load(scriptpath + "/translations/sv.qm")
            app.installTranslator(self.translator)
        else:
            app.removeTranslator(self.translator)
        self.retranslateUi(self)
        self.inputleftcoord.setText(leftcoord)
        self.inputrightcoord.setText(rightcoord)
        self.offset_left.setText(olt)
        self.offset_right.setText(ort)
        self.btn_track.setText(trackstat)
        self.coordselector.setCurrentIndex(cind)
        self.objectselector.setCurrentIndex(oind)
        if self.coordselector.currentText() == "GNSS":
            self.GNSSselector.setCurrentIndex(gind)
        #start UI timer again
        self.uitimer.start()

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
        self.progressBar.setValue(int(100*self.lapsedtime/self.expectedtime))
        self.progressBar_ez.setValue(int(100*self.lapsedtime/self.expectedtime))

    def update_progressbar(self):
        self.lapsedtime += 1
        self.progressBar.setValue(int(100*self.lapsedtime/self.expectedtime))
        self.progressBar_ez.setValue(int(100*self.lapsedtime/self.expectedtime))

    def disable_receiver_controls(self):
        self.int_time_spinbox.setReadOnly(True)
        self.gain.setReadOnly(True)
        self.FrequencyInput.setReadOnly(True)
        self.RefFreqInput.setReadOnly(True)
        self.BandwidthInput.setEnabled(False)
        self.ChannelsInput.setEnabled(False)
        self.autoedit_bad_data_checkBox.setEnabled(False)
        self.mode_switched.setEnabled(False)
        self.mode_signal.setEnabled(False)
        self.noise_checkbox.setEnabled(False)
        self.cycle_checkbox.setEnabled(False)
        self.vlsr_checkbox.setEnabled(False)
        self.btn_observe.setEnabled(False)
        self.btn_abort.setEnabled(True)
        self.sig_time_spinbox.setEnabled(False)
        self.ref_time_spinBox.setEnabled(False)
        # Simple tab
        self.obs_time_ez.setReadOnly(True)
        self.btn_start_obs_ez.setEnabled(False)
        self.btn_stop_obs_ez.setEnabled(True)

    def enable_receiver_controls(self):
        self.int_time_spinbox.setReadOnly(False)
        self.gain.setReadOnly(False)
        self.FrequencyInput.setReadOnly(False)
        self.RefFreqInput.setReadOnly(False)
        self.BandwidthInput.setEnabled(True)
        self.ChannelsInput.setEnabled(True)
        self.autoedit_bad_data_checkBox.setEnabled(True)
        self.cycle_checkbox.setEnabled(True)
        self.mode_switched.setEnabled(True)
        self.mode_signal.setEnabled(True)
        self.noise_checkbox.setEnabled(True)
        self.vlsr_checkbox.setEnabled(True)
        #self.btn_observe.setEnabled(True)
        self.btn_abort.setEnabled(False)
        self.sig_time_spinbox.setEnabled(True)
        self.ref_time_spinBox.setEnabled(True)
        # Simple tab
        self.obs_time_ez.setReadOnly(False)
        self.btn_start_obs_ez.setEnabled(True)
        self.btn_stop_obs_ez.setEnabled(False)

    def coordselector_chosen(self):
        """
        The handler called when a target is chosen from the coordselector combobox.
        Turns on the GNSS-related parts of GUI if target is 'GNSS'.
        """
        if self.coordselector.currentText() == "GNSS":
            self.GNSS_GUI_visible(True)
        else:
            self.GNSS_GUI_visible(False)

    def GNSSselector_chosen(self):
        """
        Sets the currentGNSStarget based on the selected GNSS target from the GNSSselector combobox

        """
        self.currentGNSStarget=self.GNSSselector.currentText()

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
        reply = QtWidgets.QMessageBox.question(self, 'Quit',
        "Are you sure you want to quit?", QtWidgets.QMessageBox.Yes |
        QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            self.save()
            event.accept()
            self.close_GNSSAzEl()
        else:
            event.ignore()

    def observation_finished(self):
        #self.telescope.set_noise_diode(False)
        if not self.aborting:
            # Post-process data
            sigspec = self.sigworker.measurement.signal_spec
            if self.autoedit_bad_data_checkBox.isChecked():
                print("Removing RFI from signal...")
                sigspec.auto_edit_bad_data()
            if self.mode_switched.isChecked():
                refspec = self.sigworker.measurement.reference_spec
                if self.autoedit_bad_data_checkBox.isChecked():
                    print("Removing RFI from reference...")
                    refspec.auto_edit_bad_data()
                #print("Removing reference from signal...")
                #sigspec.data -= refspec.data
                print("Removing reference from signal and adjusting level...")
                # Get current outside temperature, max 60 seconds ago
                with urllib.request.urlopen('https://www.oso.chalmers.se/weather/onsala.txt') as response:
                    html = response.read().decode().split()
                    tdata = int(html[0])
                    temp = float(html[1])
                    now = time.time()
                    dt = now - tdata
                    if (dt < 120) and (temp > -30) and (temp < 50):
                        # We have data max 2 minutes ago, which is good.
                        # And reasonable temperature in Celsius. Convert to Kelvin
                        temp = temp + 273
                    else:
                        # No good temperature data. Assume static temp for now
                        temp = 285
                    trec = 0 # Empirical addition to account for non-ambient noise sources
                    TSYS = temp + trec
                sigspec.data = TSYS*(sigspec.data-refspec.data)/refspec.data
            # Average to desired number of channels
            nchans = self.sigworker.measurement.noutchans
            sigspec.decimate_channels(nchans)
            # Correct VLSR
            if self.vlsr_checkbox.isChecked():
                print('Translating freq/vel to LSR frame of reference.')
                sigspec.shift_to_vlsr_frame()
            # Store final spectra in list of observations
            date = str(sigspec.site.date.datetime().replace(microsecond=0))
            self.spectra[date] = sigspec
            item = QtWidgets.QListWidgetItem(date, self.listWidget_spectra)
            self.listWidget_spectra.setCurrentItem(item)
            # Create simple plot on first page
            self.plot_ez(self.spectra[date])
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
            self.figure.savefig(pngfile) # current item
            spectrum.upload_to_archive(fitsfile, pngfile, txtfile)
            self.btn_upload.setEnabled(False)

    def abort_obs(self):
        print("Aborting measurement.")
        self.aborting = True
        if hasattr(self, 'sigthread'):
            self.sigworker.measurement.abort = True
            self.sigworker.measurement.receiver.stop()
            self.sigthread.quit()
        # TODO: clean up temp data file.
        self.enable_receiver_controls()

    def observe_ez(self):
        self.int_time_spinbox.setValue(self.obs_time_ez.value())
        self.observe()

    def observe(self):
        self.aborting = False
        self.btn_abort.setEnabled(True)
        self.btn_observe.setEnabled(False)
        self.clear_progressbar()
        self.progresstimer.start(1000) # ms

        ## Use LNA if selected
        #if self.LNA_checkbox.isChecked():
        #    self.telescope.set_LNA(True)
        ## Use noise diode if selected
        #if self.noise_checkbox.isChecked():
        #    self.telescope.set_noise_diode(True)

        sig_freq = float(self.FrequencyInput.value())*1e6 # Hz
        ref_freq = float(self.RefFreqInput.value())*1e6
        bw = float(self.BandwidthInput.currentText())*1e6 # Hz

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
            print("Signal cycle time per loop: ", sig_time)
            print("Reference cycle time per loop: ", ref_time)
            print("Loops: ", loops)

        nchans = int(self.ChannelsInput.currentText()) # Number of output channels
        usrp_gain = float(self.gain.text()) # USRP gain
        coordsys = self.coordselector.currentText()
        if coordsys == "GNSS":
            satellite = self.GNSSselector.currentText()
        else:
            satellite = ""
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
        self.sigworker.measurement = Measurement(sig_freq, ref_freq, switched, int_time, sig_time, ref_time, bw, calt_deg, caz_deg, self.telescope.site, nchans, self.observer, self.config, coff_alt, coff_az, usrp_gain, coordsys, satellite)

        self.sigthread.started.connect(self.sigworker.work)
        self.sigworker.finished.connect(self.sigthread.quit)
        self.sigworker.finished.connect(self.observation_finished)
        self.sigthread.start()
    
    def plot_ez(self, spectpl):
        self.figure_ez.clear()
        ax = self.figure_ez.add_subplot(111)
        # Get the obs frequency
        obsFreq=float(spectpl.obs_freq/1.0e6)
        if (spectpl.vlsr_corr!=0):
            if self.radioButton_velocity.isChecked():
                x = 1e-3 * (spectpl.get_vels())
            else:
                x = 1e-6*(spectpl.get_freqs() )-obsFreq
        else:
            if self.radioButton_velocity.isChecked():
                x = 1e-3 * (spectpl.get_vels() - spectpl.vlsr_corr)
            else:
                x = 1e-6*(spectpl.get_freqs() - spectpl.freq_vlsr_corr )-obsFreq
        y = spectpl.data

        if (spectpl.vlsr_corr!=0):
            if self.radioButton_velocity.isChecked():
                ax.set_xlabel('Velocity shifted to LSR [km/s]')
            else:
                labelX='Freq. shifted to LSR -'+ str("{:6.1f}".format(obsFreq)) +'[MHz]'
                ax.set_xlabel(labelX)
        else:
            if self.radioButton_velocity.isChecked():
                ax.set_xlabel('Velocity relative to observer [km/s]')
            else:
                labelX='Measured freq.-'+ str("{:6.1f}".format(obsFreq))+' [MHz]'
                ax.set_xlabel(labelX)
        #normalize and/or convert to dB
        if self.checkBox_normalized.isChecked() and self.checkBox_dBScale.isChecked():
            #ax.set_ylabel('Uncalibrated normalized antenna temperature [dB]')
            ax.set_ylabel('Normalised intensity [dB]')
            # avoid values at the edge of the band
            x=x[5:-5]
            y=y[5:-5]
            y=10*np.log10(np.abs(y/np.max(y)))
        elif self.checkBox_dBScale.isChecked():
            #ax.set_ylabel('Uncalibrated antenna temperature [dBK]')
            ax.set_ylabel('Intensity [dB]')
            # avoid values at the edge of the band
            x=x[5:-5]
            y=y[5:-5]
            y=10*np.log10(np.abs(y))
        elif self.checkBox_normalized.isChecked():
            #ax.set_ylabel('Uncalibrated normalized antenna temperature [-]')
            ax.set_ylabel('Normalised intensity [arbitrary units]')
            # avoid values at the edge of the band
            y=y[5:-5]
            x=x[5:-5]
            y=y/np.max(y)
        else:
            #ax.set_ylabel('Uncalibrated antenna temperature [K]')
            ax.set_ylabel('Intensity [arbitrary units]')
        ax.plot(x,y, '-')
        ax.minorticks_on()
        ax.tick_params('both', length=4, width=0.5, which='minor')

        self.groupBox_spectrum_ez.setTitle("Spectrum taken " + str(spectpl.site.date).replace("/", "-") + " UTC:")
        ax.set_title(spectpl.target)
        ax.grid(True, color='k', linestyle='-', linewidth=0.5)
        #self.figure.tight_layout(rect=[0.05, 0.05, 0.95, 0.95])
        # refresh canvas
        self.figure_ez.subplots_adjust(bottom=0.2)
        self.canvas_ez.draw()

    def plot(self, spectpl):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        # Get the obs frequency
        obsFreq=float(spectpl.obs_freq/1.0e6)
        if (spectpl.vlsr_corr!=0):
            if self.radioButton_velocity.isChecked():
                x = 1e-3 * (spectpl.get_vels())
            else:
                x = 1e-6*(spectpl.get_freqs() )-obsFreq
        else:
            if self.radioButton_velocity.isChecked():
                x = 1e-3 * (spectpl.get_vels() - spectpl.vlsr_corr)
            else:
                x = 1e-6*(spectpl.get_freqs() - spectpl.freq_vlsr_corr )-obsFreq
        y = spectpl.data

        if (spectpl.vlsr_corr!=0):
            if self.radioButton_velocity.isChecked():
                ax.set_xlabel('Velocity shifted to LSR [km/s]')
            else:
                labelX='Freq. shifted to LSR -'+ str("{:6.1f}".format(obsFreq)) +'[MHz]'
                ax.set_xlabel(labelX)
        else:
            if self.radioButton_velocity.isChecked():
                ax.set_xlabel('Velocity relative to observer [km/s]')
            else:
                labelX='Measured freq.-'+ str("{:6.1f}".format(obsFreq))+' [MHz]'
                ax.set_xlabel(labelX)
        #normalize and/or convert to dB
        if self.checkBox_normalized.isChecked() and self.checkBox_dBScale.isChecked():
            #ax.set_ylabel('Uncalibrated normalized antenna temperature [dB]')
            ax.set_ylabel('Normalised intensity [dB]')
            # avoid values at the edge of the band
            x=x[5:-5]
            y=y[5:-5]
            y=10*np.log10(np.abs(y/np.max(y)))
        elif self.checkBox_dBScale.isChecked():
            #ax.set_ylabel('Uncalibrated antenna temperature [dBK]')
            ax.set_ylabel('Intensity [dB]')
            # avoid values at the edge of the band
            x=x[5:-5]
            y=y[5:-5]
            y=10*np.log10(np.abs(y))
        elif self.checkBox_normalized.isChecked():
            #ax.set_ylabel('Uncalibrated normalized antenna temperature [-]')
            ax.set_ylabel('Normalised intensity [arbitrary units]')
            # avoid values at the edge of the band
            y=y[5:-5]
            x=x[5:-5]
            y=y/np.max(y)
        else:
            #ax.set_ylabel('Uncalibrated antenna temperature [K]')
            ax.set_ylabel('Intensity [arbitrary units]')
        ax.plot(x,y, '-')
        ax.minorticks_on()
        ax.tick_params('both', length=4, width=0.5, which='minor')

        ax.set_title(spectpl.target)
        ax.grid(True, color='k', linestyle='-', linewidth=0.5)
        #self.figure.tight_layout(rect=[0.05, 0.05, 0.95, 0.95])
        # refresh canvas
        self.canvas.draw()

    def update_Ui(self):
        UTCnow = QtCore.QDateTime.currentDateTime().toUTC().toString(QtCore.Qt.ISODate)
        self.clock.setText(UTCnow[:-1].replace("T", " ") + " UTC") # Skip T and Z for clarity here
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
        if self.btn_track.text()=="Stop":
            self.track()
        if self.telstatus.text()=="TRACKING" and (not self.btn_abort.isEnabled()):
            self.btn_observe.setEnabled(True)
            self.btn_start_obs_ez.setEnabled(True)
        else:
            self.btn_observe.setEnabled(False)
            self.btn_start_obs_ez.setEnabled(False)

        # Update simple UI distance value
        cal, caz = self.telescope.get_current_alaz()
        tal = float(self.calc_des_left.text())
        taz = float(self.calc_des_right.text())
        dist = self.telescope._get_angular_distance(cal, caz, tal, taz)
        self.distance.setText("{0:4.3f}".format(dist))
    
    def update_desired_object(self):
        target = self.objectselector.currentText()
        if target == 'The Sun':
            # get index of item in coordselector list, used to set as current
            cind = self.coordselector.findText("The Sun", QtCore.Qt.MatchFixedString)
            self.coordselector.setCurrentIndex(cind)
            # set other things
            bind = self.BandwidthInput.findText("2.5", QtCore.Qt.MatchFixedString)
            self.BandwidthInput.setCurrentIndex(bind)
            self.FrequencyInput.setValue(1410)
            self.mode_switched.setChecked(False)
            self.mode_signal.setChecked(True)
            self.vlsr_checkbox.setChecked(False)
            self.radioButton_frequency.setChecked(True)
            self.radioButton_velocity.setChecked(False)
            self.checkBox_normalized.setChecked(False)
            self.checkBox_dBScale.setChecked(False)
            self.obs_time_ez.setValue(2)
        elif target == 'Satellite C05':
            # get index of item in coordselector list, used to set as current
            cind = self.coordselector.findText("GNSS", QtCore.Qt.MatchFixedString)
            self.coordselector.setCurrentIndex(cind)
            # set other things
            # Get index of item in GNSSselector list, used to set as current
            gind = self.GNSSselector.findText("BEIDOU 11 (C05)", QtCore.Qt.MatchFixedString)
            # Set current index
            self.GNSSselector.setCurrentIndex(gind)
            bind = self.BandwidthInput.findText("25.0", QtCore.Qt.MatchFixedString)
            self.BandwidthInput.setCurrentIndex(bind)
            self.FrequencyInput.setValue(1207.14)
            self.mode_switched.setChecked(False)
            self.mode_signal.setChecked(True)
            self.vlsr_checkbox.setChecked(False)
            self.radioButton_frequency.setChecked(True)
            self.radioButton_velocity.setChecked(False)
            self.checkBox_normalized.setChecked(False)
            self.checkBox_dBScale.setChecked(True)
            self.obs_time_ez.setValue(1)
        elif target == 'Galactic (100,0)':
            cind = self.coordselector.findText("Galactic", QtCore.Qt.MatchFixedString)
            self.coordselector.setCurrentIndex(cind)
            # set other things
            self.inputleftcoord.setText('100.0')
            self.inputrightcoord.setText('0.0')
            bind = self.BandwidthInput.findText("2.5", QtCore.Qt.MatchFixedString)
            self.BandwidthInput.setCurrentIndex(bind)
            self.FrequencyInput.setValue(1420.4)
            self.mode_switched.setChecked(True)
            self.mode_signal.setChecked(False)
            self.vlsr_checkbox.setChecked(True)
            self.radioButton_frequency.setChecked(False)
            self.radioButton_velocity.setChecked(True)
            self.checkBox_normalized.setChecked(False)
            self.checkBox_dBScale.setChecked(False)
            self.obs_time_ez.setValue(10)
        elif target == 'Galactic (140,0)':
            cind = self.coordselector.findText("Galactic", QtCore.Qt.MatchFixedString)
            self.coordselector.setCurrentIndex(cind)
            # set other things
            self.inputleftcoord.setText('140.0')
            self.inputrightcoord.setText('0.0')
            bind = self.BandwidthInput.findText("2.5", QtCore.Qt.MatchFixedString)
            self.BandwidthInput.setCurrentIndex(bind)
            self.FrequencyInput.setValue(1420.4)
            self.mode_switched.setChecked(True)
            self.mode_signal.setChecked(False)
            self.vlsr_checkbox.setChecked(True)
            self.radioButton_frequency.setChecked(False)
            self.radioButton_velocity.setChecked(True)
            self.checkBox_normalized.setChecked(False)
            self.checkBox_dBScale.setChecked(False)
            self.obs_time_ez.setValue(10)
        elif target == 'Stow':
            cind = self.coordselector.findText("Stow", QtCore.Qt.MatchFixedString)
            self.coordselector.setCurrentIndex(cind)
            # set other things
            self.inputleftcoord.setReadOnly(True)
            self.inputrightcoord.setReadOnly(True)
            self.inputleftcoord.setText('Stow')
            self.inputrightcoord.setText('Stow')

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
            if self.btn_track.text()=="Track":
                self.inputleftcoord.setReadOnly(False)
                self.inputrightcoord.setReadOnly(False)

    def update_desired_altaz(self):
        (alt, az) = self.calculate_desired_alaz()
        #leftval = str(ephem.degrees(alt*np.pi/180.0))
        #rightval = str(ephem.degrees(az*np.pi/180.0))
        leftval = "{:.3f}".format(alt)
        rightval = "{:.3f}".format(az)
        self.calc_des_left.setText(leftval)
        self.calc_des_right.setText(rightval)

    def update_current_altaz(self):
        (alt, az) = self.telescope.get_current_alaz()
        leftval = "{:.1f}".format(alt)
        rightval = "{:.1f}".format(az)
        self.cur_alt.setText(leftval)
        self.cur_az.setText(rightval)
        # Color coding works, but what about color blind people?
        # Should perhaps use blue and yellow?
        if self.telescope.is_tracking() and self.btn_track.text()=="Stop":
            style = "QLineEdit {background-color:green; font-size: 13pt;}"
            self.telstatus.setText("TRACKING")
            self.ez_telstatus.setText("TRACKING")
        elif (not self.telescope.is_tracking()) and self.btn_track.text()=="Stop":
            style = "QLineEdit {background-color:yellow; font-size: 13pt;}"
            self.telstatus.setText("SLEWING")
            self.ez_telstatus.setText("SLEWING")
        else:
            style = "QLineEdit {background-color:none; font-size: 13pt;}"
            self.telstatus.setText("IDLE")
            self.ez_telstatus.setText("IDLE")
        self.cur_alt.setStyleSheet(style)
        self.cur_az.setStyleSheet(style)
        self.distance.setStyleSheet(style)
        self.telstatus.setStyleSheet(style)
        self.ez_telstatus.setStyleSheet(style)
        self.btn_GO.setStyleSheet(style)

    def update_coord_labels(self):
        target = self.coordselector.currentText()
        if target == 'Horizontal':
            leftval = 'Altitude [deg]:'
            rightval = 'Azimuth [deg]:'
        elif (target == 'Galactic' or target == 'Ecliptic'):
            leftval = 'Long. [deg]:'
            rightval = 'Lat. [deg]:'
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


    def track_or_stop(self):
        if self.btn_track.text()=="Stop" or self.btn_GO.text()=="STOP":
            self.stop()
        else:
            self.track()

    def disable_movement_controls(self):
        self.inputleftcoord.setReadOnly(True)
        self.inputrightcoord.setReadOnly(True)
        self.offset_left.setReadOnly(True)
        self.offset_right.setReadOnly(True)
        self.objectselector.setEnabled(False)
        self.coordselector.setEnabled(False)
        self.GNSSselector.setEnabled(False)
        self.btn_track.setText('Stop')
        self.btn_GO.setText('STOP')
        #style = "QWidget { background-color:red;}"
        #self.btn_track.setStyleSheet(style)
        #self.btn_GO.setStyleSheet(style)
        # Language, since changing will reset selector list
        #self.languageselector.setEnabled(False)

    def enable_movement_controls(self):
        self.btn_track.setEnabled(True)
        self.btn_reset.setEnabled(True)
        self.btn_track.setText('Track')
        self.btn_GO.setText('Move to')
        style = "QWidget {}"
        self.btn_track.setStyleSheet(style)
        self.btn_GO.setStyleSheet(style)
        self.inputleftcoord.setReadOnly(False)
        self.inputrightcoord.setReadOnly(False)
        self.offset_left.setReadOnly(False)
        self.offset_right.setReadOnly(False)
        self.objectselector.setEnabled(True)
        self.coordselector.setEnabled(True)
        self.GNSSselector.setEnabled(True)
        #style = "QWidget { background-color:orange;}"
        #self.btn_track.setStyleSheet(style)
        #self.btn_GO.setStyleSheet(style)
        # Language, since changing will reset selector list
        #self.languageselector.setEnabled(True)

    def track(self):
        try:
            # This includes a check if position is reachable
            (alt_deg, az_deg) = self.calculate_desired_alaz()
            self.telescope.set_target_alaz(alt_deg, az_deg)
            self.update_desired_altaz()
            self.disable_movement_controls()
        except Exception as e:
            self.stop()
            self.show_message(e)

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

    def stop(self):
        self.telescope.stop()
        self.enable_movement_controls()

    def unfreeze(self):
        # Show a message box
        qmsg = "You have asked to unfreeze the telescope control unit. This should fix problems where the telescope won't move. Should be harmless, but take 5 seconds. Send unfreeze command?"
        result = QtWidgets.QMessageBox.question(QtWidgets.QWidget(), 'Confirmation', qmsg, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if result==QtWidgets.QMessageBox.Yes:
            #Stop UI update while restarting device
            self.uitimer.stop()
            self.telescope.restart()
            #start UI timer again
            self.uitimer.start()

    def restore(self):
        finfo = QtCore.QFileInfo(self.settings.fileName())
    
        if finfo.exists() and finfo.isFile():
            self.languageselector.setCurrentIndex(self.settings.value("language", type=int))
            self.Observebase.setCurrentIndex(self.settings.value("maintab", type=int))
    
    def save(self):
        self.settings.setValue("language", self.languageselector.currentIndex())
        self.settings.setValue("maintab", self.Observebase.currentIndex())



class GNSSAzEl_window(QtWidgets.QMainWindow, Ui_GNSSAzElWindow ):
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

        if not hasattr(self, 'ax'):
            self.ax = self.fig.add_axes([0.1, 0.1, 0.8, 0.8], projection='polar', facecolor='#d5de9c', label="polar")

        self.grid=rc('grid', color='green', linewidth=0.5, linestyle='-')
        self.grid=rc('xtick', labelsize=10)
        self.grid=rc('ytick', labelsize=10)

        self.ax.set_rmax(90)

        self.ax.set_rgrids([10,20,30,40,50,60,70,80,90], angle=0)
        self.ax.set_theta_offset(0.5*math.pi)
        self.ax.set_theta_direction(-1)

        self.ax.set_title("GNSS satellites on the local horizon",va='bottom', )
        self.ax.set_yticklabels(map(str, range(90, 0, -10)))

        #self.ax.set_xticklabels(['N', '', 'E', '', 'S', '', 'W', ''])
        # fixing yticks with matplotlib.ticker "FixedLocator"
        ticks_loc = self.ax.get_xticks().tolist()
        self.ax.xaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
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
            #GALILEOname = [j.split()[-2].replace("(","" ) + j.split()[-1].replace(")" ,"") for j in GALILEOname]
            # Handled Gsat names without parentheses
            Gnamefilt = []
            for j in GALILEOname:
                if "(" in j:
                    gn = j.split()[-2].replace("(","" ) + j.split()[-1].replace(")" ,"")
                else:
                    gn = j
                Gnamefilt.append(gn)
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
                        icon=None, tip=None, checkable=False
                        ):
                        #signal="triggered()"):

        action = QtWidgets.QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            #self.connect(action, QtCore.SIGNAL(signal), slot)
            action.triggered.connect(slot)
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
    app = QtWidgets.QApplication(sys.argv)
    parser = argparse.ArgumentParser(description='SALSA control program')
    parser.add_argument('--local', '-l',
                        default='False',
                        type = bool,
                        help='set local run ')
    args = parser.parse_args()
    #app.setStyle(QtGui.QStyleFactory.create("plastique"))
    # Do not use default GTK, strange low level warnings. Others see this as well.
    app.setStyle(QtWidgets.QStyleFactory.create("cleanlooks"))

    window = main_window()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
