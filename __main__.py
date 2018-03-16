#!/usr/bin/env python3
import sys
import natsort
from PyQt4 import QtCore, QtGui
import SmbMainGui
from tasks_loop import DoTasks
import db
import Gbl
import ADC
from PID_heater import PidHeater
import RPi.GPIO as GPIO


def main():

    tlm = Gbl.telemetry

    """ Create DAC Objects"""
    heater = [PidHeater(i, tlm) for i in range(1)]

    """ Create ADC Objects"""
    adc = [ADC.ADC(i, tlm) for i in range(2)]

    # Get data, service PID etc.
    t2 = DoTasks(tlm, adc)
    t2.start()

    app = QtGui.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    app.exec_()
    t2.join()


class MainWindow(QtGui.QMainWindow, SmbMainGui.Ui_MainWindow):

    # q_cmds = Queue(maxsize=100)
    tlm = Gbl.telemetry
    # spi_bus.system_init(tlm)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.gui_delegates()
        db.populate_cmd_list()

    def gui_delegates(self):
        self.connect(self.btnReadAllTemps, QtCore.SIGNAL("released()"), self.__read_adc_temps)
        self.connect(self.btnReadAdcCounts, QtCore.SIGNAL("released()"), self.__read_adc_counts)
        self.connect(self.btnReadSenorVolts, QtCore.SIGNAL("released()"), self.__read_sns_volts)
        self.connect(self.btnReadSensorResistances, QtCore.SIGNAL("released()"), self.__read_sns_ohms)
        self.connect(self.btnReadHumidity, QtCore.SIGNAL("released()"), self.__read_humidity)
        self.connect(self.btnRadRefVolts, QtCore.SIGNAL("released()"), self.__read_adc_ref_volts)
        self.connect(self.btnReadAdcChipTemps, QtCore.SIGNAL("released()"), self.__read_adc_chip_temps)

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




if __name__ == "__main__":
    main()
