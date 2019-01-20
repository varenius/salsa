#!/usr/bin/env python2

from logging import getLogger, Formatter, StreamHandler, DEBUG
from time import time, sleep
from sys import argv
from getpass import getuser
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
from multiprocessing.pool import ThreadPool
from ConfigParser import ConfigParser
from os import path
from glob import glob

from numpy import empty, float64, radians
import numpy as np
from scipy.optimize import curve_fit
from ephem import (degrees as ephem_deg, Galactic, Ecliptic,
                   Equatorial, hours, J2000, B1950)
import ephem
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
from PyQt4.QtGui import QMessageBox
from PyQt4 import QtGui, QtCore
from tendo import singleton

from UI.SALSA_mapper_UI import Ui_MainWindow
from controller.tle.tle_ephem import TLEephem
from controller.util import (project_file_path, AzEl, overrides, ephdeg_to_deg)
from controller.telescope.telescope_controller import TelescopeController, PositionUnreachable
from controller.telescope.communication_handler import TelescopeCommunication
from controller.telescope.connection_handler import TelescopeConnection
from controller.telescope.position_interface import TelescopePosInterface
from controller.observation.measurement import (
    WarnOnNaN, MeasurementSetup, BatchMeasurementSetup
)
from controller.observation.observation_nodes import (
    ObservationNode, SingleFrequencyNode,
    LNANode, DiodeNode, SignalNode, SwitchingNode,
    ObservationAborting
)
from controller.observation.post_processing_nodes import (
    DecimateChannelsNode, ShiftToVLSRFrameNode, RemoveRFINode,
    UploadToArchiveNode, CustomNode
)
from controller.path.path_finder import CelestialObjectMapping
from controller.frequency_translation import Frequency
from controller.tracking import SatelliteTracker, TrackingAborting
from controller.satellites.poscomp import SatPosComp, CelObjComp
from controller.satellites.posmodel import PositionModel
from controller.satellites.satellite import ReferenceSatellite
from controller.observation.spectrum import SALSA_spectrum, ArchiveConnection
from controller.observation.receiver import SALSA_Receiver


