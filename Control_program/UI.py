# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'SALSA_UI.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(829, 632)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.centralwidget.setFont(font)
        self.centralwidget.setObjectName("centralwidget")
        self.Observebase = QtWidgets.QTabWidget(self.centralwidget)
        self.Observebase.setGeometry(QtCore.QRect(20, 20, 791, 581))
        self.Observebase.setObjectName("Observebase")
        self.tab_Observe = QtWidgets.QWidget()
        self.tab_Observe.setObjectName("tab_Observe")
        self.label_4 = QtWidgets.QLabel(self.tab_Observe)
        self.label_4.setGeometry(QtCore.QRect(20, 10, 641, 16))
        self.label_4.setObjectName("label_4")
        self.groupBox = QtWidgets.QGroupBox(self.tab_Observe)
        self.groupBox.setGeometry(QtCore.QRect(20, 40, 741, 111))
        self.groupBox.setObjectName("groupBox")
        self.objectselector = QtWidgets.QComboBox(self.groupBox)
        self.objectselector.setGeometry(QtCore.QRect(90, 30, 91, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.objectselector.setFont(font)
        self.objectselector.setEditable(True)
        self.objectselector.setObjectName("objectselector")
        self.objectselector.addItem("")
        self.objectselector.addItem("")
        self.objectselector.addItem("")
        self.objectselector.addItem("")
        self.label_5 = QtWidgets.QLabel(self.groupBox)
        self.label_5.setGeometry(QtCore.QRect(10, 30, 81, 31))
        font = QtGui.QFont()
        font.setPointSize(13)
        self.label_5.setFont(font)
        self.label_5.setObjectName("label_5")
        self.btn_GO = QtWidgets.QPushButton(self.groupBox)
        self.btn_GO.setGeometry(QtCore.QRect(190, 30, 61, 31))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.btn_GO.setFont(font)
        self.btn_GO.setObjectName("btn_GO")
        self.track_progress_ez = QtWidgets.QProgressBar(self.groupBox)
        self.track_progress_ez.setGeometry(QtCore.QRect(10, 70, 241, 23))
        self.track_progress_ez.setProperty("value", 0)
        self.track_progress_ez.setObjectName("track_progress_ez")
        self.cam_link = QtWidgets.QLabel(self.groupBox)
        self.cam_link.setGeometry(QtCore.QRect(590, 50, 51, 21))
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(True)
        font.setItalic(True)
        font.setWeight(75)
        self.cam_link.setFont(font)
        self.cam_link.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.cam_link.setOpenExternalLinks(True)
        self.cam_link.setObjectName("cam_link")
        self.label_7 = QtWidgets.QLabel(self.groupBox)
        self.label_7.setGeometry(QtCore.QRect(410, 50, 191, 20))
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setItalic(True)
        self.label_7.setFont(font)
        self.label_7.setObjectName("label_7")
        self.groupBox_2 = QtWidgets.QGroupBox(self.tab_Observe)
        self.groupBox_2.setGeometry(QtCore.QRect(20, 160, 741, 381))
        self.groupBox_2.setObjectName("groupBox_2")
        self.label_14 = QtWidgets.QLabel(self.groupBox_2)
        self.label_14.setGeometry(QtCore.QRect(10, 30, 161, 31))
        font = QtGui.QFont()
        font.setPointSize(13)
        self.label_14.setFont(font)
        self.label_14.setObjectName("label_14")
        self.obs_time_ez = QtWidgets.QSpinBox(self.groupBox_2)
        self.obs_time_ez.setGeometry(QtCore.QRect(170, 30, 77, 30))
        self.obs_time_ez.setMinimum(1)
        self.obs_time_ez.setMaximum(3600)
        self.obs_time_ez.setProperty("value", 10)
        self.obs_time_ez.setObjectName("obs_time_ez")
        self.btn_start_obs_ez = QtWidgets.QPushButton(self.groupBox_2)
        self.btn_start_obs_ez.setGeometry(QtCore.QRect(250, 30, 51, 31))
        self.btn_start_obs_ez.setObjectName("btn_start_obs_ez")
        self.stop_obs_ez = QtWidgets.QPushButton(self.groupBox_2)
        self.stop_obs_ez.setGeometry(QtCore.QRect(310, 30, 51, 31))
        self.stop_obs_ez.setObjectName("stop_obs_ez")
        self.groupBox_spectrum_ez = QtWidgets.QGroupBox(self.groupBox_2)
        self.groupBox_spectrum_ez.setGeometry(QtCore.QRect(110, 70, 531, 301))
        self.groupBox_spectrum_ez.setObjectName("groupBox_spectrum_ez")
        self.btn_plot_ez = QtWidgets.QPushButton(self.groupBox_2)
        self.btn_plot_ez.setGeometry(QtCore.QRect(650, 100, 41, 21))
        self.btn_plot_ez.setObjectName("btn_plot_ez")
        self.pushButton = QtWidgets.QPushButton(self.tab_Observe)
        self.pushButton.setGeometry(QtCore.QRect(670, 10, 41, 21))
        self.pushButton.setObjectName("pushButton")
        self.btn_sve = QtWidgets.QPushButton(self.tab_Observe)
        self.btn_sve.setGeometry(QtCore.QRect(720, 10, 41, 21))
        self.btn_sve.setObjectName("btn_sve")
        self.Observebase.addTab(self.tab_Observe, "")
        self.tab = QtWidgets.QWidget()
        font = QtGui.QFont()
        font.setPointSize(9)
        self.tab.setFont(font)
        self.tab.setObjectName("tab")
        self.groupBox_tc = QtWidgets.QGroupBox(self.tab)
        self.groupBox_tc.setGeometry(QtCore.QRect(20, 30, 721, 201))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_tc.sizePolicy().hasHeightForWidth())
        self.groupBox_tc.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(13)
        self.groupBox_tc.setFont(font)
        self.groupBox_tc.setObjectName("groupBox_tc")
        self.layoutWidget = QtWidgets.QWidget(self.groupBox_tc)
        self.layoutWidget.setGeometry(QtCore.QRect(17, 30, 691, 167))
        self.layoutWidget.setObjectName("layoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.layoutWidget)
        self.gridLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.gridLayout.setObjectName("gridLayout")
        self.label_currentaltaz = QtWidgets.QLabel(self.layoutWidget)
        self.label_currentaltaz.setObjectName("label_currentaltaz")
        self.gridLayout.addWidget(self.label_currentaltaz, 4, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_cur_alt = QtWidgets.QLabel(self.layoutWidget)
        self.label_cur_alt.setObjectName("label_cur_alt")
        self.horizontalLayout_2.addWidget(self.label_cur_alt)
        self.cur_alt = QtWidgets.QLineEdit(self.layoutWidget)
        self.cur_alt.setReadOnly(True)
        self.cur_alt.setObjectName("cur_alt")
        self.horizontalLayout_2.addWidget(self.cur_alt)
        self.gridLayout.addLayout(self.horizontalLayout_2, 4, 1, 1, 1)
        self.label_currentpointing = QtWidgets.QLabel(self.layoutWidget)
        self.label_currentpointing.setObjectName("label_currentpointing")
        self.gridLayout.addWidget(self.label_currentpointing, 3, 0, 1, 1)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.GNSSselector = QtWidgets.QComboBox(self.layoutWidget)
        self.GNSSselector.setVisible(False)
        self.GNSSselector.setObjectName("GNSSselector")
        self.horizontalLayout_6.addWidget(self.GNSSselector)
        self.coordlabel_left = QtWidgets.QLabel(self.layoutWidget)
        self.coordlabel_left.setObjectName("coordlabel_left")
        self.horizontalLayout_6.addWidget(self.coordlabel_left)
        self.inputleftcoord = QtWidgets.QLineEdit(self.layoutWidget)
        self.inputleftcoord.setObjectName("inputleftcoord")
        self.horizontalLayout_6.addWidget(self.inputleftcoord)
        self.gridLayout.addLayout(self.horizontalLayout_6, 0, 1, 1, 1)
        self.btn_track = QtWidgets.QPushButton(self.layoutWidget)
        self.btn_track.setObjectName("btn_track")
        self.gridLayout.addWidget(self.btn_track, 0, 3, 1, 1)
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.label_cur_alt_2 = QtWidgets.QLabel(self.layoutWidget)
        self.label_cur_alt_2.setObjectName("label_cur_alt_2")
        self.horizontalLayout_8.addWidget(self.label_cur_alt_2)
        self.calc_des_left = QtWidgets.QLineEdit(self.layoutWidget)
        self.calc_des_left.setReadOnly(True)
        self.calc_des_left.setObjectName("calc_des_left")
        self.horizontalLayout_8.addWidget(self.calc_des_left)
        self.gridLayout.addLayout(self.horizontalLayout_8, 3, 1, 1, 1)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.btn_GNSS_lh = QtWidgets.QPushButton(self.layoutWidget)
        self.btn_GNSS_lh.setVisible(False)
        self.btn_GNSS_lh.setObjectName("btn_GNSS_lh")
        self.horizontalLayout_7.addWidget(self.btn_GNSS_lh)
        self.coordlabel_right = QtWidgets.QLabel(self.layoutWidget)
        self.coordlabel_right.setObjectName("coordlabel_right")
        self.horizontalLayout_7.addWidget(self.coordlabel_right)
        self.inputrightcoord = QtWidgets.QLineEdit(self.layoutWidget)
        self.inputrightcoord.setObjectName("inputrightcoord")
        self.horizontalLayout_7.addWidget(self.inputrightcoord)
        self.gridLayout.addLayout(self.horizontalLayout_7, 0, 2, 1, 1)
        self.line_3 = QtWidgets.QFrame(self.layoutWidget)
        self.line_3.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_3.setObjectName("line_3")
        self.gridLayout.addWidget(self.line_3, 2, 2, 1, 1)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_cur_az = QtWidgets.QLabel(self.layoutWidget)
        self.label_cur_az.setObjectName("label_cur_az")
        self.horizontalLayout_3.addWidget(self.label_cur_az)
        self.cur_az = QtWidgets.QLineEdit(self.layoutWidget)
        self.cur_az.setReadOnly(True)
        self.cur_az.setObjectName("cur_az")
        self.horizontalLayout_3.addWidget(self.cur_az)
        self.gridLayout.addLayout(self.horizontalLayout_3, 4, 2, 1, 1)
        self.horizontalLayout_13 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.label_2 = QtWidgets.QLabel(self.layoutWidget)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_13.addWidget(self.label_2)
        self.offset_right = QtWidgets.QLineEdit(self.layoutWidget)
        self.offset_right.setReadOnly(False)
        self.offset_right.setObjectName("offset_right")
        self.horizontalLayout_13.addWidget(self.offset_right)
        self.gridLayout.addLayout(self.horizontalLayout_13, 1, 2, 1, 1)
        self.line = QtWidgets.QFrame(self.layoutWidget)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridLayout.addWidget(self.line, 2, 0, 1, 1)
        self.line_2 = QtWidgets.QFrame(self.layoutWidget)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.gridLayout.addWidget(self.line_2, 2, 1, 1, 1)
        self.label_offset = QtWidgets.QLabel(self.layoutWidget)
        self.label_offset.setObjectName("label_offset")
        self.gridLayout.addWidget(self.label_offset, 1, 0, 1, 1)
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.label_offset_left = QtWidgets.QLabel(self.layoutWidget)
        self.label_offset_left.setObjectName("label_offset_left")
        self.horizontalLayout_11.addWidget(self.label_offset_left)
        self.offset_left = QtWidgets.QLineEdit(self.layoutWidget)
        self.offset_left.setReadOnly(False)
        self.offset_left.setObjectName("offset_left")
        self.horizontalLayout_11.addWidget(self.offset_left)
        self.gridLayout.addLayout(self.horizontalLayout_11, 1, 1, 1, 1)
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.label_cur_az_2 = QtWidgets.QLabel(self.layoutWidget)
        self.label_cur_az_2.setObjectName("label_cur_az_2")
        self.horizontalLayout_10.addWidget(self.label_cur_az_2)
        self.calc_des_right = QtWidgets.QLineEdit(self.layoutWidget)
        self.calc_des_right.setReadOnly(True)
        self.calc_des_right.setObjectName("calc_des_right")
        self.horizontalLayout_10.addWidget(self.calc_des_right)
        self.gridLayout.addLayout(self.horizontalLayout_10, 3, 2, 1, 1)
        self.btn_reset = QtWidgets.QPushButton(self.layoutWidget)
        self.btn_reset.setObjectName("btn_reset")
        self.gridLayout.addWidget(self.btn_reset, 4, 3, 1, 1)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_newtarget = QtWidgets.QLabel(self.layoutWidget)
        self.label_newtarget.setObjectName("label_newtarget")
        self.horizontalLayout_5.addWidget(self.label_newtarget)
        self.coordselector = QtWidgets.QComboBox(self.layoutWidget)
        self.coordselector.setObjectName("coordselector")
        self.coordselector.addItem("")
        self.coordselector.addItem("")
        self.coordselector.addItem("")
        self.coordselector.addItem("")
        self.coordselector.addItem("")
        self.coordselector.addItem("")
        self.coordselector.addItem("")
        self.coordselector.addItem("")
        self.coordselector.addItem("")
        self.horizontalLayout_5.addWidget(self.coordselector)
        self.gridLayout.addLayout(self.horizontalLayout_5, 0, 0, 1, 1)
        self.groupBox_3 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_3.setGeometry(QtCore.QRect(20, 230, 721, 311))
        font = QtGui.QFont()
        font.setPointSize(13)
        self.groupBox_3.setFont(font)
        self.groupBox_3.setObjectName("groupBox_3")
        self.tabWidget_2 = QtWidgets.QTabWidget(self.groupBox_3)
        self.tabWidget_2.setGeometry(QtCore.QRect(20, 30, 691, 281))
        self.tabWidget_2.setObjectName("tabWidget_2")
        self.receiver_tab_basic = QtWidgets.QWidget()
        self.receiver_tab_basic.setObjectName("receiver_tab_basic")
        self.layoutWidget1 = QtWidgets.QWidget(self.receiver_tab_basic)
        self.layoutWidget1.setGeometry(QtCore.QRect(10, 50, 651, 61))
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.horizontalLayout_15 = QtWidgets.QHBoxLayout(self.layoutWidget1)
        self.horizontalLayout_15.setObjectName("horizontalLayout_15")
        self.progresslabel = QtWidgets.QLabel(self.layoutWidget1)
        self.progresslabel.setObjectName("progresslabel")
        self.horizontalLayout_15.addWidget(self.progresslabel)
        self.progressBar = QtWidgets.QProgressBar(self.layoutWidget1)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.horizontalLayout_15.addWidget(self.progressBar)
        self.layoutWidget2 = QtWidgets.QWidget(self.receiver_tab_basic)
        self.layoutWidget2.setGeometry(QtCore.QRect(10, 10, 528, 41))
        self.layoutWidget2.setObjectName("layoutWidget2")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.layoutWidget2)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.int_time_spinbox = QtWidgets.QSpinBox(self.layoutWidget2)
        self.int_time_spinbox.setMinimum(1)
        self.int_time_spinbox.setMaximum(3600)
        self.int_time_spinbox.setProperty("value", 10)
        self.int_time_spinbox.setObjectName("int_time_spinbox")
        self.gridLayout_5.addWidget(self.int_time_spinbox, 0, 1, 1, 1)
        self.btn_observe = QtWidgets.QPushButton(self.layoutWidget2)
        self.btn_observe.setObjectName("btn_observe")
        self.gridLayout_5.addWidget(self.btn_observe, 0, 2, 1, 1)
        self.btn_abort = QtWidgets.QPushButton(self.layoutWidget2)
        self.btn_abort.setDefault(False)
        self.btn_abort.setObjectName("btn_abort")
        self.gridLayout_5.addWidget(self.btn_abort, 0, 3, 1, 1)
        self.FrequencyLabel_2 = QtWidgets.QLabel(self.layoutWidget2)
        self.FrequencyLabel_2.setObjectName("FrequencyLabel_2")
        self.gridLayout_5.addWidget(self.FrequencyLabel_2, 0, 0, 1, 1)
        self.tabWidget_2.addTab(self.receiver_tab_basic, "")
        self.receiver_tab_advanced = QtWidgets.QWidget()
        self.receiver_tab_advanced.setObjectName("receiver_tab_advanced")
        self.cycle_checkbox = QtWidgets.QCheckBox(self.receiver_tab_advanced)
        self.cycle_checkbox.setEnabled(True)
        self.cycle_checkbox.setGeometry(QtCore.QRect(18, 192, 271, 20))
        self.cycle_checkbox.setChecked(False)
        self.cycle_checkbox.setObjectName("cycle_checkbox")
        self.signal_time_label_3 = QtWidgets.QLabel(self.receiver_tab_advanced)
        self.signal_time_label_3.setGeometry(QtCore.QRect(20, 218, 91, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.signal_time_label_3.setFont(font)
        self.signal_time_label_3.setObjectName("signal_time_label_3")
        self.sig_time_spinbox = QtWidgets.QSpinBox(self.receiver_tab_advanced)
        self.sig_time_spinbox.setGeometry(QtCore.QRect(119, 218, 48, 24))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.sig_time_spinbox.setFont(font)
        self.sig_time_spinbox.setProperty("value", 10)
        self.sig_time_spinbox.setObjectName("sig_time_spinbox")
        self.ref_time_label_3 = QtWidgets.QLabel(self.receiver_tab_advanced)
        self.ref_time_label_3.setGeometry(QtCore.QRect(177, 218, 116, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.ref_time_label_3.setFont(font)
        self.ref_time_label_3.setObjectName("ref_time_label_3")
        self.ref_time_spinBox = QtWidgets.QSpinBox(self.receiver_tab_advanced)
        self.ref_time_spinBox.setGeometry(QtCore.QRect(303, 218, 48, 24))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.ref_time_spinBox.setFont(font)
        self.ref_time_spinBox.setSingleStep(1)
        self.ref_time_spinBox.setProperty("value", 10)
        self.ref_time_spinBox.setObjectName("ref_time_spinBox")
        self.loops_label_3 = QtWidgets.QLabel(self.receiver_tab_advanced)
        self.loops_label_3.setGeometry(QtCore.QRect(361, 218, 105, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.loops_label_3.setFont(font)
        self.loops_label_3.setObjectName("loops_label_3")
        self.loops_spinbox = QtWidgets.QSpinBox(self.receiver_tab_advanced)
        self.loops_spinbox.setGeometry(QtCore.QRect(476, 218, 86, 24))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.loops_spinbox.setFont(font)
        self.loops_spinbox.setMaximum(1000000)
        self.loops_spinbox.setProperty("value", 1)
        self.loops_spinbox.setObjectName("loops_spinbox")
        self.ChannelsLabel = QtWidgets.QLabel(self.receiver_tab_advanced)
        self.ChannelsLabel.setGeometry(QtCore.QRect(21, 77, 131, 16))
        self.ChannelsLabel.setObjectName("ChannelsLabel")
        self.RefFreqLabel = QtWidgets.QLabel(self.receiver_tab_advanced)
        self.RefFreqLabel.setGeometry(QtCore.QRect(20, 140, 136, 16))
        self.RefFreqLabel.setObjectName("RefFreqLabel")
        self.FrequencyLabel = QtWidgets.QLabel(self.receiver_tab_advanced)
        self.FrequencyLabel.setGeometry(QtCore.QRect(21, 15, 141, 16))
        self.FrequencyLabel.setObjectName("FrequencyLabel")
        self.label_mode = QtWidgets.QLabel(self.receiver_tab_advanced)
        self.label_mode.setGeometry(QtCore.QRect(21, 108, 35, 16))
        self.label_mode.setObjectName("label_mode")
        self.BandwidthLabel = QtWidgets.QLabel(self.receiver_tab_advanced)
        self.BandwidthLabel.setGeometry(QtCore.QRect(21, 46, 141, 16))
        self.BandwidthLabel.setObjectName("BandwidthLabel")
        self.splitter = QtWidgets.QSplitter(self.receiver_tab_advanced)
        self.splitter.setGeometry(QtCore.QRect(170, 110, 201, 21))
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.mode_signal = QtWidgets.QRadioButton(self.splitter)
        self.mode_signal.setMinimumSize(QtCore.QSize(0, 15))
        self.mode_signal.setObjectName("mode_signal")
        self.mode_switched = QtWidgets.QRadioButton(self.splitter)
        self.mode_switched.setMinimumSize(QtCore.QSize(0, 15))
        self.mode_switched.setChecked(True)
        self.mode_switched.setObjectName("mode_switched")
        self.label_gain = QtWidgets.QLabel(self.receiver_tab_advanced)
        self.label_gain.setGeometry(QtCore.QRect(20, 170, 131, 16))
        self.label_gain.setObjectName("label_gain")
        self.gain = QtWidgets.QLineEdit(self.receiver_tab_advanced)
        self.gain.setGeometry(QtCore.QRect(170, 170, 125, 21))
        self.gain.setReadOnly(False)
        self.gain.setObjectName("gain")
        self.layoutWidget3 = QtWidgets.QWidget(self.receiver_tab_advanced)
        self.layoutWidget3.setGeometry(QtCore.QRect(300, 16, 232, 95))
        self.layoutWidget3.setObjectName("layoutWidget3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.layoutWidget3)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.vlsr_checkbox = QtWidgets.QCheckBox(self.layoutWidget3)
        self.vlsr_checkbox.setEnabled(True)
        self.vlsr_checkbox.setChecked(True)
        self.vlsr_checkbox.setObjectName("vlsr_checkbox")
        self.verticalLayout_2.addWidget(self.vlsr_checkbox)
        self.autoedit_bad_data_checkBox = QtWidgets.QCheckBox(self.layoutWidget3)
        self.autoedit_bad_data_checkBox.setEnabled(True)
        self.autoedit_bad_data_checkBox.setChecked(True)
        self.autoedit_bad_data_checkBox.setObjectName("autoedit_bad_data_checkBox")
        self.verticalLayout_2.addWidget(self.autoedit_bad_data_checkBox)
        self.noise_checkbox = QtWidgets.QCheckBox(self.layoutWidget3)
        self.noise_checkbox.setEnabled(True)
        self.noise_checkbox.setChecked(False)
        self.noise_checkbox.setObjectName("noise_checkbox")
        self.verticalLayout_2.addWidget(self.noise_checkbox)
        self.FrequencyInput = QtWidgets.QDoubleSpinBox(self.receiver_tab_advanced)
        self.FrequencyInput.setGeometry(QtCore.QRect(170, 10, 121, 26))
        self.FrequencyInput.setMinimum(800.0)
        self.FrequencyInput.setMaximum(2300.0)
        self.FrequencyInput.setSingleStep(0.1)
        self.FrequencyInput.setProperty("value", 1420.4)
        self.FrequencyInput.setObjectName("FrequencyInput")
        self.RefFreqInput = QtWidgets.QDoubleSpinBox(self.receiver_tab_advanced)
        self.RefFreqInput.setGeometry(QtCore.QRect(180, 140, 111, 26))
        self.RefFreqInput.setMinimum(800.0)
        self.RefFreqInput.setMaximum(2300.0)
        self.RefFreqInput.setSingleStep(0.1)
        self.RefFreqInput.setProperty("value", 1422.4)
        self.RefFreqInput.setObjectName("RefFreqInput")
        self.BandwidthInput = QtWidgets.QComboBox(self.receiver_tab_advanced)
        self.BandwidthInput.setGeometry(QtCore.QRect(170, 40, 121, 24))
        self.BandwidthInput.setModelColumn(0)
        self.BandwidthInput.setObjectName("BandwidthInput")
        self.BandwidthInput.addItem("")
        self.BandwidthInput.addItem("")
        self.BandwidthInput.addItem("")
        self.BandwidthInput.addItem("")
        self.ChannelsInput = QtWidgets.QComboBox(self.receiver_tab_advanced)
        self.ChannelsInput.setGeometry(QtCore.QRect(170, 70, 121, 24))
        self.ChannelsInput.setObjectName("ChannelsInput")
        self.ChannelsInput.addItem("")
        self.ChannelsInput.addItem("")
        self.ChannelsInput.addItem("")
        self.ChannelsInput.addItem("")
        self.ChannelsInput.addItem("")
        self.ChannelsInput.addItem("")
        self.tabWidget_2.addTab(self.receiver_tab_advanced, "")
        self.infolabel = QtWidgets.QLabel(self.tab)
        self.infolabel.setGeometry(QtCore.QRect(30, 10, 671, 16))
        self.infolabel.setObjectName("infolabel")
        self.Observebase.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.groupBox_spectrum = QtWidgets.QGroupBox(self.tab_2)
        self.groupBox_spectrum.setGeometry(QtCore.QRect(250, 30, 521, 461))
        self.groupBox_spectrum.setObjectName("groupBox_spectrum")
        self.listWidget_spectra = QtWidgets.QListWidget(self.tab_2)
        self.listWidget_spectra.setGeometry(QtCore.QRect(20, 50, 211, 331))
        self.listWidget_spectra.setObjectName("listWidget_spectra")
        self.btn_upload = QtWidgets.QPushButton(self.tab_2)
        self.btn_upload.setGeometry(QtCore.QRect(20, 390, 211, 41))
        self.btn_upload.setObjectName("btn_upload")
        self.label = QtWidgets.QLabel(self.tab_2)
        self.label.setGeometry(QtCore.QRect(20, 20, 231, 16))
        self.label.setObjectName("label")
        self.layoutWidget4 = QtWidgets.QWidget(self.tab_2)
        self.layoutWidget4.setGeometry(QtCore.QRect(590, 0, 277, 32))
        self.layoutWidget4.setObjectName("layoutWidget4")
        self.vel_or_freq_group = QtWidgets.QHBoxLayout(self.layoutWidget4)
        self.vel_or_freq_group.setObjectName("vel_or_freq_group")
        self.radioButton_velocity = QtWidgets.QRadioButton(self.layoutWidget4)
        self.radioButton_velocity.setMinimumSize(QtCore.QSize(0, 30))
        self.radioButton_velocity.setChecked(True)
        self.radioButton_velocity.setObjectName("radioButton_velocity")
        self.vel_or_freq_group.addWidget(self.radioButton_velocity)
        self.radioButton_frequency = QtWidgets.QRadioButton(self.layoutWidget4)
        self.radioButton_frequency.setMinimumSize(QtCore.QSize(0, 30))
        self.radioButton_frequency.setObjectName("radioButton_frequency")
        self.vel_or_freq_group.addWidget(self.radioButton_frequency)
        self.layoutWidget_2 = QtWidgets.QWidget(self.tab_2)
        self.layoutWidget_2.setGeometry(QtCore.QRect(380, 0, 297, 37))
        self.layoutWidget_2.setObjectName("layoutWidget_2")
        self.log_and_norm_group = QtWidgets.QHBoxLayout(self.layoutWidget_2)
        self.log_and_norm_group.setObjectName("log_and_norm_group")
        self.checkBox_dBScale = QtWidgets.QCheckBox(self.layoutWidget_2)
        self.checkBox_dBScale.setObjectName("checkBox_dBScale")
        self.log_and_norm_group.addWidget(self.checkBox_dBScale)
        self.checkBox_normalized = QtWidgets.QCheckBox(self.layoutWidget_2)
        self.checkBox_normalized.setObjectName("checkBox_normalized")
        self.log_and_norm_group.addWidget(self.checkBox_normalized)
        self.Observebase.addTab(self.tab_2, "")
        self.layoutWidget5 = QtWidgets.QWidget(self.centralwidget)
        self.layoutWidget5.setGeometry(QtCore.QRect(0, 0, 2, 2))
        self.layoutWidget5.setObjectName("layoutWidget5")
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout(self.layoutWidget5)
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.layoutWidget6 = QtWidgets.QWidget(self.centralwidget)
        self.layoutWidget6.setGeometry(QtCore.QRect(0, 0, 2, 2))
        self.layoutWidget6.setObjectName("layoutWidget6")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.layoutWidget6)
        self.verticalLayout.setObjectName("verticalLayout")
        self.layoutWidget7 = QtWidgets.QWidget(self.centralwidget)
        self.layoutWidget7.setGeometry(QtCore.QRect(0, 0, 2, 2))
        self.layoutWidget7.setObjectName("layoutWidget7")
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout(self.layoutWidget7)
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.Observebase.setCurrentIndex(0)
        self.tabWidget_2.setCurrentIndex(0)
        self.ChannelsInput.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "SALSA Controller"))
        self.label_4.setText(_translate("MainWindow", "Please: When finished, choose Desired=Stow and press \"Track\" to put telescope in stow position. "))
        self.groupBox.setTitle(_translate("MainWindow", "Tracking"))
        self.objectselector.setCurrentText(_translate("MainWindow", "The Sun"))
        self.objectselector.setItemText(0, _translate("MainWindow", "The Sun"))
        self.objectselector.setItemText(1, _translate("MainWindow", "Satelite A"))
        self.objectselector.setItemText(2, _translate("MainWindow", "Galactic A"))
        self.objectselector.setItemText(3, _translate("MainWindow", "Stow"))
        self.label_5.setText(_translate("MainWindow", "Tracking"))
        self.btn_GO.setText(_translate("MainWindow", "GO"))
        self.cam_link.setText(_translate("MainWindow", "<a href=\"http://129.16.208.83/view/#view\">Here</a>"))
        self.label_7.setText(_translate("MainWindow", "Access live webcam "))
        self.groupBox_2.setTitle(_translate("MainWindow", "GroupBox"))
        self.label_14.setText(_translate("MainWindow", "Observing time (s)"))
        self.btn_start_obs_ez.setText(_translate("MainWindow", "Start"))
        self.stop_obs_ez.setText(_translate("MainWindow", "Cancel"))
        self.groupBox_spectrum_ez.setTitle(_translate("MainWindow", "Spectrum"))
        self.btn_plot_ez.setText(_translate("MainWindow", "plot"))
        self.pushButton.setText(_translate("MainWindow", "Eng"))
        self.btn_sve.setText(_translate("MainWindow", "Sve"))
        self.Observebase.setTabText(self.Observebase.indexOf(self.tab_Observe), _translate("MainWindow", "Observe"))
        self.groupBox_tc.setTitle(_translate("MainWindow", "Telescope movement control"))
        self.label_currentaltaz.setText(_translate("MainWindow", "Current horizontal"))
        self.label_cur_alt.setText(_translate("MainWindow", "Alt:"))
        self.cur_alt.setText(_translate("MainWindow", "0"))
        self.label_currentpointing.setText(_translate("MainWindow", "Calc. target horizontal"))
        self.coordlabel_left.setText(_translate("MainWindow", "Longitude"))
        self.inputleftcoord.setText(_translate("MainWindow", "120"))
        self.btn_track.setText(_translate("MainWindow", "Track"))
        self.label_cur_alt_2.setText(_translate("MainWindow", "Alt:"))
        self.calc_des_left.setText(_translate("MainWindow", "0"))
        self.btn_GNSS_lh.setText(_translate("MainWindow", "GNSS Az-El View"))
        self.coordlabel_right.setText(_translate("MainWindow", "Latitude"))
        self.inputrightcoord.setText(_translate("MainWindow", "0"))
        self.label_cur_az.setText(_translate("MainWindow", "Az:"))
        self.cur_az.setText(_translate("MainWindow", "0"))
        self.label_2.setText(_translate("MainWindow", "Az[deg]:"))
        self.offset_right.setText(_translate("MainWindow", "0"))
        self.label_offset.setText(_translate("MainWindow", "Desired horisontal offset"))
        self.label_offset_left.setText(_translate("MainWindow", "Alt[deg]:"))
        self.offset_left.setText(_translate("MainWindow", "0"))
        self.label_cur_az_2.setText(_translate("MainWindow", "Az:"))
        self.calc_des_right.setText(_translate("MainWindow", "0"))
        self.btn_reset.setText(_translate("MainWindow", "Reset"))
        self.label_newtarget.setText(_translate("MainWindow", "Desired"))
        self.coordselector.setItemText(0, _translate("MainWindow", "Galactic"))
        self.coordselector.setItemText(1, _translate("MainWindow", "Horizontal"))
        self.coordselector.setItemText(2, _translate("MainWindow", "Eq. J2000"))
        self.coordselector.setItemText(3, _translate("MainWindow", "Eq. B1950"))
        self.coordselector.setItemText(4, _translate("MainWindow", "The Sun"))
        self.coordselector.setItemText(5, _translate("MainWindow", "The Moon"))
        self.coordselector.setItemText(6, _translate("MainWindow", "Cas. A"))
        self.coordselector.setItemText(7, _translate("MainWindow", "GNSS"))
        self.coordselector.setItemText(8, _translate("MainWindow", "Stow"))
        self.groupBox_3.setTitle(_translate("MainWindow", "Receiver control"))
        self.progresslabel.setText(_translate("MainWindow", "Measurement progress:"))
        self.btn_observe.setText(_translate("MainWindow", "Measure"))
        self.btn_abort.setText(_translate("MainWindow", "Abort measurement"))
        self.FrequencyLabel_2.setText(_translate("MainWindow", "Integration time [s]:"))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.receiver_tab_basic), _translate("MainWindow", "Basic"))
        self.cycle_checkbox.setText(_translate("MainWindow", "Manually specify cycle times"))
        self.signal_time_label_3.setText(_translate("MainWindow", "Signal time [s]:"))
        self.ref_time_label_3.setText(_translate("MainWindow", "Reference time [s]:"))
        self.loops_label_3.setText(_translate("MainWindow", "Number of loops:"))
        self.ChannelsLabel.setText(_translate("MainWindow", "Channels [#]"))
        self.RefFreqLabel.setText(_translate("MainWindow", "Ref. freq. [MHz]"))
        self.FrequencyLabel.setText(_translate("MainWindow", "Frequency [MHz]"))
        self.label_mode.setText(_translate("MainWindow", "Mode"))
        self.BandwidthLabel.setText(_translate("MainWindow", "Bandwidth [MHz]"))
        self.mode_signal.setText(_translate("MainWindow", "Signal"))
        self.mode_switched.setText(_translate("MainWindow", "Switched"))
        self.label_gain.setText(_translate("MainWindow", "Gain factor"))
        self.gain.setText(_translate("MainWindow", "930"))
        self.vlsr_checkbox.setText(_translate("MainWindow", "Translate to VLSR frame"))
        self.autoedit_bad_data_checkBox.setText(_translate("MainWindow", "Remove RFI"))
        self.noise_checkbox.setText(_translate("MainWindow", "Noise diode"))
        self.BandwidthInput.setItemText(0, _translate("MainWindow", "2.5"))
        self.BandwidthInput.setItemText(1, _translate("MainWindow", "5.0"))
        self.BandwidthInput.setItemText(2, _translate("MainWindow", "10.0"))
        self.BandwidthInput.setItemText(3, _translate("MainWindow", "25.0"))
        self.ChannelsInput.setItemText(0, _translate("MainWindow", "128"))
        self.ChannelsInput.setItemText(1, _translate("MainWindow", "256"))
        self.ChannelsInput.setItemText(2, _translate("MainWindow", "512"))
        self.ChannelsInput.setItemText(3, _translate("MainWindow", "1024"))
        self.ChannelsInput.setItemText(4, _translate("MainWindow", "2048"))
        self.ChannelsInput.setItemText(5, _translate("MainWindow", "4096"))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.receiver_tab_advanced), _translate("MainWindow", "Advanced"))
        self.infolabel.setText(_translate("MainWindow", "Please: When finished, choose Desired=Stow and press \"Track\" to put telescope in stow position. "))
        self.Observebase.setTabText(self.Observebase.indexOf(self.tab), _translate("MainWindow", "Advanced"))
        self.groupBox_spectrum.setTitle(_translate("MainWindow", "Plot of selected spectrum"))
        self.btn_upload.setText(_translate("MainWindow", "Upload selected to archive"))
        self.label.setText(_translate("MainWindow", "List of measured spectra [date-UT]"))
        self.radioButton_velocity.setText(_translate("MainWindow", "Velocity"))
        self.radioButton_frequency.setText(_translate("MainWindow", "Frequency"))
        self.checkBox_dBScale.setText(_translate("MainWindow", "dB scale"))
        self.checkBox_normalized.setText(_translate("MainWindow", "Normalized"))
        self.Observebase.setTabText(self.Observebase.indexOf(self.tab_2), _translate("MainWindow", "Measured spectra"))

