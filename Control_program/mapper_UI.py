# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'SALSA_mapper_UI.ui'
#
# Created: Mon Jun 19 16:40:24 2017
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(773, 576)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.tabWidget = QtGui.QTabWidget(self.centralwidget)
        self.tabWidget.setGeometry(QtCore.QRect(0, 0, 761, 541))
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tab = QtGui.QWidget()
        self.tab.setObjectName(_fromUtf8("tab"))
        self.groupBox_tc = QtGui.QGroupBox(self.tab)
        self.groupBox_tc.setGeometry(QtCore.QRect(20, 0, 661, 181))
        self.groupBox_tc.setObjectName(_fromUtf8("groupBox_tc"))
        self.layoutWidget = QtGui.QWidget(self.groupBox_tc)
        self.layoutWidget.setGeometry(QtCore.QRect(10, 30, 621, 141))
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.gridLayout = QtGui.QGridLayout(self.layoutWidget)
        self.gridLayout.setMargin(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.label_newtarget = QtGui.QLabel(self.layoutWidget)
        self.label_newtarget.setObjectName(_fromUtf8("label_newtarget"))
        self.horizontalLayout_5.addWidget(self.label_newtarget)
        self.coordselector = QtGui.QComboBox(self.layoutWidget)
        self.coordselector.setObjectName(_fromUtf8("coordselector"))
        self.coordselector.addItem(_fromUtf8(""))
        self.coordselector.addItem(_fromUtf8(""))
        self.coordselector.addItem(_fromUtf8(""))
        self.coordselector.addItem(_fromUtf8(""))
        self.coordselector.addItem(_fromUtf8(""))
        self.coordselector.addItem(_fromUtf8(""))
        self.horizontalLayout_5.addWidget(self.coordselector)
        self.gridLayout.addLayout(self.horizontalLayout_5, 0, 0, 1, 1)
        self.horizontalLayout_6 = QtGui.QHBoxLayout()
        self.horizontalLayout_6.setObjectName(_fromUtf8("horizontalLayout_6"))
        self.coordlabel_left = QtGui.QLabel(self.layoutWidget)
        self.coordlabel_left.setObjectName(_fromUtf8("coordlabel_left"))
        self.horizontalLayout_6.addWidget(self.coordlabel_left)
        self.inputleftcoord = QtGui.QLineEdit(self.layoutWidget)
        self.inputleftcoord.setObjectName(_fromUtf8("inputleftcoord"))
        self.horizontalLayout_6.addWidget(self.inputleftcoord)
        self.gridLayout.addLayout(self.horizontalLayout_6, 0, 1, 1, 1)
        self.horizontalLayout_7 = QtGui.QHBoxLayout()
        self.horizontalLayout_7.setObjectName(_fromUtf8("horizontalLayout_7"))
        self.coordlabel_right = QtGui.QLabel(self.layoutWidget)
        self.coordlabel_right.setObjectName(_fromUtf8("coordlabel_right"))
        self.horizontalLayout_7.addWidget(self.coordlabel_right)
        self.inputrightcoord = QtGui.QLineEdit(self.layoutWidget)
        self.inputrightcoord.setObjectName(_fromUtf8("inputrightcoord"))
        self.horizontalLayout_7.addWidget(self.inputrightcoord)
        self.gridLayout.addLayout(self.horizontalLayout_7, 0, 2, 1, 1)
        self.horizontalLayout_11 = QtGui.QHBoxLayout()
        self.horizontalLayout_11.setObjectName(_fromUtf8("horizontalLayout_11"))
        self.label_offset_left = QtGui.QLabel(self.layoutWidget)
        self.label_offset_left.setObjectName(_fromUtf8("label_offset_left"))
        self.horizontalLayout_11.addWidget(self.label_offset_left)
        self.offset_left = QtGui.QLineEdit(self.layoutWidget)
        self.offset_left.setReadOnly(False)
        self.offset_left.setObjectName(_fromUtf8("offset_left"))
        self.horizontalLayout_11.addWidget(self.offset_left)
        self.gridLayout.addLayout(self.horizontalLayout_11, 1, 1, 1, 1)
        self.horizontalLayout_13 = QtGui.QHBoxLayout()
        self.horizontalLayout_13.setObjectName(_fromUtf8("horizontalLayout_13"))
        self.label_offset_right = QtGui.QLabel(self.layoutWidget)
        self.label_offset_right.setObjectName(_fromUtf8("label_offset_right"))
        self.horizontalLayout_13.addWidget(self.label_offset_right)
        self.offset_right = QtGui.QLineEdit(self.layoutWidget)
        self.offset_right.setReadOnly(False)
        self.offset_right.setObjectName(_fromUtf8("offset_right"))
        self.horizontalLayout_13.addWidget(self.offset_right)
        self.gridLayout.addLayout(self.horizontalLayout_13, 1, 2, 1, 1)
        self.horizontalLayout_14 = QtGui.QHBoxLayout()
        self.horizontalLayout_14.setObjectName(_fromUtf8("horizontalLayout_14"))
        self.label_newtarget_2 = QtGui.QLabel(self.layoutWidget)
        self.label_newtarget_2.setObjectName(_fromUtf8("label_newtarget_2"))
        self.horizontalLayout_14.addWidget(self.label_newtarget_2)
        self.coordselector_steps = QtGui.QComboBox(self.layoutWidget)
        self.coordselector_steps.setObjectName(_fromUtf8("coordselector_steps"))
        self.coordselector_steps.addItem(_fromUtf8(""))
        self.coordselector_steps.addItem(_fromUtf8(""))
        self.coordselector_steps.addItem(_fromUtf8(""))
        self.coordselector_steps.addItem(_fromUtf8(""))
        self.horizontalLayout_14.addWidget(self.coordselector_steps)
        self.label_newtarget_3 = QtGui.QLabel(self.layoutWidget)
        self.label_newtarget_3.setObjectName(_fromUtf8("label_newtarget_3"))
        self.horizontalLayout_14.addWidget(self.label_newtarget_3)
        self.gridLayout.addLayout(self.horizontalLayout_14, 1, 0, 1, 1)
        self.horizontalLayout_16 = QtGui.QHBoxLayout()
        self.horizontalLayout_16.setObjectName(_fromUtf8("horizontalLayout_16"))
        self.nsteps_left = QtGui.QSpinBox(self.layoutWidget)
        self.nsteps_left.setMinimum(1)
        self.nsteps_left.setMaximum(3600)
        self.nsteps_left.setSingleStep(1)
        self.nsteps_left.setProperty("value", 9)
        self.nsteps_left.setObjectName(_fromUtf8("nsteps_left"))
        self.horizontalLayout_16.addWidget(self.nsteps_left)
        self.gridLayout.addLayout(self.horizontalLayout_16, 2, 1, 1, 1)
        self.horizontalLayout_15 = QtGui.QHBoxLayout()
        self.horizontalLayout_15.setObjectName(_fromUtf8("horizontalLayout_15"))
        self.nsteps_right = QtGui.QSpinBox(self.layoutWidget)
        self.nsteps_right.setMinimum(1)
        self.nsteps_right.setMaximum(3600)
        self.nsteps_right.setSingleStep(1)
        self.nsteps_right.setProperty("value", 9)
        self.nsteps_right.setObjectName(_fromUtf8("nsteps_right"))
        self.horizontalLayout_15.addWidget(self.nsteps_right)
        self.gridLayout.addLayout(self.horizontalLayout_15, 2, 2, 1, 1)
        self.label_newtarget_4 = QtGui.QLabel(self.layoutWidget)
        self.label_newtarget_4.setObjectName(_fromUtf8("label_newtarget_4"))
        self.gridLayout.addWidget(self.label_newtarget_4, 2, 0, 1, 1)
        self.scale_az_offset = QtGui.QCheckBox(self.layoutWidget)
        self.scale_az_offset.setEnabled(True)
        self.scale_az_offset.setChecked(True)
        self.scale_az_offset.setObjectName(_fromUtf8("scale_az_offset"))
        self.gridLayout.addWidget(self.scale_az_offset, 3, 2, 1, 1)
        self.allow_flip = QtGui.QCheckBox(self.layoutWidget)
        self.allow_flip.setEnabled(True)
        self.allow_flip.setChecked(False)
        self.allow_flip.setObjectName(_fromUtf8("allow_flip"))
        self.gridLayout.addWidget(self.allow_flip, 3, 0, 1, 1)
        self.groupBox_3 = QtGui.QGroupBox(self.tab)
        self.groupBox_3.setGeometry(QtCore.QRect(20, 180, 691, 311))
        self.groupBox_3.setObjectName(_fromUtf8("groupBox_3"))
        self.tabWidget_3 = QtGui.QTabWidget(self.groupBox_3)
        self.tabWidget_3.setGeometry(QtCore.QRect(10, 20, 651, 271))
        self.tabWidget_3.setObjectName(_fromUtf8("tabWidget_3"))
        self.receiver_tab_basic_4 = QtGui.QWidget()
        self.receiver_tab_basic_4.setObjectName(_fromUtf8("receiver_tab_basic_4"))
        self.progresslabel_4 = QtGui.QLabel(self.receiver_tab_basic_4)
        self.progresslabel_4.setGeometry(QtCore.QRect(20, 80, 161, 21))
        self.progresslabel_4.setObjectName(_fromUtf8("progresslabel_4"))
        self.layoutWidget_12 = QtGui.QWidget(self.receiver_tab_basic_4)
        self.layoutWidget_12.setGeometry(QtCore.QRect(20, 110, 581, 101))
        self.layoutWidget_12.setObjectName(_fromUtf8("layoutWidget_12"))
        self.gridLayout_13 = QtGui.QGridLayout(self.layoutWidget_12)
        self.gridLayout_13.setMargin(0)
        self.gridLayout_13.setObjectName(_fromUtf8("gridLayout_13"))
        self.label_currentaltaz_3 = QtGui.QLabel(self.layoutWidget_12)
        self.label_currentaltaz_3.setObjectName(_fromUtf8("label_currentaltaz_3"))
        self.gridLayout_13.addWidget(self.label_currentaltaz_3, 1, 0, 1, 1)
        self.horizontalLayout_25 = QtGui.QHBoxLayout()
        self.horizontalLayout_25.setObjectName(_fromUtf8("horizontalLayout_25"))
        self.label_cur_az_5 = QtGui.QLabel(self.layoutWidget_12)
        self.label_cur_az_5.setObjectName(_fromUtf8("label_cur_az_5"))
        self.horizontalLayout_25.addWidget(self.label_cur_az_5)
        self.cur_az = QtGui.QLineEdit(self.layoutWidget_12)
        self.cur_az.setReadOnly(True)
        self.cur_az.setObjectName(_fromUtf8("cur_az"))
        self.horizontalLayout_25.addWidget(self.cur_az)
        self.gridLayout_13.addLayout(self.horizontalLayout_25, 1, 2, 1, 1)
        self.label_currentpointing_3 = QtGui.QLabel(self.layoutWidget_12)
        self.label_currentpointing_3.setObjectName(_fromUtf8("label_currentpointing_3"))
        self.gridLayout_13.addWidget(self.label_currentpointing_3, 0, 0, 1, 1)
        self.horizontalLayout_27 = QtGui.QHBoxLayout()
        self.horizontalLayout_27.setObjectName(_fromUtf8("horizontalLayout_27"))
        self.label_cur_alt_5 = QtGui.QLabel(self.layoutWidget_12)
        self.label_cur_alt_5.setObjectName(_fromUtf8("label_cur_alt_5"))
        self.horizontalLayout_27.addWidget(self.label_cur_alt_5)
        self.calc_des_left = QtGui.QLineEdit(self.layoutWidget_12)
        self.calc_des_left.setReadOnly(True)
        self.calc_des_left.setObjectName(_fromUtf8("calc_des_left"))
        self.horizontalLayout_27.addWidget(self.calc_des_left)
        self.gridLayout_13.addLayout(self.horizontalLayout_27, 0, 1, 1, 1)
        self.horizontalLayout_28 = QtGui.QHBoxLayout()
        self.horizontalLayout_28.setObjectName(_fromUtf8("horizontalLayout_28"))
        self.label_cur_alt_6 = QtGui.QLabel(self.layoutWidget_12)
        self.label_cur_alt_6.setObjectName(_fromUtf8("label_cur_alt_6"))
        self.horizontalLayout_28.addWidget(self.label_cur_alt_6)
        self.cur_alt = QtGui.QLineEdit(self.layoutWidget_12)
        self.cur_alt.setReadOnly(True)
        self.cur_alt.setObjectName(_fromUtf8("cur_alt"))
        self.horizontalLayout_28.addWidget(self.cur_alt)
        self.gridLayout_13.addLayout(self.horizontalLayout_28, 1, 1, 1, 1)
        self.horizontalLayout_29 = QtGui.QHBoxLayout()
        self.horizontalLayout_29.setObjectName(_fromUtf8("horizontalLayout_29"))
        self.label_cur_az_6 = QtGui.QLabel(self.layoutWidget_12)
        self.label_cur_az_6.setObjectName(_fromUtf8("label_cur_az_6"))
        self.horizontalLayout_29.addWidget(self.label_cur_az_6)
        self.calc_des_right = QtGui.QLineEdit(self.layoutWidget_12)
        self.calc_des_right.setReadOnly(True)
        self.calc_des_right.setObjectName(_fromUtf8("calc_des_right"))
        self.horizontalLayout_29.addWidget(self.calc_des_right)
        self.gridLayout_13.addLayout(self.horizontalLayout_29, 0, 2, 1, 1)
        self.layoutWidget_13 = QtGui.QWidget(self.receiver_tab_basic_4)
        self.layoutWidget_13.setGeometry(QtCore.QRect(20, 10, 486, 29))
        self.layoutWidget_13.setObjectName(_fromUtf8("layoutWidget_13"))
        self.horizontalLayout_10 = QtGui.QHBoxLayout(self.layoutWidget_13)
        self.horizontalLayout_10.setMargin(0)
        self.horizontalLayout_10.setObjectName(_fromUtf8("horizontalLayout_10"))
        self.IntegrationTimeLabel_2 = QtGui.QLabel(self.layoutWidget_13)
        self.IntegrationTimeLabel_2.setObjectName(_fromUtf8("IntegrationTimeLabel_2"))
        self.horizontalLayout_10.addWidget(self.IntegrationTimeLabel_2)
        self.int_time_spinbox = QtGui.QSpinBox(self.layoutWidget_13)
        self.int_time_spinbox.setMinimum(1)
        self.int_time_spinbox.setMaximum(3600)
        self.int_time_spinbox.setSingleStep(1)
        self.int_time_spinbox.setProperty("value", 2)
        self.int_time_spinbox.setObjectName(_fromUtf8("int_time_spinbox"))
        self.horizontalLayout_10.addWidget(self.int_time_spinbox)
        self.btn_observe = QtGui.QPushButton(self.layoutWidget_13)
        self.btn_observe.setObjectName(_fromUtf8("btn_observe"))
        self.horizontalLayout_10.addWidget(self.btn_observe)
        self.btn_abort = QtGui.QPushButton(self.layoutWidget_13)
        self.btn_abort.setDefault(False)
        self.btn_abort.setObjectName(_fromUtf8("btn_abort"))
        self.horizontalLayout_10.addWidget(self.btn_abort)
        self.btn_reset = QtGui.QPushButton(self.receiver_tab_basic_4)
        self.btn_reset.setGeometry(QtCore.QRect(510, 10, 85, 27))
        self.btn_reset.setObjectName(_fromUtf8("btn_reset"))
        self.progressBar = QtGui.QProgressBar(self.receiver_tab_basic_4)
        self.progressBar.setGeometry(QtCore.QRect(150, 80, 441, 23))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.infolabel = QtGui.QLabel(self.receiver_tab_basic_4)
        self.infolabel.setGeometry(QtCore.QRect(20, 50, 581, 21))
        self.infolabel.setObjectName(_fromUtf8("infolabel"))
        self.loop_grid_checkbox = QtGui.QCheckBox(self.receiver_tab_basic_4)
        self.loop_grid_checkbox.setEnabled(True)
        self.loop_grid_checkbox.setGeometry(QtCore.QRect(20, 210, 341, 22))
        self.loop_grid_checkbox.setChecked(False)
        self.loop_grid_checkbox.setObjectName(_fromUtf8("loop_grid_checkbox"))
        self.tabWidget_3.addTab(self.receiver_tab_basic_4, _fromUtf8(""))
        self.receiver_tab_advanced_4 = QtGui.QWidget()
        self.receiver_tab_advanced_4.setObjectName(_fromUtf8("receiver_tab_advanced_4"))
        self.gridLayout_14 = QtGui.QGridLayout(self.receiver_tab_advanced_4)
        self.gridLayout_14.setObjectName(_fromUtf8("gridLayout_14"))
        self.gridLayout_15 = QtGui.QGridLayout()
        self.gridLayout_15.setObjectName(_fromUtf8("gridLayout_15"))
        self.label_mode_4 = QtGui.QLabel(self.receiver_tab_advanced_4)
        self.label_mode_4.setObjectName(_fromUtf8("label_mode_4"))
        self.gridLayout_15.addWidget(self.label_mode_4, 8, 0, 1, 1)
        self.gridLayout_16 = QtGui.QGridLayout()
        self.gridLayout_16.setObjectName(_fromUtf8("gridLayout_16"))
        self.groupBox_5 = QtGui.QGroupBox(self.receiver_tab_advanced_4)
        self.groupBox_5.setTitle(_fromUtf8(""))
        self.groupBox_5.setObjectName(_fromUtf8("groupBox_5"))
        self.layoutWidget_14 = QtGui.QWidget(self.groupBox_5)
        self.layoutWidget_14.setGeometry(QtCore.QRect(10, 0, 171, 24))
        self.layoutWidget_14.setObjectName(_fromUtf8("layoutWidget_14"))
        self.horizontalLayout_8 = QtGui.QHBoxLayout(self.layoutWidget_14)
        self.horizontalLayout_8.setMargin(0)
        self.horizontalLayout_8.setObjectName(_fromUtf8("horizontalLayout_8"))
        self.mode_signal = QtGui.QRadioButton(self.layoutWidget_14)
        self.mode_signal.setChecked(True)
        self.mode_signal.setObjectName(_fromUtf8("mode_signal"))
        self.horizontalLayout_8.addWidget(self.mode_signal)
        self.mode_switched = QtGui.QRadioButton(self.layoutWidget_14)
        self.mode_switched.setChecked(False)
        self.mode_switched.setObjectName(_fromUtf8("mode_switched"))
        self.horizontalLayout_8.addWidget(self.mode_switched)
        self.gridLayout_16.addWidget(self.groupBox_5, 0, 0, 1, 2)
        self.gridLayout_15.addLayout(self.gridLayout_16, 8, 1, 1, 1)
        self.BandwidthLabel_4 = QtGui.QLabel(self.receiver_tab_advanced_4)
        self.BandwidthLabel_4.setObjectName(_fromUtf8("BandwidthLabel_4"))
        self.gridLayout_15.addWidget(self.BandwidthLabel_4, 2, 0, 1, 1)
        self.ChannelsInput = QtGui.QLineEdit(self.receiver_tab_advanced_4)
        self.ChannelsInput.setObjectName(_fromUtf8("ChannelsInput"))
        self.gridLayout_15.addWidget(self.ChannelsInput, 3, 1, 1, 1)
        self.BandwidthInput = QtGui.QLineEdit(self.receiver_tab_advanced_4)
        self.BandwidthInput.setObjectName(_fromUtf8("BandwidthInput"))
        self.gridLayout_15.addWidget(self.BandwidthInput, 2, 1, 1, 1)
        self.ChannelsLabel_4 = QtGui.QLabel(self.receiver_tab_advanced_4)
        self.ChannelsLabel_4.setObjectName(_fromUtf8("ChannelsLabel_4"))
        self.gridLayout_15.addWidget(self.ChannelsLabel_4, 3, 0, 1, 1)
        self.RefFreqLabel_4 = QtGui.QLabel(self.receiver_tab_advanced_4)
        self.RefFreqLabel_4.setObjectName(_fromUtf8("RefFreqLabel_4"))
        self.gridLayout_15.addWidget(self.RefFreqLabel_4, 9, 0, 1, 1)
        self.RefFreqInput = QtGui.QLineEdit(self.receiver_tab_advanced_4)
        self.RefFreqInput.setObjectName(_fromUtf8("RefFreqInput"))
        self.gridLayout_15.addWidget(self.RefFreqInput, 9, 1, 1, 1)
        self.FrequencyLabel_7 = QtGui.QLabel(self.receiver_tab_advanced_4)
        self.FrequencyLabel_7.setObjectName(_fromUtf8("FrequencyLabel_7"))
        self.gridLayout_15.addWidget(self.FrequencyLabel_7, 0, 0, 1, 1)
        self.FrequencyInput = QtGui.QLineEdit(self.receiver_tab_advanced_4)
        self.FrequencyInput.setObjectName(_fromUtf8("FrequencyInput"))
        self.gridLayout_15.addWidget(self.FrequencyInput, 0, 1, 1, 1)
        self.vlsr_checkbox = QtGui.QCheckBox(self.receiver_tab_advanced_4)
        self.vlsr_checkbox.setEnabled(True)
        self.vlsr_checkbox.setChecked(True)
        self.vlsr_checkbox.setObjectName(_fromUtf8("vlsr_checkbox"))
        self.gridLayout_15.addWidget(self.vlsr_checkbox, 0, 2, 1, 1)
        self.autoedit_bad_data_checkBox = QtGui.QCheckBox(self.receiver_tab_advanced_4)
        self.autoedit_bad_data_checkBox.setEnabled(True)
        self.autoedit_bad_data_checkBox.setChecked(True)
        self.autoedit_bad_data_checkBox.setObjectName(_fromUtf8("autoedit_bad_data_checkBox"))
        self.gridLayout_15.addWidget(self.autoedit_bad_data_checkBox, 2, 2, 1, 1)
        self.LNA_checkbox = QtGui.QCheckBox(self.receiver_tab_advanced_4)
        self.LNA_checkbox.setEnabled(True)
        self.LNA_checkbox.setChecked(True)
        self.LNA_checkbox.setObjectName(_fromUtf8("LNA_checkbox"))
        self.gridLayout_15.addWidget(self.LNA_checkbox, 3, 2, 1, 1)
        self.noise_checkbox = QtGui.QCheckBox(self.receiver_tab_advanced_4)
        self.noise_checkbox.setEnabled(True)
        self.noise_checkbox.setChecked(False)
        self.noise_checkbox.setObjectName(_fromUtf8("noise_checkbox"))
        self.gridLayout_15.addWidget(self.noise_checkbox, 8, 2, 1, 1)
        self.horizontalLayout_26 = QtGui.QHBoxLayout()
        self.horizontalLayout_26.setObjectName(_fromUtf8("horizontalLayout_26"))
        self.label_gain_3 = QtGui.QLabel(self.receiver_tab_advanced_4)
        self.label_gain_3.setObjectName(_fromUtf8("label_gain_3"))
        self.horizontalLayout_26.addWidget(self.label_gain_3)
        self.gain = QtGui.QLineEdit(self.receiver_tab_advanced_4)
        self.gain.setReadOnly(False)
        self.gain.setObjectName(_fromUtf8("gain"))
        self.horizontalLayout_26.addWidget(self.gain)
        self.gridLayout_15.addLayout(self.horizontalLayout_26, 9, 2, 1, 1)
        self.gridLayout_14.addLayout(self.gridLayout_15, 0, 0, 1, 7)
        self.cycle_checkbox = QtGui.QCheckBox(self.receiver_tab_advanced_4)
        self.cycle_checkbox.setEnabled(True)
        self.cycle_checkbox.setChecked(False)
        self.cycle_checkbox.setObjectName(_fromUtf8("cycle_checkbox"))
        self.gridLayout_14.addWidget(self.cycle_checkbox, 1, 0, 1, 3)
        self.signal_time_label_5 = QtGui.QLabel(self.receiver_tab_advanced_4)
        self.signal_time_label_5.setObjectName(_fromUtf8("signal_time_label_5"))
        self.gridLayout_14.addWidget(self.signal_time_label_5, 2, 0, 1, 1)
        self.sig_time_spinbox = QtGui.QSpinBox(self.receiver_tab_advanced_4)
        self.sig_time_spinbox.setProperty("value", 10)
        self.sig_time_spinbox.setObjectName(_fromUtf8("sig_time_spinbox"))
        self.gridLayout_14.addWidget(self.sig_time_spinbox, 2, 1, 1, 1)
        self.ref_time_label_5 = QtGui.QLabel(self.receiver_tab_advanced_4)
        self.ref_time_label_5.setObjectName(_fromUtf8("ref_time_label_5"))
        self.gridLayout_14.addWidget(self.ref_time_label_5, 2, 2, 1, 1)
        self.ref_time_spinbox = QtGui.QSpinBox(self.receiver_tab_advanced_4)
        self.ref_time_spinbox.setSingleStep(1)
        self.ref_time_spinbox.setProperty("value", 10)
        self.ref_time_spinbox.setObjectName(_fromUtf8("ref_time_spinbox"))
        self.gridLayout_14.addWidget(self.ref_time_spinbox, 2, 3, 1, 1)
        self.loops_label_5 = QtGui.QLabel(self.receiver_tab_advanced_4)
        self.loops_label_5.setObjectName(_fromUtf8("loops_label_5"))
        self.gridLayout_14.addWidget(self.loops_label_5, 2, 4, 1, 1)
        self.loops_spinbox = QtGui.QSpinBox(self.receiver_tab_advanced_4)
        self.loops_spinbox.setMaximum(1000000)
        self.loops_spinbox.setProperty("value", 1)
        self.loops_spinbox.setObjectName(_fromUtf8("loops_spinbox"))
        self.gridLayout_14.addWidget(self.loops_spinbox, 2, 5, 1, 1)
        self.tabWidget_3.addTab(self.receiver_tab_advanced_4, _fromUtf8(""))
        self.tabWidget.addTab(self.tab, _fromUtf8(""))
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName(_fromUtf8("tab_2"))
        self.groupBox_plot = QtGui.QGroupBox(self.tab_2)
        self.groupBox_plot.setGeometry(QtCore.QRect(250, 20, 521, 461))
        self.groupBox_plot.setObjectName(_fromUtf8("groupBox_plot"))
        self.listWidget_measurements = QtGui.QListWidget(self.tab_2)
        self.listWidget_measurements.setGeometry(QtCore.QRect(20, 50, 211, 331))
        self.listWidget_measurements.setObjectName(_fromUtf8("listWidget_measurements"))
        self.label = QtGui.QLabel(self.tab_2)
        self.label.setGeometry(QtCore.QRect(20, 20, 231, 16))
        self.label.setObjectName(_fromUtf8("label"))
        self.btn_fit = QtGui.QPushButton(self.tab_2)
        self.btn_fit.setGeometry(QtCore.QRect(20, 400, 211, 41))
        self.btn_fit.setObjectName(_fromUtf8("btn_fit"))
        self.tabWidget.addTab(self.tab_2, _fromUtf8(""))
        self.layoutWidget1 = QtGui.QWidget(self.centralwidget)
        self.layoutWidget1.setGeometry(QtCore.QRect(0, 0, 2, 2))
        self.layoutWidget1.setObjectName(_fromUtf8("layoutWidget1"))
        self.horizontalLayout_9 = QtGui.QHBoxLayout(self.layoutWidget1)
        self.horizontalLayout_9.setMargin(0)
        self.horizontalLayout_9.setObjectName(_fromUtf8("horizontalLayout_9"))
        self.layoutWidget2 = QtGui.QWidget(self.centralwidget)
        self.layoutWidget2.setGeometry(QtCore.QRect(0, 0, 2, 2))
        self.layoutWidget2.setObjectName(_fromUtf8("layoutWidget2"))
        self.verticalLayout = QtGui.QVBoxLayout(self.layoutWidget2)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.layoutWidget3 = QtGui.QWidget(self.centralwidget)
        self.layoutWidget3.setGeometry(QtCore.QRect(0, 0, 2, 2))
        self.layoutWidget3.setObjectName(_fromUtf8("layoutWidget3"))
        self.horizontalLayout_12 = QtGui.QHBoxLayout(self.layoutWidget3)
        self.horizontalLayout_12.setMargin(0)
        self.horizontalLayout_12.setObjectName(_fromUtf8("horizontalLayout_12"))
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget_3.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "SALSA mapper", None))
        self.groupBox_tc.setTitle(_translate("MainWindow", "Grid setup", None))
        self.label_newtarget.setText(_translate("MainWindow", "Center on ", None))
        self.coordselector.setItemText(0, _translate("MainWindow", "The Sun", None))
        self.coordselector.setItemText(1, _translate("MainWindow", "Galactic", None))
        self.coordselector.setItemText(2, _translate("MainWindow", "Horizontal", None))
        self.coordselector.setItemText(3, _translate("MainWindow", "Eq. J2000", None))
        self.coordselector.setItemText(4, _translate("MainWindow", "Eq. B1950", None))
        self.coordselector.setItemText(5, _translate("MainWindow", "Cas. A", None))
        self.coordlabel_left.setText(_translate("MainWindow", "Longitude [deg]", None))
        self.inputleftcoord.setText(_translate("MainWindow", "0", None))
        self.coordlabel_right.setText(_translate("MainWindow", "Latitude [deg]", None))
        self.inputrightcoord.setText(_translate("MainWindow", "0", None))
        self.label_offset_left.setText(_translate("MainWindow", "[deg]:", None))
        self.offset_left.setText(_translate("MainWindow", "1.5", None))
        self.label_offset_right.setText(_translate("MainWindow", "[deg]:", None))
        self.offset_right.setText(_translate("MainWindow", "1.5", None))
        self.label_newtarget_2.setText(_translate("MainWindow", "with", None))
        self.coordselector_steps.setItemText(0, _translate("MainWindow", "Horizontal", None))
        self.coordselector_steps.setItemText(1, _translate("MainWindow", "Galactic", None))
        self.coordselector_steps.setItemText(2, _translate("MainWindow", "Eq. J2000", None))
        self.coordselector_steps.setItemText(3, _translate("MainWindow", "Eq. B1950", None))
        self.label_newtarget_3.setText(_translate("MainWindow", "steps of size", None))
        self.label_newtarget_4.setText(_translate("MainWindow", "and respective number of points", None))
        self.scale_az_offset.setText(_translate("MainWindow", "Scale Az. offset with cos(alt)", None))
        self.allow_flip.setText(_translate("MainWindow", "Allow flip alt <90deg to >90deg", None))
        self.groupBox_3.setTitle(_translate("MainWindow", "Measurement control", None))
        self.progresslabel_4.setText(_translate("MainWindow", "Progress:", None))
        self.label_currentaltaz_3.setText(_translate("MainWindow", "Current horizontal", None))
        self.label_cur_az_5.setText(_translate("MainWindow", "Az:", None))
        self.cur_az.setText(_translate("MainWindow", "0", None))
        self.label_currentpointing_3.setText(_translate("MainWindow", "Calc. target horizontal", None))
        self.label_cur_alt_5.setText(_translate("MainWindow", "Alt:", None))
        self.calc_des_left.setText(_translate("MainWindow", "0", None))
        self.label_cur_alt_6.setText(_translate("MainWindow", "Alt:", None))
        self.cur_alt.setText(_translate("MainWindow", "0", None))
        self.label_cur_az_6.setText(_translate("MainWindow", "Az:", None))
        self.calc_des_right.setText(_translate("MainWindow", "0", None))
        self.IntegrationTimeLabel_2.setText(_translate("MainWindow", "Grid point integration time [s]", None))
        self.btn_observe.setText(_translate("MainWindow", "Measure", None))
        self.btn_abort.setText(_translate("MainWindow", "Abort measurement", None))
        self.btn_reset.setText(_translate("MainWindow", "Reset", None))
        self.infolabel.setText(_translate("MainWindow", "INFO: Your selected values imply a total observing time of X minutes plus slewing.", None))
        self.loop_grid_checkbox.setText(_translate("MainWindow", "Repeat (loop) grid measurements until abort is pressed", None))
        self.tabWidget_3.setTabText(self.tabWidget_3.indexOf(self.receiver_tab_basic_4), _translate("MainWindow", "Basic", None))
        self.label_mode_4.setText(_translate("MainWindow", "Mode", None))
        self.mode_signal.setText(_translate("MainWindow", "Signal", None))
        self.mode_switched.setText(_translate("MainWindow", "Switched", None))
        self.BandwidthLabel_4.setText(_translate("MainWindow", "Bandwidth [MHz]", None))
        self.ChannelsInput.setText(_translate("MainWindow", "256", None))
        self.BandwidthInput.setText(_translate("MainWindow", "2.5", None))
        self.ChannelsLabel_4.setText(_translate("MainWindow", "Channels [#]", None))
        self.RefFreqLabel_4.setText(_translate("MainWindow", "Reference freq. [MHz]", None))
        self.RefFreqInput.setText(_translate("MainWindow", "1422.9", None))
        self.FrequencyLabel_7.setText(_translate("MainWindow", "Frequency [MHz]", None))
        self.FrequencyInput.setText(_translate("MainWindow", "1410", None))
        self.vlsr_checkbox.setText(_translate("MainWindow", "Translate to VLSR frame", None))
        self.autoedit_bad_data_checkBox.setText(_translate("MainWindow", "Remove RFI", None))
        self.LNA_checkbox.setText(_translate("MainWindow", "LNA", None))
        self.noise_checkbox.setText(_translate("MainWindow", "Noise diode", None))
        self.label_gain_3.setText(_translate("MainWindow", "Gain factor", None))
        self.gain.setText(_translate("MainWindow", "930", None))
        self.cycle_checkbox.setText(_translate("MainWindow", "Manually specify cycle times", None))
        self.signal_time_label_5.setText(_translate("MainWindow", "Signal time [s]:", None))
        self.ref_time_label_5.setText(_translate("MainWindow", "Reference time [s]:", None))
        self.loops_label_5.setText(_translate("MainWindow", "Number of loops:", None))
        self.tabWidget_3.setTabText(self.tabWidget_3.indexOf(self.receiver_tab_advanced_4), _translate("MainWindow", "Advanced", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Observe", None))
        self.groupBox_plot.setTitle(_translate("MainWindow", "Total power plot", None))
        self.label.setText(_translate("MainWindow", "List of measurements [date-UT]", None))
        self.btn_fit.setText(_translate("MainWindow", "Fit and plot Gaussian", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Measurements", None))
