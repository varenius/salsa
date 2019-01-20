#!/usr/bin/env python2

from logging import getLogger, Formatter, StreamHandler, DEBUG
from time import time
from sys import argv
from getpass import getuser
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
from multiprocessing.pool import ThreadPool
from ConfigParser import ConfigParser
from os import path
from glob import glob

from numpy import pi, log10, abs, max, min, radians, size
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
from ephem import (Observer, degrees as ephem_deg, now, Galactic, Ecliptic,
                   Equatorial, hours, J2000, B1950)
from PyQt4.QtCore import QTimer
from PyQt4.QtGui import (QMessageBox, QMainWindow, QListWidgetItem,
                         QApplication, QStyleFactory, QComboBox, QPushButton)

from tendo import singleton

from UI.SALSA_UI import Ui_MainWindow
from UI.UI_LH import Ui_GNSSAzElWindow
from controller.tle.tle_ephem import TLEephem

from controller.telescope.telescope_controller import TelescopeController
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
from controller.frequency_translation import Frequency
from controller.observation.receiver import SALSA_Receiver
from controller.observation.spectrum import ArchiveConnection
from controller.util import (project_file_path, AzEl, ephdeg_to_deg, overrides)
from controller.tracking import SatelliteTracker
from controller.satellites.poscomp import SatPosComp, CelObjComp
from controller.satellites.posmodel import PositionModel
from controller.satellites.satellite import ReferenceSatellite


