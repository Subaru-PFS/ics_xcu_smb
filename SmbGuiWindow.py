import natsort
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSlot
import Gbl
import SmbMainGui
import sqlite3
import db


class MainWindow(QtGui.QMainWindow, SmbMainGui.Ui_MainWindow):

    # q_cmds = Queue(maxsize=100)
    tlm = Gbl.telemetry
    # spi_bus.system_init(tlm)

    def __init__(self, adcs, heaters):
        super(MainWindow, self).__init__()
        self.htrs = heaters
        self.adcs = adcs
        self.setupUi(self)
        self.__gui_delegates()
        self._tablename = 'tblHtrParams'
        self.__read_loop1_settings()
        db.populate_cmd_list()

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
        self.connect(self.btnSetHtrPwrPercent1, QtCore.SIGNAL("released()"), self.__set_htr_percent1)
        self.connect(self.groupHtrCtl, QtCore.SIGNAL("buttonReleased(QAbstractButton *)"), self.__set_htr_mode)
        # self.connect(self.groupHtrCtl, QtCore.SIGNAL("buttonReleased(int)"), self.__set_htr_mode)
        # button_clicked slot

    @pyqtSlot(QtGui.QAbstractButton)
    def __set_htr_mode(self, button_or_id):
        if button_or_id.text() == 'Disabled':
            value = 0
        elif button_or_id.text() == 'Percent':
            value = 1
        elif button_or_id.text() == 'PID':
            value = 2
        else:
            value = 0
        self.htrs[0].heater_mode = value
        self.__update_htr_db_param(value, 'mode')

    def __set_htr_percent1(self):
        value = self.SpinHtrPwrPercent1.value()
        self.htrs[0].heater_percent = value
        self.__update_htr_db_param(value, 'percent')

    def __set_setpt1(self):
        value = self.SpinDblSetPoint1.value()
        self.htrs[0].heater_set_pt = value
        self.__update_htr_db_param(value, 'set_pt')

    def __set_loop_sensor1(self):
        value = self.cboSelLoopSns1.currentIndex() + 1
        self.htrs[0].heater_ctrl_sensor = value
        self.__update_htr_db_param(value, 'ctrl_sensor')

    def __set_pterm1(self):
        value = self.SpinDblPterm1.value()
        self.htrs[0].heater_p_term = value
        self.__update_htr_db_param(value, 'P')

    def __set_i_term1(self):
        value = self.SpinDblIterm1.value()
        self.htrs[0].heater_i_term = value
        self.__update_htr_db_param(value, 'I')

    def __set_d_term1(self):
        value = self.SpinDblDterm1.value()
        self.htrs[0].heater_d_term = value
        self.__update_htr_db_param(value, 'D')

    def __update_htr_db_param(self, value, name):
        con = sqlite3.connect("smb.db")
        cur = con.cursor()
        qrytxt = "UPDATE {tn} SET {n} = {v}  WHERE PK_HTR_ID = 1". \
            format(tn=self._tablename, n=name, v=value)
        cur.execute(qrytxt)
        con.commit()
        con.close()

    def __read_loop1_settings(self):
        self.SpinDblSetPoint1.setValue(self.htrs[0].heater_set_pt)
        self.SpinDblPterm1.setValue(self.htrs[0].heater_p_term)
        self.SpinDblIterm1.setValue(self.htrs[0].heater_i_term)
        self.SpinDblDterm1.setValue(self.htrs[0].heater_d_term)
        self.SpinHtrPwrPercent1.setValue(self.htrs[0].heater_percent)
        self.cboSelLoopSns1.setCurrentIndex(self.htrs[0].heater_ctrl_sensor - 1)
        if self.htrs[0].heater_mode == 0:
            self.radDisabled1.setChecked(True)
        elif self.htrs[0].heater_mode == 1:
            self.radPercent1.setChecked(True)
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
