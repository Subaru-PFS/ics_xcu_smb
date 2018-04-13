import natsort
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSlot
import Gbl
import SmbMainGui
import re
from SMB_Cmd_handler import SmbCmd
from db import config_table

class MainWindow(QtGui.QMainWindow, SmbMainGui.Ui_MainWindow):

    tlm = Gbl.telemetry

    def __init__(self, db, adcs, heaters, qcommand):
        super(MainWindow, self).__init__()
        self.db = db
        self.htrs = heaters
        self.adcs = adcs
        self.qcmd = qcommand
        self.setupUi(self)
        self.__gui_delegates()
        self._tablename = 'tblHtrParams'
        self.__read_loop1_settings()
        self.tabMain.setCurrentIndex(0)



        tblnames = self.db.db_fetch_tablenames()

        for i in range(len(tblnames)):
            line = re.sub('[!@#$,()\']', '', str(tblnames[i]))
            self.cboDatabaseTableNames.addItem(line)

    def __gui_delegates(self):
        self.connect(self.btnReadAllTemps, QtCore.SIGNAL("released()"), self.__read_adc_temps)
        self.connect(self.btnReadAdcCounts, QtCore.SIGNAL("released()"), self.__read_adc_counts)
        self.connect(self.btnReadSenorVolts, QtCore.SIGNAL("released()"), self.__read_sns_volts)
        self.connect(self.btnReadSensorResistances, QtCore.SIGNAL("released()"), self.__read_sns_ohms)
        self.connect(self.btnReadHumidity, QtCore.SIGNAL("released()"), self.__read_humidity)
        self.connect(self.btnRadRefVolts, QtCore.SIGNAL("released()"), self.__read_adc_ref_volts)
        self.connect(self.btnReadAdcChipTemps, QtCore.SIGNAL("released()"), self.__read_adc_chip_temps)
        self.connect(self.btnReadLoop1Settings, QtCore.SIGNAL("released()"), self.__read_loop1_settings)
        self.connect(self.btnSetPterm1, QtCore.SIGNAL("released()"), self.__set_pterm1)
        self.connect(self.btnSetIterm1, QtCore.SIGNAL("released()"), self.__set_i_term1)
        self.connect(self.btnSetDterm1, QtCore.SIGNAL("released()"), self.__set_d_term1)
        self.connect(self.cboSelLoopSns1, QtCore.SIGNAL("activated(int)"), self.__set_loop_sensor1)
        self.connect(self.btnSetSp1, QtCore.SIGNAL("released()"), self.__set_setpt1)
        self.connect(self.btnSetHtrCurrent1, QtCore.SIGNAL("released()"), self.__set_htr_current1)
        self.connect(self.groupHtrCtl, QtCore.SIGNAL("buttonReleased(QAbstractButton *)"), self.__set_htr_mode1)
        self.connect(self.cboDatabaseTableNames, QtCore.SIGNAL("activated(int)"), self.__read_tabledata_from_db)
        # self.connect(self.spinAdcFilterDataRate, QtCore.SIGNAL("valueChanged(int)"), self.__adc_set_filter_rate)
        self.connect(self.btnSetFilterDataRate, QtCore.SIGNAL("released()"), self.__adc_set_filter_rate)
        self.connect(self.cboExciationCurrent, QtCore.SIGNAL("activated(int)"), self.__adc_set_excitation_current)
        self.connect(self.cboSelectAdcSincFilter, QtCore.SIGNAL("activated(int)"), self.__adc_set_sync_filter)

    def __adc_set_sync_filter(self):
        value=self.cboSelectAdcSincFilter()
        i=1
        for checkbox in self.grpAdcs.findChildren(QtGui.QCheckBox):
            if checkbox.isChecked() is True:
                cmdtxt = '~Q, {adc}, {v}'.format(adc=i, v=value)
                self.__enqueue_cmd(cmdtxt)
            i += 1

    def __adc_set_excitation_current(self):
        value = self.cboExciationCurrent.currentIndex()

        i = 1
        for checkbox in self.grpAdcs.findChildren(QtGui.QCheckBox):
            if checkbox.isChecked() is True:
                # self.adcs[i].adc_set_exciatiation_current(value)
                cmdtxt = '~X, {adc}, {v}'.format(adc=i, v=value)
                # print(cmdtxt)
                self.__enqueue_cmd(cmdtxt)
            i += 1


    def __adc_set_filter_rate(self):
        i=0
        for checkbox in self.grpAdcs.findChildren(QtGui.QCheckBox):
            if checkbox.isChecked() is True:
                self.adcs[i].adc_set_filter_rate(self.spinAdcFilterDataRate.value())
                i += 1
                # self.__enqueue_cmd()

        pass

    def __read_tabledata_from_db(self):
        tblname = self.cboDatabaseTableNames.currentText()
        tabledata =  self.db.db_fetch_table_data(tblname)
        tblheader = self.db.db_fetch_table_fields(tblname)
        self.table = config_table(self.tableView, tblheader, tabledata)

    @pyqtSlot(QtGui.QAbstractButton)
    def __set_htr_mode1(self, button_or_id):
        if button_or_id.text() == 'Disabled':
            value = 0
            self.__enqueue_cmd("~L,1,0")

        elif button_or_id.text() == 'Current':
            value = 1
            # Queue set mode Current command (L).
            self.__enqueue_cmd("~L,1,1")

        elif button_or_id.text() == 'PID':
            value = 2
            # Queue set mode PID command (L).
            self.__enqueue_cmd("~L,1,2")
        else:
            value = 0
        self.htrs[0].heater_mode = value
        self.db.db_update_htr_params(value, 'mode', 1)

    def __set_htr_current1(self):
        value = self.SpinHtrCurrent1.value()
        self.htrs[0].heater_current = value
        self.txtDisplay.append("Expected Htr Voltage = {0:3.3f}V".format(value * 212.25))
        self.db.db_update_htr_params(value, 'htr_current', 1)
        self.__enqueue_cmd("~V,1," + str(value))

    def __enqueue_cmd(self, strdata):
        smb_cmd = SmbCmd(self.db)
        cmd_dict = smb_cmd.parse_smb_cmd(strdata)
        if not self.qcmd.full():
            self.txtDisplay.append(strdata)
            self.qcmd.put(cmd_dict)

    def __set_setpt1(self):
        value = self.SpinDblSetPoint1.value()
        self.htrs[0].heater_set_pt = value
        self.db.db_update_htr_params(value, 'set_pt', 1)

    def __set_loop_sensor1(self):
        value = self.cboSelLoopSns1.currentIndex() + 1
        self.htrs[0].heater_ctrl_sensor = value
        self.db.db_update_htr_params(value, 'ctrl_sensor', 1)

    def __set_pterm1(self):
        value = self.SpinDblPterm1.value()
        self.htrs[0].heater_p_term = value
        self.db.db_update_htr_params(value, 'P', 1)

    def __set_i_term1(self):
        value = self.SpinDblIterm1.value()
        self.htrs[0].heater_i_term = value
        self.db.db_update_htr_params(value, 'I', 1)

    def __set_d_term1(self):
        value = self.SpinDblDterm1.value()
        self.htrs[0].heater_d_term = value
        self.db.db_update_htr_params(value, 'D', 1)

    def __read_loop1_settings(self):
        self.SpinDblSetPoint1.setValue(self.htrs[0].heater_set_pt)
        self.SpinDblPterm1.setValue(self.htrs[0].heater_p_term)
        self.SpinDblIterm1.setValue(self.htrs[0].heater_i_term)
        self.SpinDblDterm1.setValue(self.htrs[0].heater_d_term)
        self.SpinHtrCurrent1.setValue(self.htrs[0].heater_current)
        self.cboSelLoopSns1.setCurrentIndex(self.htrs[0].heater_ctrl_sensor - 1)
        if self.htrs[0].heater_mode == 0:
            self.radDisabled1.setChecked(True)
        elif self.htrs[0].heater_mode == 1:
            self.radHtrCurrent1.setChecked(True)
        elif self.htrs[0].heater_mode == 2:
            self.radPid1.setChecked(True)
        else:
            self.radDisabled1.setChecked(True)

    def __read_adc_temps(self):
        self.txtDisplay.clear()
        for key, value in natsort.natsorted(self.tlm.items()):
            if 'rtd' in key:
                buf = '{:s} = {:3.3f}K'.format(key, value)
                self.txtDisplay.append(buf)

    def __read_adc_chip_temps(self):
        self.txtDisplay.clear()
        for key, value in natsort.natsorted(self.tlm.items()):
            if 'adc_int_temp' in key:
                buf = '{:s} = {:3.3f}K'.format(key, value)
                self.txtDisplay.append(buf)

    def __read_adc_ref_volts(self):
        self.txtDisplay.clear()
        for key, value in natsort.natsorted(self.tlm.items()):
            if 'adc_ref_volt' in key:
                buf = '{:s} = {:3.4f}V'.format(key, value)
                self.txtDisplay.append(buf)

    def __read_adc_counts(self):
        self.txtDisplay.clear()
        for key, value in natsort.natsorted(self.tlm.items()):
            if 'adc_counts' in key:
                buf = '{:s} = {:10.0f}'.format(key, value)
                self.txtDisplay.append(buf)

    def __read_sns_volts(self):
        self.txtDisplay.clear()
        for key, value in natsort.natsorted(self.tlm.items()):
            if 'adc_sns_volts' in key:
                buf = '{:s} = {:3.6f}V'.format(key, value)
                self.txtDisplay.append(buf)

    def __read_sns_ohms(self):
        self.txtDisplay.clear()
        for key, value in natsort.natsorted(self.tlm.items()):
            if 'adc_sns_ohms' in key:
                buf = '{:s} = {:3.3f}ohms'.format(key, value)
                self.txtDisplay.append(buf)

    def __read_humidity(self):
        self.txtDisplay.clear()
        for key, value in natsort.natsorted(self.tlm.items()):
            if 'humidity' in key:
                buf = '{:s} = {:3.1f}%'.format(key, value)
                self.txtDisplay.append(buf)