class SALSA_GUI(QMainWindow, Ui_MainWindow):
    class SpectrumPlot:
        def __init__(self, spec_, title_):
            self.spec = spec_
            self.title = title_

    def __init__(self, logger_, tleEphem_, site_, telescope_, software_gain_,
                 sat_pos_comp_, obj_pos_comp_, stow_sat_, tmpfile_,
                 measurement_setup_, tracker_):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)

        self._logger = logger_
        self._tleEphem = tleEphem_
        self._site = site_
        self._telescope = telescope_
        self._software_gain = software_gain_
        self._sat_pos_comp = sat_pos_comp_
        self._obj_pos_comp = obj_pos_comp_
        self._stow_target = stow_sat_
        self._tmpfile = tmpfile_
        self._measurement_setup = measurement_setup_
        self._tracker = tracker_

        self._tracking_update_intervall = 0.250  # s
        self._tracker.set_update_intervall(self._tracking_update_intervall)
        self._tracker.set_lost_callback(self._telescope_lost_action)

        # Dict used to store spectra observed in this session
        self._reset_anim_frame = 0
        self._spectra = dict()
        self._gnss_view_active = False
        self._gnss_window = None
        self._target = None
        self._target_selected = None
        self._obs_node = None
        self._emitt_telescope_lost = self._nothing
        self._emitt_observation_finished = self._nothing

        self._update_pos_labels = self.__update_pos_labels

        self._progressbar_update_interval = 100  # ms
        self._ui_update_interval = 100           # ms
        self._reset_update_intervall = 250       # ms
        self._progress_timer = QTimer()          # updates progressbar
        self._ui_timer = QTimer()                # updates ui
        self._tracking_timer = QTimer()  # updates telescope target
        self._reset_timer = QTimer()     # resets telescope pointing

        self.setupUi(self)
        self._init_Ui()
        self.setWindowTitle("SALSA Controller: %s" % site_.name)
        self._update_target_obj()

    @overrides(QMainWindow)
    def show(self):
        QMainWindow.show(self)
        # Check if telescope knows where it is (position can be lost
        # e.g. during powercut).
        if self._telescope.is_lost():
            self._reset_needed()
        else:
            QMessageBox.about(self, "Welcome to SALSA",
                              "If this is your first measurement for today, "
                              "please reset the telscope to make sure that it "
                              "tracks the sky correctly. A small position "
                              "error can accumulate if using the telescope "
                              "for multiple hours, but this is fixed if you "
                              "press the reset button and issue a soft reset.")

    @overrides(QMainWindow)
    def closeEvent(self, event):
        """
        Confirmation whether one would like to quit SALSA
        """
        reply = QMessageBox.question(
            self, "Quit", "Are you sure you want to quit?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
            self._close_gnss_window()
            if self._ui_timer.isActive():
                self._ui_timer.stop()
            if self._progress_timer.isActive():
                self._progress_timer.stop()
            if self._tracker.is_tracking():
                self._tracker.stop_tracking()
            if self._reset_timer.isActive():
                self._reset_timer.stop()
            self._telescope.set_target(self._stow_target.compute_az_el())
            self._telescope.terminate()
        else:
            event.ignore()

    def _init_Ui(self):
        self._gnss_selector = QComboBox(self.layoutWidget)
        self._gnss_selector.setVisible(False)
        self._gnss_selector.setObjectName("_gnss_selector")
        self.horizontalLayout_6.addWidget(self._gnss_selector)
        self._gnss_lh_btn = QPushButton("GNSS Az-El View", self.layoutWidget)
        self._gnss_lh_btn.setVisible(False)
        self._gnss_lh_btn.setObjectName("_gnss_lh_btn")
        self.horizontalLayout_7.addWidget(self._gnss_lh_btn)

        self.gain.setText(str(self._software_gain))

        self.listWidget_spectra.currentItemChanged.connect(self._change_spectra)
        self._progress_timer.timeout.connect(self._update_progressbar)
        self._ui_timer.timeout.connect(self._update_ui)
        self._reset_timer.timeout.connect(self.resettimer_action)
        self.btn_track.clicked.connect(self._track_clicked)
        self.btn_reset.clicked.connect(self._reset_clicked)
        self.mode_switched.clicked.connect(self._switched_mode_clicked)
        self.mode_signal.clicked.connect(self._signal_mode_clicked)
        self.cycle_checkbox.stateChanged.connect(self._cycle_checkbox_changed)
        self.coordselector.currentIndexChanged.connect(self._update_target_obj)
        self.coordselector.currentIndexChanged.connect(self._update_ui)
        self._gnss_selector.currentIndexChanged.connect(self._gnss_selector_chosen)
        self._gnss_lh_btn.clicked.connect(self._open_gnss_satellite_window)

        # Receiver control
        self.btn_observe.clicked.connect(self._pre_observation)
        self.btn_abort.clicked.connect(self._abort_obs)
        self.btn_abort.setEnabled(False)

        # Plotting and saving
        self.btn_upload.clicked.connect(self._send_to_webarchive)
        self._figure = Figure(facecolor="white")
        self.canvas = FigureCanvasQTAgg(self._figure)
        self.canvas.setParent(self.groupBox_spectrum)
        self.plotwinlayout.addWidget(self.canvas)
        self.plotwinlayout.addWidget(NavigationToolbar2QT(
            self.canvas, self.groupBox_spectrum))

        # replot spectra in case status of freq,
        # dBScale or normalized has changed
        self.radioButton_frequency.toggled.connect(self._change_spectra)
        self.checkBox_dBScale.toggled.connect(self._change_spectra)
        self.checkBox_normalized.toggled.connect(self._change_spectra)

        self._clear_progressbar()
        self._ui_timer.start(self._ui_update_interval)

    def _switched_mode_clicked(self):
        self.cycle_checkbox.setEnabled(True)
        self.sig_time_spinbox.setEnabled(True)
        self.ref_time_spinBox.setEnabled(True)
        self.loops_spinbox.setEnabled(True)

    def _signal_mode_clicked(self):
        self.cycle_checkbox.setEnabled(False)
        self.sig_time_spinbox.setEnabled(False)
        self.ref_time_spinBox.setEnabled(False)
        self.loops_spinbox.setEnabled(False)
        self.cycle_checkbox.setChecked(False)

    def _cycle_checkbox_changed(self):
        manual_cycle = self.cycle_checkbox.isChecked()
        self.sig_time_spinbox.setEnabled(manual_cycle)
        self.ref_time_spinBox.setEnabled(manual_cycle)
        self.loops_spinbox.setEnabled(manual_cycle)
        self.int_time_spinbox.setEnabled(not manual_cycle)

    def _change_spectra(self):
        # Plot spectra of currently selected item
        if self.listWidget_spectra.count() > 0:
            spec_plt = self._spectra[str(self.listWidget_spectra.currentItem().text())]
            self._plot(spec_plt)
            spec = spec_plt.spec
            self.lbl_val_offset_el.setText("%.3f" % spec.get_offset_el())
            self.lbl_val_offset_az.setText("%.3f" % spec.get_offset_az())
            self.lbl_val_total_power.setText("%e" % spec.get_total_power())
            self.lbl_val_el.setText("%.3f" % spec.get_elevation())
            self.lbl_val_az.setText("%.3f" % spec.get_azimuth())
            self.btn_upload.setEnabled(not spec_plt.spec.is_uploaded())

    def _start_progressbar(self, integration_time):
        # Add extra time for processing, stacking etc.
        self._expected_time = 1.0625*integration_time
        self._start_time = time()

    def _clear_progressbar(self):
        self._expected_time = -1
        self._start_time = -1
        self.progressBar.setValue(0)

    def _update_progressbar(self):
        if self._expected_time < 0:  # unknown expected time
            return
        perenct = 100*(time()-self._start_time)/self._expected_time
        self.progressBar.setValue(max((0, min((100, perenct)))))

    def _pre_observation(self):
        self.btn_abort.setEnabled(True)
        self.btn_observe.setEnabled(False)
        if self._progress_timer.isActive():
            self._progress_timer.stop()
        self._clear_progressbar()
        self._observe()

    def _post_observation(self):
        self._emitt_observation_finished = self._nothing
        self.btn_abort.setEnabled(False)
        self.btn_observe.setEnabled(True)
        if self._progress_timer.isActive():
            self._progress_timer.stop()
        self._clear_progressbar()
        try:
            self._obs_thrd.join()
            del self._obs_thrd
        except ObservationAborting:
            pass
        self.listWidget_spectra.setCurrentRow(self.listWidget_spectra.count()-1)
        self._obs_node = None

    def _abort_obs(self):
        self._logger.info("Aborting measurement.")
        if self._obs_node:
            self._obs_node.abort_measurement()

    def _observe(self):
        offset = self._get_desired_offset()
        bw = float(self.BandwidthInput.text())*1e6        # Hz
        nchans = int(self.ChannelsInput.text())  # Number of output channels
        calfact = float(self.gain.text())        # Software gain
        int_time = float(self.int_time_spinbox.text())   # s
        sig_freq = float(self.FrequencyInput.text())*1e6  # Hz
        ref_freq = float(self.RefFreqInput.text())*1e6    # Hz
        ref_offset = ref_freq - sig_freq
        meas_setup = BatchMeasurementSetup(
            self._measurement_setup, bw, nchans, calfact, int_time,
            offset, ref_offset, 1, 1, self.LNA_checkbox.isChecked(),
            self.noise_checkbox.isChecked())
        if self.mode_switched.isChecked():
            first_obs_node = SwitchingNode(ref_offset)
        else:
            first_obs_node = SignalNode()
        prev_node = first_obs_node

        freq_node = SingleFrequencyNode(Frequency(sig_freq))
        prev_node.connect(freq_node)
        prev_node = freq_node

        if meas_setup.get_diode_on():
            use_diode = DiodeNode()
            prev_node.connect(use_diode)
            prev_node = use_diode
        if meas_setup.get_lna_on():
            use_lna = LNANode()
            prev_node.connect(use_lna)
            prev_node = use_lna

        if self._target and self._tracker.is_tracking():
            target_name = self._tracker.get_target().name()
        else:
            target_name = "Nothing"
        self._obs_node = ObservationNode(self._logger, self._telescope,
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

        store_spec_node = CustomNode(
            self._logger,
            lambda spec, targ_type=str(self.coordselector.currentText()), targ=self._target: self._store_spectrum(spec, self._store_spectrum_title(targ_type, targ)))
        prev_node.connect(store_spec_node)
        prev_node = store_spec_node

        self._start_progressbar(int_time)
        self._progress_timer.start(self._progressbar_update_interval)
        # run GNURadio in background
        self._obs_thrd = Thread(target=self._observation_thread,
                                args=(first_obs_node, self._obs_node))
        self._obs_thrd.start()

    def _observation_thread(self, first_obs_node_, obs_node_):
        try:
            first_obs_node_.execute(obs_node_)
        except ObservationAborting:
            pass                # measurement was aborted, do nothing
        self._emitt_observation_finished = self._post_observation

    def _send_to_webarchive(self):
        date = str(self.listWidget_spectra.currentItem().text())
        spec_plt = self._spectra[date]
        spectrum = spec_plt.spec
        if not spectrum.is_uploaded():
            ul = UploadToArchiveNode(self._logger, self._figure, self._tmpfile,
                                     lambda: self._plot(spec_plt),
                                     save_vel_=self.radioButton_velocity.isChecked())
            ul.execute(spectrum)
            self.btn_upload.setEnabled(False)

    def _store_spectrum_title(self, target_type, target):
        if target_type == "GNSS":
            pos = self._telescope.get_current()
            return ('%s @ Az=%6.2f, El=%6.2f' %
                    (target.name() if target else "Nothing",
                     pos.get_azimuth(), pos.get_elevation()))
        elif target_type == "Horizontal":
            pos = self._telescope.get_current()
            return 'Azimuth=%6.2f, Elevation=%6.2f' % (pos.get_azimuth(),
                                                       pos.get_elevation())
        else:
            return ""

    def _store_spectrum(self, spec, title):
        # Store final spectra in list of observations
        if not title:  # Get galactic coordinates
            pos = Galactic(spec.get_target())
            title = 'Galactic lon=%s, lat=%s' % (str(pos.lon),
                                                 str(pos.lat))
        date = str(spec.get_site_date().datetime().replace(microsecond=0))
        self._spectra[date] = self.SpectrumPlot(spec, title)
        self.listWidget_spectra.addItem(QListWidgetItem(date, self.listWidget_spectra))

    def _plot(self, spec_plt):
        spec = spec_plt.spec

        f_center = spec.get_center_freq() * 1e-6
        if spec.get_vlsr_corr() != 0:
            if self.radioButton_velocity.isChecked():
                x_label = 'Velocity shifted to LSR [km/s]'
                x = 1e-3*(spec.get_vels())
            else:
                x_label = 'Freq. shifted to LSR -%6.1f [MHz]' % f_center
                x = 1e-6*(spec.get_freqs())-f_center
        else:
            if self.radioButton_velocity.isChecked():
                x_label = 'Velocity relative to observer [km/s]'
                x = 1e-3*(spec.get_vels()-spec.get_vlsr_corr())
            else:
                x_label = 'Center frequency: %6.1f [MHz]' % f_center
                x = 1e-6*(spec.get_freqs()-spec.get_freq_vlsr_corr()) - f_center

        unit_ = ["[K]", "[-]", "[dBK]", "[dB]"]
        normalize_y = 1 if self.checkBox_normalized.isChecked() else 0
        y_in_db = 2 if self.checkBox_dBScale.isChecked() else 0
        y = spec.get_data()
        y_label = "Uncalibrated"
        if normalize_y:
            y_label += " normalized"
            y = y/max(y)
        y_label += " antenna temperature "
        if y_in_db:
            # avoid bad data at the edges
            n = int(0.02*len(y))
            x = x[n:-n]
            y = 10*log10(abs(y[n:-n]))
        y_label += unit_[normalize_y | y_in_db]

        self._figure.clear()
        ax_ = self._figure.add_axes([0.2, 0.1, 0.7, 0.8])
        ax_.set_title(spec_plt.title)
        ax_.plot(x, y, '-b')
        ax_.grid(True, color='k', linestyle='-', linewidth=0.5)
        ax_.set_xlabel(x_label)
        ax_.set_ylabel(y_label)
        ax_.minorticks_on()
        ax_.tick_params('both', length=6, width=0.5, which='minor')
        self.canvas.draw()

    def _update_ui(self):
        self._update_pos_labels()
        self._emitt_telescope_lost()
        self._emitt_observation_finished()

    def __update_pos_labels(self):
        self._update_target_pos_labels()
        self._update_current_pos_labels()

    def __update_pos_labels_reset(self):
        _text = "Resetting" + "."*(self._reset_anim_frame >> 2)
        self._reset_anim_frame = (self._reset_anim_frame + 1) & 0xf

        self.cur_alt.setText(_text)
        self.cur_az.setText(_text)
        self.cur_alt.setStyleSheet("QWidget { }")
        self.cur_az.setStyleSheet("QWidget { }")
        self.calc_des_left.setText(_text)
        self.calc_des_right.setText(_text)

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
            pos = self._telescope.get_current()
            el_str = str(ephem_deg(radians(pos.get_elevation())))
            az_str = str(ephem_deg(radians(pos.get_azimuth())))
            self.cur_alt.setText(el_str)
            self.cur_az.setText(az_str)
        except Exception:
            pass                # invalid position; do not update
        if self._telescope.is_at_target():
            style = "QWidget { background-color:#8AE234;}"  # bright green
        elif self._telescope.is_close_to_target():
            style = "QWidget { background-color:#FCE94F;}"  # bright yellow
        else:
            style = "QWidget { background-color:#EF2929;}"  # bright red
        self.cur_alt.setStyleSheet(style)
        self.cur_az.setStyleSheet(style)

    def _get_desired_offset(self):
        return AzEl(ephdeg_to_deg(self.offset_right.text()),
                    ephdeg_to_deg(self.offset_left.text()))

    def _track_clicked(self):
        if self._tracker.is_tracking():
            self.stop_tracking()
        elif self._target_selected:
            self.start_tracking()
        else:
            self._show_message("You must select a target before tracking.")

    def start_tracking(self):
        try:
            self.btn_track.setText("Stop")
            self.btn_track.setStyleSheet("QWidget { background-color:red;}")
            self.btn_reset.setEnabled(False)

            self._target = self._target_selected
            self._tracker.set_target(self._target)
            self._tracker.set_offset(self._get_desired_offset())
            if not self._tracker.is_tracking():
                self._tracker.start_tracking()
        except Exception as e:
            self.stop_tracking()
            self._logger.error("An error occurred when starting tracker", exc_info=1)
            self._show_message(e.message)

    def stop_tracking(self):
        if self._tracker.is_tracking():
            self._tracker.stop_tracking()

        self._target = None
        self.btn_track.setText("Track")
        self.btn_track.setStyleSheet("QWidget {}")
        self.btn_reset.setEnabled(True)

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
            self.btn_track.setEnabled(False)
            self.btn_reset.setEnabled(False)
            self._telescope.reset(hard_reset=clicked is hard_btn)
            self._reset_timer.start(self._reset_update_intervall)

    def resettimer_action(self):
        if self._telescope.isreset():
            self._reset_timer.stop()
            self.btn_reset.setEnabled(True)
            self.btn_track.setEnabled(True)
            self.btn_observe.setEnabled(True)
            self._update_pos_labels = self.__update_pos_labels
            self._show_message("Dear user: The telescope has been reset "
                               "and now knows its position. Thank you "
                               "for your patience.")

    def _open_gnss_satellite_window(self):
        if self._gnss_window:
            if self._gnss_window.isVisible():
                self._gnss_window.activateWindow()
            else:
                self._gnss_window.show()
            return
        self._gnss_window = GNSSWindow(self._sat_pos_comp)
        self._gnss_window.show()

    def _close_gnss_window(self):
        if not self._gnss_window:
            return
        self._gnss_window.close()

    def _toggle_gnss_view(self, gnss_view):
        if self._gnss_view_active == gnss_view:
            return              # same view; no action needed
        self._gnss_view_active = gnss_view

        self.inputleftcoord.setVisible(not gnss_view)
        self.inputrightcoord.setVisible(not gnss_view)
        self.coordlabel_left.setVisible(not gnss_view)
        self.coordlabel_right.setVisible(not gnss_view)

        self._gnss_selector.setVisible(gnss_view)
        self._gnss_lh_btn.setVisible(gnss_view)
        if gnss_view:
            for n, _, _ in zip(*self._sat_pos_comp.SatCompute('ALL', 5.0)):
                self._gnss_selector.addItem(n)
            self._gnss_selector.setCurrentIndex(-1)
        else:
            self._gnss_selector.clear()
            self._close_gnss_window()

    def _update_target_obj(self):
        read_only = False
        tf_left_coord = "0.0"
        tf_right_coord = "0.0"
        lbl_left_coord = "Object:"
        lbl_right_coord = "Object:"
        target = str(self.coordselector.currentText())
        # switching away from GNSS view emitts a currentIndexChanged
        # signal and self._target_selected will be set to None.
        # Solution: toggle gnss view before setting target here.
        self._toggle_gnss_view(target == "GNSS")
        if target == "The Sun":
            read_only = True
            tf_left_coord = "The Sun"
            tf_right_coord = "The Sun"
            self._target_selected = self._obj_pos_comp.load_satellite("Sun")
        elif target == "The Moon":
            read_only = True
            tf_left_coord = "The Moon"
            tf_right_coord = "The Moon"
            self._target_selected = self._obj_pos_comp.load_satellite("Moon")
        elif target == "Cas. A":
            read_only = True
            tf_left_coord = "Cas. A"
            tf_right_coord = "Cas. A"
            self._target_selected = self._obj_pos_comp.load_satellite("CasA")
        elif target == "Stow":
            read_only = True
            tf_left_coord = "Stow"
            tf_right_coord = "Stow"
            self._target_selected = self._stow_target
        elif target == "Horizontal":
            lbl_left_coord = "Altitude [deg]"
            lbl_right_coord = "Azimuth [deg]"
            self.inputleftcoord.setText(tf_left_coord)
            self.inputrightcoord.setText(tf_right_coord)
            posmdl = PositionModel(
                lambda: AzEl(ephdeg_to_deg(self.inputrightcoord.text()),
                             ephdeg_to_deg(self.inputleftcoord.text())))
            self._target_selected = ReferenceSatellite(target, posmdl)
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
            self._target_selected = ReferenceSatellite(target, posmdl)
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
            self._target_selected = ReferenceSatellite(target, posmdl)
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
            self._target_selected = ReferenceSatellite(target, posmdl)
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
            self._target_selected = ReferenceSatellite(target, posmdl)
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

    def _gnss_selector_chosen(self):
        """
        Sets the current gnss target based on the selected GNSS
        target from the _gnss_selector combobox
        """
        try:
            target = str(self._gnss_selector.currentText())
            self._target_selected = self._sat_pos_comp.load_satellite(target)
        except NameError:
            self._target_selected = None
        self._update_pos_labels()

    def _reset_needed(self):
        # user have been notified
        self._emitt_telescope_lost = self._nothing
        # Telescope must apparently be resetted
        self.btn_track.setEnabled(False)
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


class GNSSWindow(QMainWindow, Ui_GNSSAzElWindow):
    def __init__(self, sat_pos_comp_):
        QMainWindow.__init__(self)
        Ui_GNSSAzElWindow.__init__(self)
        self._gps_plots = list()
        self._gps_texts = list()
        self._glonass_plots = list()
        self._glonass_texts = list()
        self._galileo_plots = list()
        self._galileo_texts = list()
        self._beidou_plots = list()
        self._beidou_texts = list()

        self._sat_pos_comp = sat_pos_comp_
        self._dpi = 100
        self._refreshtimer = QTimer()

        self.setupUi(self)
        self._init_ui()

    @overrides(QMainWindow)
    def closeEvent(self, event):
        if self._refreshtimer.isActive():
            self._refreshtimer.stop()
        QMainWindow.closeEvent(self, event)

    @overrides(QMainWindow)
    def showEvent(self, event):
        if not self._refreshtimer.isActive():
            self._refresh_all()
            self._refreshtimer.start(1000)  # ms
        QMainWindow.showEvent(self, event)

    def _init_ui(self):
        fig = Figure((6.6, 6.6), dpi=self._dpi)
        fig.patch.set_facecolor('none')
        self._canvas = FigureCanvasQTAgg(fig)
        self._canvas.setParent(self.groupBox)
        self.verticalLayout.addWidget(self._canvas)
        self.verticalLayout.addWidget(NavigationToolbar2QT(self._canvas,
                                                           self.groupBox))
        self._ax = self._create_axes(fig)

        self.checkBoxGPS.stateChanged.connect(self._refresh_gps)
        self.checkBoxGLONASS.stateChanged.connect(self._refresh_glonass)
        self.checkBoxGALILEO.stateChanged.connect(self._refresh_galileo)
        self.checkBoxBEIDOU.stateChanged.connect(self._refresh_beidou)
        self._refreshtimer.timeout.connect(self._refresh_all)

    def _create_axes(self, fig):
        ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], projection='polar',
                          axisbg='#d5de9c')
        ax.grid(color='green', linewidth=0.5, linestyle='-')
        ax.set_rmax(90)

        ax.set_rgrids(range(10, 91, 10), angle=0)
        # controll room / webcam is roughly looking directly east
        ax.set_theta_offset(pi/2 + pi/2)
        ax.set_theta_direction(-1)

        ax.set_yticklabels(map(str, range(80, 1, -10)), fontsize=10)
        ax.set_xticklabels(['N', '', 'E', '', 'S', '', 'W', ''], fontsize=15)

        ax.set_autoscalex_on(False)
        ax.set_autoscaley_on(False)
        return ax

    def _clear_constellation(self, plots, texts):
        while len(plots) > 0:
            self._ax.lines.pop(self._ax.lines.index(plots.pop()))
        while len(texts) > 0:
            self._ax.texts.pop(self._ax.texts.index(texts.pop()))

    def _gps_abbrev_name(self, norad_name):
        return norad_name[norad_name.find("(")+1:norad_name.find(")")]

    def _glonass_abbrev_name(self, norad_name):
        return norad_name[norad_name.find("(")+1:norad_name.find(")")]

    def _galileo_abbrev_name(self, norad_name):
        return norad_name[norad_name.find("(")+1:norad_name.find(")")]

    def _beidou_abbrev_name(self, norad_name):
        return norad_name[norad_name.find(" ")+1:]

    def _refresh_gps(self):
        self._clear_constellation(self._gps_plots, self._gps_texts)
        if self.checkBoxGPS.isChecked():
            name, phi, r = self._sat_pos_comp.SatCompute('GPS', 5.0)
            name = [self._gps_abbrev_name(n) for n in name]
            self._gps_plots.extend(self._ax.plot(phi, r, 'ro', label='GPS'))
            for n, v, d in zip(name, phi, r):
                self._gps_texts.append(self._ax.annotate(n, (v, d)))
        self._canvas.draw()

    def _refresh_glonass(self):
        self._clear_constellation(self._glonass_plots, self._glonass_texts)
        if self.checkBoxGLONASS.isChecked():
            name, phi, r = self._sat_pos_comp.SatCompute('COSMOS', 5.0)
            name = [self._glonass_abbrev_name(n) for n in name]
            self._glonass_plots.extend(self._ax.plot(phi, r, 'bo', label='GLONASS'))
            for n, v, d in zip(name, phi, r):
                self._glonass_texts.append(self._ax.annotate(n, (v, d)))
        self._canvas.draw()

    def _refresh_galileo(self):
        self._clear_constellation(self._galileo_plots, self._galileo_texts)
        if self.checkBoxGALILEO.isChecked():
            name, phi, r = self._sat_pos_comp.SatCompute('GSAT', 5.0)
            name = [self._galileo_abbrev_name(n) for n in name]
            self._galileo_plots.extend(self._ax.plot(phi, r, 'go', label='GALILEO'))
            for n, v, d in zip(name, phi, r):
                self._galileo_texts.append(self._ax.annotate(n, (v, d)))
        self._canvas.draw()

    def _refresh_beidou(self):
        self._clear_constellation(self._beidou_plots, self._beidou_texts)
        if self.checkBoxBEIDOU.isChecked():
            name, phi, r = self._sat_pos_comp.SatCompute('BEIDOU', 5.0)
            name = [self._beidou_abbrev_name(n) for n in name]
            self._beidou_plots.extend(self._ax.plot(phi, r, 'wo', label='BEIDOU'))
            for n, v, d in zip(name, phi, r):
                self._beidou_texts.append(self._ax.annotate(n, (v, d)))
        self._canvas.draw()

    def _refresh_all(self):
        self._refresh_beidou()
        self._refresh_galileo()
        self._refresh_glonass()
        self._refresh_gps()


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
    #me = singleton.SingleInstance()

    salsa_config = ConfigParser()
    salsa_config.read(project_file_path('/config/SALSA.cfg'))
    tle_config = ConfigParser()
    tle_config.read(project_file_path('/config/tle.cfg'))
    site = Observer()
    site.date = now()
    site.lat = ephem_deg(salsa_config.get('SITE', 'latitude'))
    site.lon = ephem_deg(salsa_config.get('SITE', 'longitude'))
    site.elev = salsa_config.getfloat('SITE', 'elevation')
    site.name = salsa_config.get('SITE', 'name')
    tle_files = glob(path.join(tle_config.get('TLE', 'output-dir'), '*.tle'))
    tleEphem = TLEephem(tle_files, site)

    logger = load_logger()
    username = getuser()

    stow_az = salsa_config.getfloat('RIO', 'stowaz')
    stow_el = salsa_config.getfloat('RIO', 'stowal')

    tconn = TelescopeConnection(salsa_config.get('RIO', 'host'),
                                salsa_config.getint('RIO', 'port'),
                                socket(AF_INET, SOCK_STREAM))
    tcom = TelescopeCommunication(logger, tconn)
    lim = TelescopePosInterface(tcom,
                                salsa_config.getfloat('RIO', 'minaz'),
                                salsa_config.getfloat('RIO', 'minal'))
    tolerance = salsa_config.getfloat('RIO', 'close_enough')
    telescope = TelescopeController(logger, tcom,
                                    AzEl(stow_az, stow_el),
                                    lim, tolerance)

    software_gain = salsa_config.getfloat('USRP', 'software_gain')
    usrp_gain = salsa_config.getfloat('USRP', 'usrp_gain')
    tmpdir = salsa_config.get('USRP', 'tmpdir')
    dbconn = ArchiveConnection(
        salsa_config.get('ARCHIVE', 'host'),
        salsa_config.get('ARCHIVE', 'database'),
        salsa_config.get('ARCHIVE', 'user'),
        salsa_config.get('ARCHIVE', 'password'),
        salsa_config.get('ARCHIVE', 'table'))
    usrp_outfile = "%s/SALSA_%s" % (tmpdir, username)
    receiver = SALSA_Receiver(salsa_config.get('USRP', 'host'),
                              "%s.tmp" % usrp_outfile)
    receiver.set_gain(usrp_gain)
    sat_pos_comp = SatPosComp(tleEphem)
    obj_pos_comp = CelObjComp(site)
    stow_sat = ReferenceSatellite("Stow", PositionModel(lambda: AzEl(stow_az, stow_el)))

    tmpfile = "%s/tmp_%s_%s" % (tmpdir, site.name, username)

    # use 1 process for signal
    tp_signal = ThreadPool(processes=1)
    # use 1 process for signal and 1 for reference
    tp_switched = ThreadPool(processes=2)
    nan_handler = WarnOnNaN(logger)
    meas_setup = MeasurementSetup(logger, nan_handler, site,
                                  telescope.get_current, dbconn, receiver,
                                  username, tp_signal, tp_switched)
    tracker = SatelliteTracker(logger, telescope, stow_sat)

    app = QApplication(argv)
    # app.setStyle(QStyleFactory.create("plastique"))
    app.setStyle(QStyleFactory.create("cleanlooks"))
    window = SALSA_GUI(logger, tleEphem, site, telescope,
                       software_gain, sat_pos_comp, obj_pos_comp,
                       stow_sat, tmpfile, meas_setup, tracker)
    window.show()
    app.exec_()
