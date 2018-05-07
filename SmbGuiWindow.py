import natsort
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
import Gbl
import SmbMainGui
import re
from SMB_Cmd_handler import SmbCmd
from db import config_table


class MainWindow(QtWidgets.QMainWindow, SmbMainGui.Ui_MainWindow):

    tlm = Gbl.telemetry

    def __init__(self, db,bang_bangs, adcs, heaters, qcommand):
        super(MainWindow, self).__init__()
        self.db = db
        self.htrs = heaters
        self.adcs = adcs
        self.bb = bang_bangs
        self.qcmd = qcommand
        self.setupUi(self)
        self.__gui_delegates()
        self._tablename = 'tblHtrParams'
        self.__read_loop1_settings()
        self.tabMain.setCurrentIndex(0)
        self._board_id=self.db.db_fetch_board_id()
        self.SpinBoardID.setValue(self._board_id)

        tblnames = self.db.db_fetch_tablenames()

        for i in range(len(tblnames)):
            line = re.sub('[!@#$,()\']', '', str(tblnames[i]))
            self.cboDatabaseTableNames.addItem(line)

    def __gui_delegates(self):
        self.btnReadAllTemps.released.connect(self.__read_adc_temps)
        self.btnReadAdcCounts.released.connect(self.__read_adc_counts)
        self.btnReadSenorVolts.released.connect(self.__read_sns_volts)
        self.btnReadSensorResistances.released.connect(self.__read_sns_ohms)
        self.btnReadHumidity.released.connect(self.__read_humidity)
        self.btnRadRefVolts.released.connect(self.__read_adc_ref_volts)
        self.btnReadAdcChipTemps.released.connect(self.__read_adc_chip_temps)
        self.btnReadLoop1Settings.released.connect(self.__read_loop1_settings)
        self.btnSetPterm1.released.connect(self.__set_pterm1)
        self.btnSetIterm1.released.connect(self.__set_i_term1)
        self.btnSetDterm1.released.connect(self.__set_d_term1)
        self.cboSelLoopSns1.currentIndexChanged.connect(self.__set_loop_sensor1)
        self.btnSetSp1.released.connect(self.__set_setpt1)
        self.btnSetHtrCurrent1.released.connect(self.__set_htr_current1)
        self.groupHtrCtl.buttonReleased.connect(self.__set_htr_mode1)
        self.cboDatabaseTableNames.currentIndexChanged.connect(self.__read_tabledata_from_db)
        self.btnSetFilterDataRate.released.connect(self.__adc_set_filter_rate)
        self.cboExciationCurrent.currentIndexChanged.connect(self.__adc_set_excitation_current)
        self.cboSelectAdcSincFilter.currentIndexChanged.connect(self.__adc_set_sync_filter)
        self.btnSetBoardID.released.connect(self.__set_board_ID)
        self.chkHighPowerOut1.stateChanged.connect(self.__set_hi_power_state1)
        self.chkHighPowerOut2.stateChanged.connect(self.__set_hi_power_state2)
        self.cboSelectSensorType.currentIndexChanged.connect(self.__adc_select_sensor)
        self.cboSelectTempUnit.currentIndexChanged.connect(self.__adc_select_temp_units)

    def __adc_select_temp_units(self):
        value = self.cboSelectTempUnit.currentIndex()
        i = 1
        for checkbox in self.grpAdcs.findChildren(QtWidgets.QCheckBox):
            if checkbox.isChecked() is True:
                self.adcs[i - 1].adc_set_temp_units(value)
            i += 1

    def __adc_select_sensor(self):
        value=self.cboSelectSensorType.currentIndex() + 1
        i = 1
        for checkbox in self.grpAdcs.findChildren(QtWidgets.QCheckBox):
            if checkbox.isChecked() is True:
                self.adcs[i - 1].adc_set_sensor_type(value)
            i += 1

    def __set_hi_power_state1(self):
        if self.chkHighPowerOut1.isChecked() == True:
            self.bb[0].power_on_output()
            print("BangBang 1 activated")
        else:
            self.bb[0].power_off_output()
            print("BangBang 1 deactivated")

    def __set_hi_power_state2(self):
        if self.chkHighPowerOut2.isChecked() == True:
            self.bb[1].power_on_output()
            print("BangBang 2 activated")
        else:
            self.bb[1].power_off_output()
            print("BangBang 2 deactivated")

    def __set_board_ID(self):
        board_id = self.SpinBoardID.value()
        self.db.db_update_board_id(board_id)


    def __adc_set_sync_filter(self):
        value = self.cboSelectAdcSincFilter.currentIndex()
        i = 1
        for checkbox in self.grpAdcs.findChildren(QtWidgets.QCheckBox):
            if checkbox.isChecked() is True:
                self.adcs[i - 1].set_filter_type(value)
            i += 1

    def __adc_set_excitation_current(self):
        value = self.cboExciationCurrent.currentIndex()
        i = 0
        for checkbox in self.grpAdcs.findChildren(QtWidgets.QCheckBox):
            if checkbox.isChecked() is True:
                self.adcs[i].set_exciatation_current(value)
            i += 1

    def __adc_set_filter_rate(self):
        i = 0
        for checkbox in self.grpAdcs.findChildren(QtWidgets.QCheckBox):
            if checkbox.isChecked() is True:
                self.adcs[i].adc_set_filter_rate(self.spinAdcFilterDataRate.value())
                i += 1


    def __read_tabledata_from_db(self):
        tblname = self.cboDatabaseTableNames.currentText()
        tabledata = self.db.db_fetch_table_data(tblname)
        tblheader = self.db.db_fetch_table_fields(tblname)
        self.table = config_table(self.tableView, tblheader, tabledata)

    @pyqtSlot(QtWidgets.QAbstractButton)
    def __set_htr_mode1(self, button_or_id):
        value=0
        if button_or_id.text() == 'Disabled':
            value=0
        elif button_or_id.text() == 'Current':
            value=1
        elif button_or_id.text() == 'PID':
            value = 2
        else:
            value=0

        self.htrs[0].set_htr_mode(value)

    def __set_htr_current1(self):
        value = self.SpinHtrCurrent1.value()
        self.txtDisplay.append("Expected Htr Voltage = {0:3.3f}V".format(value * 212.25))
        self.htrs[0].htr_set_heater_current(value)

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
