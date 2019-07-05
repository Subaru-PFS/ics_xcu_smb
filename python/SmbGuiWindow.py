import natsort
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
import Gbl
import SmbMainGui
import re
from quieres import config_table
import quieres

class MainWindow(QtWidgets.QMainWindow, SmbMainGui.Ui_MainWindow):

    tlm = Gbl.telemetry

    def __init__(self, db, bang_bangs, adcs, heaters, ads1015, qcommand):
        super(MainWindow, self).__init__()

        self.db = db
        self.ads1015 = ads1015
        self.htrs = heaters
        self.adcs = adcs
        self.bb = bang_bangs
        self.qcmd = qcommand
        self.setupUi(self)
        self.__gui_delegates()
        self._tablename = 'tblHtrParams'
        self.__read_loop1_settings()
        self.__read_loop2_settings()
        self.tabMain.setCurrentIndex(0)
        self._board_id = quieres.db_fetch_board_id(self.db)
        self.SpinBoardID.setValue(self._board_id)

        sshFile = "StyleSheet.css"
        with open(sshFile, "r") as fh:
            self.setStyleSheet(fh.read())

        tblnames = quieres.db_fetch_tablenames(self.db)
        adc_registers = quieres.db_fetch_table_data(self.db, 'tblAdcRegisters')
        for adc_register in adc_registers:
            self.cboAdcRegisters.addItem(adc_register[0])
        self.cboAdcRegisters.setCurrentIndex(1)
        dac_registers = quieres.db_fetch_table_data(self.db, 'tblDacRegisters')
        for dac_register in dac_registers:
            self.cboDacRegisters1.addItem(dac_register[0])
        for dac_register in dac_registers:
            self.cboDacRegisters2.addItem(dac_register[0])
        self.cboDacRegisters1.setCurrentIndex(11)
        self.cboDacRegisters2.setCurrentIndex(11)

        for i in range(len(tblnames)):
            line = re.sub('[!@#$,()\']', '', str(tblnames[i]))
            self.cboDatabaseTableNames.addItem(line)

    def __gui_delegates(self):
        self.btnReadAdcCountsFromChip.released.connect(self.__read_adc_counts_from_chip)
        self.btnReadAllTempsFromTlm.released.connect(self.__read_adc_temps_from_tlm)
        self.btnReadAdcCountsFromTlm.released.connect(self.__read_adc_counts_from_tlm)
        self.btnReadSenorVoltsFromTlm.released.connect(self.__read_sns_volts_from_tlm)
        self.btnReadSensorResistancesFromTlm.released.connect(self.__read_sns_ohms_from_tlm)
        self.btnReadHumidityFromTlm.released.connect(self.__read_humidity_from_tlm)
        self.btnRadRefVoltsFromTlm.released.connect(self.__read_adc_ref_volts_from_tlm)
        self.btnReadAdcChipTempsFromTlm.released.connect(self.__read_adc_chip_temps_from_tlm)
        self.btnReadLoop1Settings.released.connect(self.__read_loop1_settings)
        self.btnReadLoop2Settings.released.connect(self.__read_loop2_settings)
        self.btnSetPterm1.released.connect(self.__set_pterm1)
        self.btnSetIterm1.released.connect(self.__set_i_term1)
        self.btnSetDterm1.released.connect(self.__set_d_term1)
        self.cboSelLoopSns1.currentIndexChanged.connect(self.__set_loop_sensor1)
        self.btnSetSp1.released.connect(self.__set_setpt1)
        self.btnSetHtrCurrent1.released.connect(self.__set_htr_current1)
        self.btnSetHtrCurrent2.released.connect(self.__set_htr_current2)
        self.groupHtrCtl1.buttonReleased.connect(self.__set_htr_mode1)
        self.groupHtrCtl2.buttonReleased.connect(self.__set_htr_mode2)
        self.cboDatabaseTableNames.currentIndexChanged.connect(self.__read_tabledata_from_db)
        self.btnSetFilterDataRate.released.connect(self.__adc_set_filter_rate)
        self.btnSetExcitationCurrent.released.connect(self.__adc_set_excitation_current)
        self.btnSetSyncFilter.released.connect(self.__adc_set_sync_filter)
        self.btnSetBoardID.released.connect(self.__set_board_id)
        self.chkHighPowerOut1.stateChanged.connect(self.__set_hi_power_state1)
        self.chkHighPowerOut2.stateChanged.connect(self.__set_hi_power_state2)
        self.btnSetSensorType.released.connect(self.__adc_select_sensor)
        self.btnSetTempUnit.released.connect(self.__adc_select_temp_units)
        self.btnReadAdcRegister.released.connect(self.__adc_get_status)
        self.btnReadDacStatus1.released.connect(self.__dac_get_status1)
        self.btnReadDacStatus2.released.connect(self.__dac_get_status2)
        self.bthHighPowerOutStatus.released.connect(self.__read_ads1015_conversion)
        self.btnSetSenorWiring.released.connect(self.__set_sensor_wiring)
        self.btnSetPostFilter.released.connect(self.__adc_set_post_filter)

    def __read_ads1015_conversion(self):
        self.txtDisplay.clear()
        current = self.ads1015.ads1015_read_current_bb(1)
        self.txtDisplay.append("bb1 Current = " + str(current))
        current = self.ads1015.ads1015_read_current_bb(2)
        self.txtDisplay.append("bb2 Current = " + str(current))

        status = self.bb[0].bang_bang_status()
        if status is True:
            self.chkHighPowerOut1.setChecked(True)
        else:
            self.chkHighPowerOut1.setChecked(False)

        status = self.bb[1].bang_bang_status()
        if status is True:
            self.chkHighPowerOut2.setChecked(True)
        else:
            self.chkHighPowerOut2.setChecked(False)

    def __adc_get_status(self):
        self.txtDisplay.clear()
        tablename = self.cboAdcRegisters.currentText()
        adc_selected = self.cboSelAdc.currentIndex()
        status = self.adcs[adc_selected].adc_read_register_to_dict(tablename)

        for key, value in sorted(status.items()):
            self.txtDisplay.append(key + " " + str(value))

    def __dac_get_status1(self):
        self.txtDisplay.clear()
        tablename = self.cboDacRegisters1.currentText()
        status = self.htrs[0].dac.dac_read_register(tablename)
        for key, value in sorted(status.items()):
            self.txtDisplay.append(key + " " + str(value))

    def __dac_get_status2(self):
        self.txtDisplay.clear()
        tablename = self.cboDacRegisters2.currentText()
        status = self.htrs[1].dac.dac_read_register(tablename)
        for key, value in sorted(status.items()):
            self.txtDisplay.append(key + " " + str(value))

    def __set_sensor_wiring(self):
        value = self.cboSeletSenorWiring.currentIndex()
        for checkbox in self.grpAdcs.findChildren(QtWidgets.QCheckBox):
            if checkbox.isChecked() is True:
                name = checkbox.text()
                chbxid = int(re.search(r'\d+', name).group())
                self.adcs[chbxid - 1].adc_set_sensor_wiring(value)

    def __adc_select_temp_units(self):
        value = self.cboSelectTempUnit.currentIndex()
        for checkbox in self.grpAdcs.findChildren(QtWidgets.QCheckBox):
            if checkbox.isChecked() is True:
                name = checkbox.text()
                chbxid = int(re.search(r'\d+', name).group())
                self.adcs[chbxid - 1].adc_set_temp_units(value)

    def __adc_select_sensor(self):
        value = self.cboSelectSensorType.currentIndex() + 1
        for checkbox in self.grpAdcs.findChildren(QtWidgets.QCheckBox):
            if checkbox.isChecked() is True:
                name = checkbox.text()
                chbxid = int(re.search(r'\d+', name).group())
                self.adcs[chbxid - 1].adc_set_sensor_type(value)

    def __set_hi_power_state1(self):
        if self.chkHighPowerOut1.isChecked() is True:
            self.bb[0].power_on_output()
            print("BangBang 1 activated")
        else:
            self.bb[0].power_off_output()
            print("BangBang 1 deactivated")

    def __set_hi_power_state2(self):
        if self.chkHighPowerOut2.isChecked() is True:
            self.bb[1].power_on_output()
            print("BangBang 2 activated")
        else:
            self.bb[1].power_off_output()
            print("BangBang 2 deactivated")

    def __set_board_id(self):
        board_id = self.SpinBoardID.value()
        quieres.db_update_board_id(self.db, board_id)

    def __adc_set_post_filter(self):
        value = self.cboSelectAdcPostFilter.currentIndex()
        for checkbox in self.grpAdcs.findChildren(QtWidgets.QCheckBox):
            if checkbox.isChecked() is True:
                name = checkbox.text()
                chbxid = int(re.search(r'\d+', name).group())
                self.adcs[chbxid - 1].set_post_filter_type(value)

    def __adc_set_sync_filter(self):
        value = self.cboSelectAdcSincFilter.currentIndex()
        for checkbox in self.grpAdcs.findChildren(QtWidgets.QCheckBox):
            if checkbox.isChecked() is True:
                name = checkbox.text()
                chbxid = int(re.search(r'\d+', name).group())
                self.adcs[chbxid - 1].set_filter_type(value)

    def __adc_set_excitation_current(self):
        value = self.cboExciationCurrent.currentIndex()
        for checkbox in self.grpAdcs.findChildren(QtWidgets.QCheckBox):
            if checkbox.isChecked() is True:
                name = checkbox.text()
                chbxid = int(re.search(r'\d+', name).group())
                self.adcs[chbxid-1].set_exciatation_current(value)

    def __adc_set_filter_rate(self):
        for checkbox in self.grpAdcs.findChildren(QtWidgets.QCheckBox):
            if checkbox.isChecked() is True:
                name = checkbox.text()
                chbxid = int(re.search(r'\d+', name).group())
                self.adcs[chbxid-1].adc_set_filter_rate(self.spinAdcFilterDataRate.value())

    def __read_tabledata_from_db(self):
        tblname = self.cboDatabaseTableNames.currentText()
        tabledata = quieres.db_fetch_table_data(self.db, tblname)
        tblheader = quieres.db_fetch_table_fields(self.db, tblname)
        self.table = config_table(self.tableView, tblheader, tabledata)

    @pyqtSlot(QtWidgets.QAbstractButton)
    def __set_htr_mode1(self, button_or_id):
        if button_or_id.text() == 'Disabled':
            value = 0
        elif button_or_id.text() == 'Current':
            value = 1
        elif button_or_id.text() == 'PID':
            value = 2
        else:
            value = 0

        self.htrs[0].set_htr_mode(value)

    @pyqtSlot(QtWidgets.QAbstractButton)
    def __set_htr_mode2(self, button_or_id):
        if button_or_id.text() == 'Disabled':
            value = 0
        elif button_or_id.text() == 'Current':
            value = 1
        elif button_or_id.text() == 'PID':
            value = 2
        else:
            value = 0

        self.htrs[1].set_htr_mode(value)

    def __set_htr_current1(self):
        value = self.SpinHtrCurrent1.value()
        self.txtDisplay.append("Expected Htr Voltage = {0:3.3f}V".format(value * 219))
        self.htrs[0].htr_set_heater_current(value)

    def __set_htr_current2(self):
        value = self.SpinHtrCurrent2.value()
        self.txtDisplay.append("Expected Htr Voltage = {0:3.3f}V".format(value * 217))
        self.htrs[1].htr_set_heater_current(value)

    def __set_setpt1(self):
        value = self.SpinDblSetPoint1.value()
        self.htrs[0].heater_set_pt = value
        quieres.db_update_htr_params(self.db, value, 'set_pt', 1)

    def __set_loop_sensor1(self):
        value = self.cboSelLoopSns1.currentIndex() + 1
        self.htrs[0].heater_ctrl_sensor = value
        quieres.db_update_htr_params(self.db, value, 'ctrl_sensor', 1)

    def __set_pterm1(self):
        value = self.SpinDblPterm1.value()
        self.htrs[0].heater_p_term = value
        quieres.db_update_htr_params(self.db, value, 'P', 1)

    def __set_i_term1(self):
        value = self.SpinDblIterm1.value()
        self.htrs[0].heater_i_term = value
        quieres.db_update_htr_params(self.db, value, 'I', 1)

    def __set_d_term1(self):
        value = self.SpinDblDterm1.value()
        self.htrs[0].heater_d_term = value
        quieres.db_update_htr_params(self.db, value, 'D', 1)

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

    def __read_loop2_settings(self):
        self.SpinDblSetPoint2.setValue(self.htrs[1].heater_set_pt)
        self.SpinDblPterm2.setValue(self.htrs[1].heater_p_term)
        self.SpinDblIterm2.setValue(self.htrs[1].heater_i_term)
        self.SpinDblDterm2.setValue(self.htrs[1].heater_d_term)
        self.SpinHtrCurrent2.setValue(self.htrs[1].heater_current)
        self.cboSelLoopSns2.setCurrentIndex(self.htrs[1].heater_ctrl_sensor - 1)
        if self.htrs[1].heater_mode == 0:
            self.radDisabled2.setChecked(True)
        elif self.htrs[1].heater_mode == 1:
            self.radHtrCurrent2.setChecked(True)
        elif self.htrs[1].heater_mode == 2:
            self.radPid2.setChecked(True)
        else:
            self.radDisabled2.setChecked(True)

    def __read_adc_counts_from_chip(self):
        self.txtDisplay.clear()
        adc_selected = self.cboSelAdcTemp.currentIndex()
        self.adcs[adc_selected].read_conversion_data()
        self.txtDisplay.clear()

        for key, value in natsort.natsorted(self.tlm.items()):
            if key == 'adc_counts' + str(adc_selected + 1):
                buf = '{:s} = {:10.0f}'.format(key, value)
                self.txtDisplay.append(buf)
            if key == 'rtd' + str(adc_selected + 1):
                buf = '{:s} = {:3.3f}K'.format(key, value)
                self.txtDisplay.append(buf)
            if key == 'adc_int_temp' + str(adc_selected + 1):
                buf = '{:s} = {:3.3f}K'.format(key, value)
                self.txtDisplay.append(buf)
            if key == 'refin' + str(adc_selected + 1):
                buf = '{:s} = {:3.4f}V'.format(key, value)
                self.txtDisplay.append(buf)
            if key == 'adc_sns_volts' + str(adc_selected + 1):
                buf = '{:s} = {:3.6f}V'.format(key, value)
                self.txtDisplay.append(buf)
            if key == 'adc_ext_therm'+ str(adc_selected + 1):
                buf = '{:s} = {:3.3f}K'.format(key, value)
                self.txtDisplay.append(buf)
            if key == 'adc_ref_volt'+ str(adc_selected + 1):
                buf = '{:s} = {:3.1f}V'.format(key, value)
                self.txtDisplay.append(buf)
            if key == 'adc_vddio' + str(adc_selected + 1):
                buf = '{:s} = {:3.1f}V'.format(key, value)
                self.txtDisplay.append(buf)


    def __read_adc_temps_from_tlm(self):
        self.txtDisplay.clear()
        for key, value in natsort.natsorted(self.tlm.items()):
            if 'rtd' in key:
                buf = '{:s} = {:3.3f}K'.format(key, value)
                self.txtDisplay.append(buf)

    def __read_adc_chip_temps_from_tlm(self):
        self.txtDisplay.clear()
        for key, value in natsort.natsorted(self.tlm.items()):
            if 'adc_int_temp' in key:
                buf = '{:s} = {:3.3f}K'.format(key, value)
                self.txtDisplay.append(buf)

    def __read_adc_ref_volts_from_tlm(self):
        self.txtDisplay.clear()
        for key, value in natsort.natsorted(self.tlm.items()):
            if 'adc_ref_volt' in key:
                buf = '{:s} = {:3.4f}V'.format(key, value)
                self.txtDisplay.append(buf)

    def __read_adc_counts_from_tlm(self):
        self.txtDisplay.clear()
        for key, value in natsort.natsorted(self.tlm.items()):
            if 'adc_counts' in key:
                buf = '{:s} = {:10.0f}'.format(key, value)
                self.txtDisplay.append(buf)

    def __read_sns_volts_from_tlm(self):
        self.txtDisplay.clear()
        for key, value in natsort.natsorted(self.tlm.items()):
            if 'adc_sns_volts' in key:
                buf = '{:s} = {:3.6f}V'.format(key, value)
                self.txtDisplay.append(buf)

    def __read_sns_ohms_from_tlm(self):
        self.txtDisplay.clear()
        for key, value in natsort.natsorted(self.tlm.items()):
            if 'adc_sns_ohms' in key:
                buf = '{:s} = {:3.3f}ohms'.format(key, value)
                self.txtDisplay.append(buf)

    def __read_humidity_from_tlm(self):
        self.txtDisplay.clear()
        for key, value in natsort.natsorted(self.tlm.items()):
            if 'humidity' in key:
                buf = '{:s} = {:3.1f}%'.format(key, value)
                self.txtDisplay.append(buf)
