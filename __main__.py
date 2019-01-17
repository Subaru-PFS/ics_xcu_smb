#!/usr/bin/env python3
import logging
import queue
import RPi.GPIO as GPIO
import spidev
import sys
import time
from PyQt5 import QtWidgets
import ADS1015
import GPIO_config
import Gbl
from AD7124 import AD7124 as ad7124
from BangBang import bang_bang as bb
from SmbGuiWindow import MainWindow
from heaters import PidHeater
from spi_bus import DacSpi
from tasks_loop import DoTasks
from tcpip import TcpServer
from PyQt5.QtSql import *


def main():
    logging.basicConfig(datefmt = "%Y-%m-%d %H:%M:%S",
                        format = "%(asctime)s.%(msecs)03dZ %(name)-10s %(levelno)s %(filename)s:%(lineno)d %(message)s")
    
    logger = logging.getLogger('smb')
    logger.setLevel(5)
    logger.info('starting logging!')
    
    smbdb = QSqlDatabase.addDatabase("QSQLITE")
    smbdb.setDatabaseName("smb.db")
    if not smbdb.open():
        result = QMessageBox.warning(None, 'Error', "Database Error: %s" % smbdb.lastError().text())
        print(result)
        sys.exit(1)

    # db = smb_db()
    qxmit = queue.Queue()
    qxmit.empty()
    qcmd = queue.Queue()
    qcmd.empty()

    tlm = Gbl.telemetry
    # create IO object
    io = GPIO_config.io()
    # reset both DACs
    io.dac_reset(0)
    time.sleep(.001)
    io.dac_reset(1)
    time.sleep(.001)

    io.dac_bank_sel(1)
    # create BUS Objects
    bus1 = DacSpi(0)
    bus2 = DacSpi(1)

    bus1.xfer([3, 0, 0x10])
    bus2.xfer([3, 0, 0x10])
    time.sleep(.002)

    # issue read command
    data1 = bus1.xfer([0x83, 0, 0x10])
    data2 = bus1.xfer([0, 0, 0])

    logger.debug('data1: %s', data1)
    logger.debug('data2: %s', data2)
    # issue read command
    data3 = bus2.xfer([0x83, 0, 0x10])
    data4 = bus2.xfer([0, 0, 0])

    logger.debug('data3: %s', data3)
    logger.debug('data4: %s', data4)

    # Create DAC objects.
    heaters = [PidHeater(i, smbdb, tlm) for i in range(2)]

    # Create SPI Bus object
    spi = spidev.SpiDev()  # create spi object
    spi_id = 0
    cs_id = 0
    spi.open(spi_id, cs_id)
    spi.max_speed_hz = 7000
    spi.mode = 3
    spi.cshigh = True

    # Create ADC objects.
    adcs = [ad7124(i, smbdb, tlm, spi) for i in range(12)]

    # Create ADS1015 object
    ads1015 = ADS1015.ADS1015(smbdb)

    # Create Bang-Bang heater objects
    bang_bangs = [bb(i) for i in range(2)]

    # Setup socket thread.
    t1 = TcpServer(smbdb, qcmd, qxmit)
    t1.start()

    # Get data, service PID etc.
    t2 = DoTasks(smbdb, tlm, bang_bangs, adcs, heaters, ads1015, qcmd, qxmit)
    t2.start()

    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow(smbdb, bang_bangs, adcs, heaters, ads1015, qcmd)
    main_window.show()
    app.exec_()

    t1.join()
    # t2.join()
    qxmit.join()
    qcmd.join()
    GPIO.cleanup()


if __name__ == "__main__":
    main()

# TODO: get t2 loop to place nice with the other tasks