class main_window(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self, logger_, observer_, config_, telescope_, site_,
                 software_gain_, sat_pos_comp_, obj_pos_comp_,
                 measurement_setup_, tracker_, pf_):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.observer = observer_
        self.config = config_
        self._logger = logger_
        self._site = site_
        self.telescope = telescope_
        self._software_gain = software_gain_
        self._sat_pos_comp = sat_pos_comp_
        self._obj_pos_comp = obj_pos_comp_
        self._measurement_setup = measurement_setup_
        self._tracker = tracker_
        self._target = None
        self._pathfinder = pf_
        self._meas_thrd = None

        self._tracking_update_intervall = 0.250  # s
        self._tracker.set_update_intervall(self._tracking_update_intervall)
        self._tracker.set_lost_callback(self._telescope_lost_action)

        self._update_pos_labels = self.__update_pos_labels

        self.maps = dict()
        self._grid = empty((0, 0), dtype=float64)
        self.leftpos = [0]
        self.rightpos = [0]
        self.leftiter = 0
        self.rightiter = 0
        self.recording = False
        self._obs_node = None
        self._emitt_telescope_lost = self._nothing
        self._emitt_observation_finished = self._nothing

        self._reset_update_intervall = 250
        self.progresstimer = QtCore.QTimer()  # updates progressbar
        self.uitimer = QtCore.QTimer()
        self.trackingtimer = QtCore.QTimer()
        self.resettimer = QtCore.QTimer()

        self.setupUi(self)
        self.init_Ui()
        self.setWindowTitle("SALSA mapper: " + self._site.name)
        self._update_target_obj()

    @overrides(QtGui.QMainWindow)
    def show(self):
        QtGui.QMainWindow.show(self)
        # Check if telescope knows where it is (position can be lost
        # e.g. during powercut).
        if self.telescope.is_lost():
            self.reset_needed()
        else:
            QtGui.QMessageBox.about(
                self, "Welcome to SALSA",
                "If this is your first measurement for today, "
                "please reset the telscope to make sure that it "
                "tracks the sky correctly. A small position "
                "error can accumulate if using the telescope "
                "for multiple hours, but this is fixed if you "
                "press the reset button and issue a soft reset.")

    def init_Ui(self):
        # Set software gain
        self.gain.setText(self._software_gain)

        self.listWidget_measurements.currentItemChanged.connect(self.change_measurement)

        self.progresstimer.timeout.connect(self.update_progressbar)
        self.uitimer.timeout.connect(self.update_Ui)
        self.resettimer.timeout.connect(self.resettimer_action)

        # Initialise buttons and tracking status.
        self.btn_reset.clicked.connect(self._reset_clicked)
        self.btn_fit.clicked.connect(self.fit_gauss)
        self.coordselector.currentIndexChanged.connect(self._update_target_obj)
        self.coordselector.currentIndexChanged.connect(self.update_Ui)

        # Receiver control
        self.btn_observe.clicked.connect(self._track_clicked)

        # Plotting and saving
        self.figure = Figure(facecolor="white")
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setParent(self.groupBox_plot)
        self.plotwinlayout.addWidget(self.canvas)
        self.plotwinlayout.addWidget(NavigationToolbar2QT(self.canvas, self.groupBox_plot))

        self.uitimer.start(250)  # ms

    def clear_progressbar(self):
        self._gp = 0
        self._grid_points = 1
        self.progressBar.setValue(0)

    def setup_progressbar(self, grid_points):
        self._gp = 0
        self._grid_points = grid_points
        self.progressBar.setValue(0)

    def update_progressbar(self):
        self.progressBar.setValue(100.0*self._gp/self._grid_points)
        self._gp += 1

    def _store_spectrum(self, spec):
        i, j = self._pathfinder.get_current_grid_point()
        self._grid_data[i, j] = spec.get_total_power()

    def measure_pointing(self):
        offset = AzEl(0, 0)
        bw = float(self.BandwidthInput.text())*1e6  # Hz
        nchans = int(self.ChannelsInput.text())
        calfact = float(self.gain.text())
        int_time = float(self.int_time_spinbox.text())
        sig_freq = float(self.FrequencyInput.text())*1e6  # Hz
        ref_freq = float(self.RefFreqInput.text())*1e6
        ref_offset = ref_freq - sig_freq

        meas_setup = BatchMeasurementSetup(self._measurement_setup, bw, nchans,
                                           calfact, int_time, offset, ref_offset,
                                           1, 1, self.LNA_checkbox.isChecked(),
                                           self.noise_checkbox.isChecked())
        if self.mode_switched.isChecked():
            first_obs_node = SwitchingNode(ref_freq)
        else:
            first_obs_node = SignalNode()
        prev_node = first_obs_node

        freq_node = SingleFrequencyNode(Frequency(sig_freq))
        prev_node.connect(freq_node)
        prev_node = freq_node

        use_lna = LNANode()
        prev_node.connect(use_lna)
        prev_node = use_lna

        target_name = self._target.name()
        self._obs_node = ObservationNode(self._logger, self.telescope,
                                         meas_setup, target_name)
        prev_node.connect(self._obs_node)

        # connect post-processing nodes
        prev_node = first_pp_node = None
        if self.autoedit_bad_data_checkBox.isChecked():
            first_pp_node = RemoveRFINode(self._logger)
            self._obs_node.connect_post_processer(first_pp_node)
            prev_node = first_pp_node
        decch_node = DecimateChannelsNode(self._logger, nchans)
        if first_pp_node:
            first_pp_node.connect(decch_node)
        else:
            first_pp_node = decch_node
            self._obs_node.connect_post_processer(first_pp_node)
        prev_node = decch_node

        if self.vlsr_checkbox.isChecked():
            vlsr_node = ShiftToVLSRFrameNode(self._logger)
            prev_node.connect(vlsr_node)
            prev_node = vlsr_node
        # placeholder forbidden save spectrum
        store_spec_node = CustomNode(self._logger, self._store_spectrum)
        prev_node.connect(store_spec_node)
        prev_node = store_spec_node

        try:
            first_obs_node.execute(self._obs_node)
        except RuntimeError:
            print "runtime error"

    def update_Ui(self):
        self._update_pos_labels()

        t = float(self.int_time_spinbox.text())*len(self.leftpos)*len(self.rightpos)
        s = float(10)*len(self.leftpos)*len(self.rightpos)
        self.infolabel.setText('INFO: Your grid implies %.1f min recording plus slewing '
                               '(estimated to %.1f min assuming 10 sec/point).' % (
                                   t/60.0, s/60.0))
        self._emitt_telescope_lost()
        self._emitt_observation_finished()

    def __update_pos_labels(self):
        self._update_target_pos_labels()
        self._update_current_pos_labels()

    def _update_target_pos_labels(self):
        try:
            pos = self._target.compute_az_el()
        except AttributeError:  # no valid target selected
            try:
                pos = self._telescope.get_target()
            except IOError:     # error getting telescope target
                self.calc_des_left.setText("--:--:--")
                self.calc_des_right.setText("--:--:--")
                return
        el_str = str(ephem_deg(radians(pos.get_elevation())))
        az_str = str(ephem_deg(radians(pos.get_azimuth())))
        self.calc_des_left.setText(el_str)
        self.calc_des_right.setText(az_str)

    def _update_current_pos_labels(self):
        try:
            pos = self.telescope.get_current()
            el_str = str(ephem_deg(radians(pos.get_elevation())))
            az_str = str(ephem_deg(radians(pos.get_azimuth())))
            self.cur_alt.setText(el_str)
            self.cur_az.setText(az_str)
        except Exception:
            pass                # invalid position; do not update
        if self.telescope.is_at_target():
            style = "QWidget { background-color:#8AE234;}"  # bright green
        elif self.telescope.is_close_to_target():
            style = "QWidget { background-color:#FCE94F;}"  # bright yellow
        else:
            style = "QWidget { background-color:#EF2929;}"  # bright red
        self.cur_alt.setStyleSheet(style)
        self.cur_az.setStyleSheet(style)

    def _track_clicked(self):
        if self._meas_thrd:
            self.stop_measurement()
        elif self._target:
            self.start_measurement()
        else:
            self._show_message("You must select a target before tracking.")

    def start_measurement(self):
        if self._meas_thrd:
            return
        try:
            self.btn_observe.setText("Abort")
            self.btn_observe.setStyleSheet("QWidget { background-color:red;}")
            self.btn_reset.setEnabled(False)

            self._pathfinder.set_row_step(ephdeg_to_deg(self.offset_right.text()))
            self._pathfinder.set_col_step(ephdeg_to_deg(self.offset_left.text()))
            self._pathfinder.set_rows(int(str(self.nsteps_right.text())))
            self._pathfinder.set_cols(int(str(self.nsteps_left.text())))

            self._meas_thrd = Thread(target=self.measure__)
            self._meas_thrd.start()
        except Exception as e:
            self.stop_measurement()
            self._logger.error("An error occurred when starting tracker", exc_info=1)
            self._show_message(e.message)

    def stop_measurement(self):
        print "Stopping measurement..."
        if self._obs_node:
            self._obs_node.abort_measurement()
        self._tracker.abort_tracking()
        if self._meas_thrd:
            self._meas_thrd.join()
            self._meas_thrd = None

        self.btn_observe.setText("Measure")
        self.btn_observe.setStyleSheet("QWidget { }")
        self.btn_reset.setEnabled(False)

    def measure__(self):
        try:
            while True:
                self._grid_data = GridData(int(str(self.nsteps_right.text())),
                                           int(str(self.nsteps_left.text())),
                                           ephdeg_to_deg(self.offset_right.text()),
                                           ephdeg_to_deg(self.offset_left.text()))
                t0 = time()
                sat_in_path, plen = pf.find_optimal_path()
                if not sat_in_path:
                    wait_retry = 60.0
                    self._logger.warn("No satellites in path. Retrying "
                                      "in %d seconds" % int(wait_retry))
                    sleep(wait_retry)
                    continue

                self._logger.info("Starting new observation lap with %d satellites."
                                  % (len(sat_in_path)))

                for s in pf:
                    try:
                        self._tracker.set_target(s)
                        with self._tracker:
                            self._tracker.reach_target()
                            self.measure_pointing()
                    except PositionUnreachable as e:
                        self._logger.error(e.message, exc_info=1)

                t_observation = time() - t0
                date = str(self._site.date.datetime().replace(microsecond=0))
                self.maps[date] = self._grid_data
                self.listWidget_measurements.addItem(QtGui.QListWidgetItem(date, self.listWidget_measurements))
                self._logger.info("Lap took %.2f seconds." % (t_observation))
                self._logger.info("~Scan complete~")
                if not self.loop_grid_checkbox.isChecked():
                    break
        except ObservationAborting:
            pass
        except TrackingAborting:
            pass

    def _telescope_lost_action(self):
        self._emitt_telescope_lost = self._reset_needed

    def _reset_clicked(self):
        # Show a message box
        msg_box = QMessageBox(QMessageBox.Information, "Confirm reset",
                              "Hard reset: reboot the telescope hardware and "
                              "issue a soft reset.\n"
                              "Soft reset: restart the telescope software and "
                              "move the telescope to a known position.\n"
                              "Most users will find that a soft reset is "
                              "enough.\n\n"
                              "Resetting the telescope pointing may take a "
                              "few minutes if the telescope is far from its "
                              "starting position so please be patient.")
        hard_btn = msg_box.addButton("Hard reset", QMessageBox.ResetRole)
        soft_btn = msg_box.addButton("Soft reset", QMessageBox.ResetRole)
        msg_box.addButton("Cancel", QMessageBox.RejectRole)
        msg_box.setDefaultButton(soft_btn)

        msg_box.exec_()
        clicked = msg_box.clickedButton()
        if (clicked is hard_btn or clicked is soft_btn):
            self.stop_tracking()
            self._reset_anim_frame = 0
            self._update_pos_labels = self.__update_pos_labels_reset
            self.btn_observe.setEnabled(False)
            self.btn_reset.setEnabled(False)
            self._telescope.reset(hard_reset=clicked is hard_btn)
            self._reset_timer.start(self._reset_update_intervall)

    def resettimer_action(self):
        if self.telescope.isreset():
            self.resettimer.stop()
            self.btn_reset.setEnabled(True)
            self.btn_observe.setEnabled(True)
            self._update_pos_labels = self.__update_pos_labels
            self._show_message("Dear user: The telescope has been reset "
                               "and now knows its position. Thank you "
                               "for your patience.")

    def _update_target_obj(self):
        read_only = False
        tf_left_coord = "0.0"
        tf_right_coord = "0.0"
        lbl_left_coord = "Object:"
        lbl_right_coord = "Object:"
        target = str(self.coordselector.currentText())
        if target == "The Sun":
            read_only = True
            tf_left_coord = "The Sun"
            tf_right_coord = "The Sun"
            self._target = self._obj_pos_comp.load_satellite("Sun")
        elif target == "The Moon":
            read_only = True
            tf_left_coord = "The Moon"
            tf_right_coord = "The Moon"
            self._target = self._obj_pos_comp.load_satellite("Moon")
        elif target == "Cas. A":
            read_only = True
            tf_left_coord = "Cas. A"
            tf_right_coord = "Cas. A"
            self._target = self._obj_pos_comp.load_satellite("CasA")
        elif target == "Stow":
            read_only = True
            tf_left_coord = "Stow"
            tf_right_coord = "Stow"
            self._target = self._stow_target
        elif target == "Horizontal":
            lbl_left_coord = "Altitude [deg]"
            lbl_right_coord = "Azimuth [deg]"
            self.inputleftcoord.setText(tf_left_coord)
            self.inputrightcoord.setText(tf_right_coord)
            posmdl = PositionModel(
                lambda: AzEl(ephdeg_to_deg(self.inputrightcoord.text()),
                             ephdeg_to_deg(self.inputleftcoord.text())))
            self._target = ReferenceSatellite(target, posmdl)
        elif target == "Galactic":
            tf_left_coord = "120.0"
            lbl_left_coord = "Longitude [deg]"
            lbl_right_coord = "Latitude [deg]"
            self.inputleftcoord.setText(tf_left_coord)
            self.inputrightcoord.setText(tf_right_coord)
            posmdl = PositionModel(
                lambda: CelObjComp.astro_compute(
                    Galactic(ephem_deg(str(self.inputleftcoord.text())),
                             ephem_deg(str(self.inputrightcoord.text()))),
                    CelObjComp.refresh_observer_time(self._site)))
            self._target = ReferenceSatellite(target, posmdl)
        elif target == "Ecliptic":
            lbl_left_coord = "Longitude [deg]"
            lbl_right_coord = "Latitude [deg]"
            self.inputleftcoord.setText(tf_left_coord)
            self.inputrightcoord.setText(tf_right_coord)
            posmdl = PositionModel(
                lambda: CelObjComp.astro_compute(
                    Ecliptic(ephem_deg(str(self.inputleftcoord.text())),
                             ephem_deg(str(self.inputrightcoord.text()))),
                    CelObjComp.refresh_observer_time(self._site)))
            self._target = ReferenceSatellite(target, posmdl)
        elif target == "Eq. J2000":
            lbl_left_coord = "R.A. [H:M:S]"
            lbl_right_coord = "Dec. [D:\':\"]"
            self.inputleftcoord.setText(tf_left_coord)
            self.inputrightcoord.setText(tf_right_coord)
            posmdl = PositionModel(
                lambda: CelObjComp.astro_compute(
                    Equatorial(hours(str(self.inputleftcoord.text())),
                               ephem_deg(str(self.inputrightcoord.text())),
                               epoch=J2000),
                    CelObjComp.refresh_observer_time(self._site)))
            self._target = ReferenceSatellite(target, posmdl)
        elif target == "Eq. B1950":
            lbl_left_coord = "R.A. [H:M:S]"
            lbl_right_coord = "Dec. [D:\':\"]"
            self.inputleftcoord.setText(tf_left_coord)
            self.inputrightcoord.setText(tf_right_coord)
            posmdl = PositionModel(
                lambda: CelObjComp.astro_compute(
                    Equatorial(hours(str(self.inputleftcoord.text())),
                               ephem_deg(str(self.inputrightcoord.text())),
                               epoch=B1950),
                    CelObjComp.refresh_observer_time(self._site)))
            self._target = ReferenceSatellite(target, posmdl)
        elif target == "GNSS":
            # target is set with the gnss selector
            pass

        if self._tracker.is_tracking():
            read_only = True

        self.inputleftcoord.setReadOnly(read_only)
        self.inputrightcoord.setReadOnly(read_only)
        self.inputleftcoord.setText(tf_left_coord)
        self.inputrightcoord.setText(tf_right_coord)
        self.coordlabel_left.setText(lbl_left_coord)
        self.coordlabel_right.setText(lbl_right_coord)
        self._update_pos_labels()
        self._pathfinder.set_target(self._target)

    def reset_needed(self):
        # user have been notified
        self._emitt_telescope_lost = self._nothing
        # Telescope must apparently be resetted
        self.btn_reset.setEnabled(True)
        self.btn_observe.setEnabled(False)
        self.stop_tracking()
        self._show_message("Dear user. The telescope is lost, this may "
                           "happen when there is a power cut. A reset "
                           "is needed for SALSA to know where it is "
                           "pointing. Please press reset and wait until "
                           "reset is finished.")

    def _show_message(self, m):
        msg_box = QMessageBox(QMessageBox.Information, "Message from SALSA", m,
                              QMessageBox.Ok)
        msg_box.exec_()

    def _nothing(self):
        """
        Empty method that can be used instead of 'lambda: None'
        to avoid warnings about assigning lambda expressions.
        """
        return

    def change_measurement(self):
        # Plot spectra of currently selected item
        self.plot(self.maps[str(self.listWidget_measurements.currentItem().text())])

    def plot(self, grid_data):
        grid = grid_data.get_grid()
        self.figure.clear()
        ax = self.figure.add_axes([0.2, 0.1, 0.7, 0.8])
        if np.size(grid, axis=1) > 1 and np.size(grid, axis=0) > 1:
            ax.imshow(grid, origin='lower', interpolation='none',
                      extent=[grid_data.cmin(), grid_data.cmax(), grid_data.rmin(), grid_data.rmax()])
            ax.set_xlabel('Relative offset [deg]')
            ax.set_ylabel('Relative offset [deg]')
        if np.size(grid, axis=1) > 1 and np.size(grid, axis=0) == 1:
            ydata = grid.flatten()
            xdata = np.linspace(grid_data.cmin(), grid_data.cmax(), len(ydata))
            ax.plot(xdata, ydata, linestyle="-", marker='*', color="green",
                    markeredgecolor="blue", markerfacecolor="blue")
            ax.set_xlabel('Relative offset left [deg]')
            ax.set_ylabel('Arbitrary amplitude')
        if np.size(grid, axis=1) == 1 and np.size(grid, axis=0) > 1:
            ydata = grid.flatten()
            xdata = np.linspace(grid_data.rmin(), grid_data.rmax(), len(ydata))
            ax.plot(xdata, ydata, linestyle="-", marker='*', color="green",
                    markeredgecolor="blue", markerfacecolor="blue")
            ax.set_xlabel('Relative offset right [deg]')
            ax.set_ylabel('Arbitrary amplitude')
        ax.autoscale_view('tight')
        # refresh canvas
        self.canvas.draw()

    # Define model function to be used to fit measured beam data:
    def oneD_Gaussian(self, x, *p):
        A, mu, sigma, offset = p
        return offset + A*np.exp(-(x-mu)**2/(2.*sigma**2))

    def twoD_Gaussian(self, (x, y), amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
        """
        Define 2D Gaussian according to
        http://stackoverflow.com/questions/21566379/fitting-a-2d-gaussian-function-using-scipy-optimize-curve-fit-valueerror-and-m/21566831#21566831
        """
        xo = float(xo)
        yo = float(yo)
        a = (np.cos(theta)**2)/(2*sigma_x**2) + (np.sin(theta)**2)/(2*sigma_y**2)
        b = -(np.sin(2*theta))/(4*sigma_x**2) + (np.sin(2*theta))/(4*sigma_y**2)
        c = (np.sin(theta)**2)/(2*sigma_x**2) + (np.cos(theta)**2)/(2*sigma_y**2)
        g = offset + amplitude*np.exp(-(a*((x-xo)**2) + 2*b*(x-xo)*(y-yo)
                                        + c*((y-yo)**2)))
        return g.ravel()

    def fit_gauss(self):
        map2plot = self.maps[str(self.listWidget_measurements.currentItem().text())]
        leftpos = map2plot['leftpos']
        rightpos = map2plot['rightpos']
        nleft = len(leftpos)
        nright = len(rightpos)
        data = np.zeros((nleft, nright))
        for i in range(nleft):
            for j in range(nright):
                num = map2plot['L'+str(i)+'R'+str(j)].get_total_power()
                data[i, j] = num
        leftmid = np.mean(leftpos)
        rightmid = np.mean(rightpos)
        leftrel = leftpos - leftmid
        rightrel = rightpos - rightmid
        ax = plt.gca()
        if nleft > 1 and nright > 1:
            # Two-D Gauss
            # amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
            p0 = [500, 0.0, 0.0, 5.0, 5.0, 0.0, 100]
            rm, lm = np.meshgrid(rightrel, leftrel)
            popt, pcov = curve_fit(self.twoD_Gaussian, (rm, lm),
                                   np.ravel(data), p0=p0)
            print popt
            fx0 = popt[1]
            fy0 = popt[2]
            fsigma_x = popt[3]
            fsigma_y = popt[4]
            print(('Towards {0}, {1}: Fitted Gaussian roff={2}deg, '
                  'loff={3}, FWHM1={4}deg, FWHM2={5}deg.').format(
                      round(leftmid, 1), round(rightmid, 1), fx0, fy0,
                      fsigma_x*2.355, fsigma_y*2.355))
            npt = 100
            xv = np.linspace(np.min(rightrel), np.max(rightrel), npt)
            yv = np.linspace(np.min(leftrel), np.max(leftrel), npt)
            xi, yi = np.meshgrid(xv, yv)
            model = self.twoD_Gaussian((xi, yi), *popt)
            plt.contour(xi, yi, model.reshape(npt, npt), 8, colors='k')
        else:
            if nleft > 1 and nright == 1:
                xvals = leftrel
                yvals = data.flatten()
            if nleft == 1 and nright > 1:
                xvals = rightrel
                yvals = data.flatten()
            # p0 is the initial guess for the fitting coefficients
            # (A, mu,sigma, offset)
            wmean = np.average(xvals, weights=yvals)
            wvar = np.average((xvals-wmean)**2, weights=yvals)
            wstd = np.sqrt(wvar)
            p0 = [max(yvals), wmean, wstd, min(yvals)]
            popt, pcov = curve_fit(self.oneD_Gaussian, xvals, yvals, p0=p0)
            # Make nice grid for fitted data
            fitx = np.linspace(min(xvals), max(xvals), 500)
            # Get the fitted curve
            fity = self.oneD_Gaussian(fitx, *popt)
            fsigma = popt[2]
            fmu = popt[1]
            fbeam = 2.355*fsigma  # FWHM
            plt.plot(fitx, fity, '--', color='blue')
            print(('Towards {0}, {1}: Fitted Gaussian mean={2}deg and '
                   'FWHM={3} deg.').format(round(leftmid, 1),
                                           round(rightmid, 1),
                                           fmu, fbeam))
        # refresh canvas
        self.canvas.draw()


class GridData:
    def __init__(self, rows_, cols_, rsep_, csep_):
        self._rows = rows_
        self._cols = cols_
        self._rsep = rsep_
        self._csep = csep_
        self._grid = np.zeros((rows_, cols_), dtype=float64)
        self._az_min = rows_*rsep_

        self._rmin = -(rows_-1)/2.0*rsep_
        self._rmax = (rows_-1)/2.0*rsep_
        self._cmin = -(cols_-1)/2.0*csep_
        self._cmax = (cols_-1)/2.0*csep_

    def rmin(self):
        return self._rmin

    def rmax(self):
        return self._rmax

    def cmin(self):
        return self._cmin

    def cmax(self):
        return self._cmax

    def get_grid(self):
        return self._grid

    def __setitem__(self, key, value):
        self._grid[key] = value

    def __getitem__(self, key):
        return self._grid[key]




def load_logger():
    logger = getLogger(__file__)
    logger.setLevel(DEBUG)
    fmt = Formatter('[%(asctime)s] [%(levelname)s] %(message)s', "%H:%M:%S")

    # create console handler
    ch = StreamHandler()
    ch.setLevel(DEBUG)
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    return logger


if __name__ == '__main__':
    # Make sure only one instance is running of this program
    me = singleton.SingleInstance()  # will exit if other instance is running

    logger_ = load_logger()
    username_ = getuser()
    config_ = ConfigParser()
    config_.read(project_file_path("/config/SALSA.cfg"))
    tle_config = ConfigParser()
    tle_config.read(project_file_path('/config/tle.cfg'))

    stow_az = config_.getfloat('RIO', 'stowaz')
    stow_el = config_.getfloat('RIO', 'stowal')

    software_gain = config_.get('USRP', 'software_gain')

    site_ = ephem.Observer()
    site_.date = ephem.now()
    site_.lat = ephem.degrees(config_.get('SITE', 'latitude'))
    site_.lon = ephem.degrees(config_.get('SITE', 'longitude'))
    site_.elev = config_.getfloat('SITE', 'elevation')
    site_.pressure = 0  # Do not correct for atmospheric refraction
    site_.name = config_.get('SITE', 'name')
    tle_files = glob(path.join(tle_config.get('TLE', 'output-dir'), '*.tle'))
    tleEphem = TLEephem(tle_files, site_)
    tmpdir = config_.get('USRP', 'tmpdir')
    dbconn_ = ArchiveConnection(
        config_.get('ARCHIVE', 'host'),
        config_.get('ARCHIVE', 'database'),
        config_.get('ARCHIVE', 'user'),
        config_.get('ARCHIVE', 'password'),
        config_.get('ARCHIVE', 'table'))
    usrp_outfile = "%s/SALSA_%s" % (tmpdir, username_)
    receiver = SALSA_Receiver(config_.get('USRP', 'host'),
                              "%s.tmp" % usrp_outfile)

    stow_pos = AzEl(config_.getfloat('RIO', 'stowaz'),
                    config_.getfloat('RIO', 'stowal'))
    tolerance = config_.getfloat('RIO', 'close_enough')
    host = config_.get('RIO', 'host')
    port = config_.getint('RIO', 'port')
    s = socket(AF_INET, SOCK_STREAM)
    tcom = TelescopeCommunication(logger_, TelescopeConnection(host, port, s))
    lim = TelescopePosInterface(tcom,
                                config_.getfloat('RIO', 'minaz'),
                                config_.getfloat('RIO', 'minal'))
    telescope_ = TelescopeController(logger_, tcom,
                                     stow_pos, lim, tolerance)
    sat_pos_comp = SatPosComp(tleEphem)
    obj_pos_comp = CelObjComp(site_)
    pf = CelestialObjectMapping(logger_)
    stow_sat = ReferenceSatellite("Stow", PositionModel(lambda: AzEl(stow_az, stow_el)))

    # use 1 process for signal
    tp_signal = ThreadPool(processes=1)
    # use 1 process for signal and 1 for reference
    tp_switched = ThreadPool(processes=2)
    nan_handler = WarnOnNaN(logger_)
    meas_setup = MeasurementSetup(logger_, nan_handler, site_,
                                  telescope_.get_current, dbconn_, receiver,
                                  username_, tp_signal, tp_switched)
    tracker = SatelliteTracker(logger_, telescope_, stow_sat)

    app = QtGui.QApplication(argv)
    # app.setStyle(QtGui.QStyleFactory.create("plastique"))
    # Do not use default GTK, strange low level warnings.
    # Others see this as well.
    app.setStyle(QtGui.QStyleFactory.create("cleanlooks"))
    window = main_window(logger_, username_, config_, telescope_, site_,
                         software_gain, sat_pos_comp, obj_pos_comp, meas_setup, tracker, pf)
    window.show()
    app.exec_()
