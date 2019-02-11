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
import cmd_loop
from sensor_loop import SensorThread
from tcpip import TcpServer
import PyQt5.QtSql as qtSql


def runSmb(dbPath=None, logLevel=logging.INFO, sensorPeriod=1, doGUI=True):
    """Start the SMB program

    Args
    ----
    dbPath : str
      The path to the configuration database.
    logLevel : int
      the logging threshold, per standard ``logging`` levels
    sensorPeriod = number
      how often to run the sensor loop;.
    doGUI : bool
      whether to load the GUI windows.
    
    """
    
    logging.basicConfig(datefmt = "%Y-%m-%d %H:%M:%S",
                        format = "%(asctime)s.%(msecs)03dZ %(name)-10s %(levelno)s %(filename)s:%(lineno)d %(message)s")
    
    logger = logging.getLogger('smb')
    logger.setLevel(logLevel)
    logger.info('starting logging!')

    if dbPath is None:
        dbPath = '/db/smb.db'
    smbdb = qtSql.QSqlDatabase.addDatabase("QSQLITE")
    smbdb.setDatabaseName(dbPath)
    if not smbdb.open():
        logger.critical("Error opening database %s: %s" % (dbPath, smbdb.lastError().text()))
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

    # Get data, service PID etc.
    sensorThread = SensorThread(smbdb, tlm, bang_bangs, adcs, heaters, ads1015,
                                sensorPeriod=sensorPeriod)
    sensorThread.start()

    # Setup socket thread. Must be merged with the cmdThread
    t1 = TcpServer(smbdb, qcmd, qxmit)
    t1.start()

    # Start command handler. This is slightly tricky: if we have a
    # GUI, that is the main thread and the command thread is run in
    # the background (daemon=True). If there is no GUI, the commadn
    # thread becomes the "main thread" (daemon=False). Daemon-ness
    # must be set before the thread is .start()ed.
    # 
    cmdThread = cmd_loop.CmdLoop(smbdb, tlm, bang_bangs, adcs, heaters, ads1015,
                                 qcmd, qxmit, isMainThread=(not doGUI))
    cmdThread.start()

    if doGUI:
        app = QtWidgets.QApplication(sys.argv)
        main_window = MainWindow(smbdb, bang_bangs, adcs, heaters, ads1015, qcmd)
        main_window.show()

        app.exec_()

    cmdThread.join()
    GPIO.cleanup()

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if isinstance(argv, str):
        import shlex
        argv = shlex.split(argv)

    import argparse

    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument('--dbPath', default=None,
                        help='path to configuration sqlite file.')
    parser.add_argument('--logLevel', type=int, default=logging.INFO,
                        help='logging threshold. 10=debug, 20=info, 30=warn')
    parser.add_argument('--noGUI', action='store_true',
                        help='do not start X GUI')
    parser.add_argument('--sensorPeriod', type=float, default=1.0,
                        help='how often to sample the sensors')

    opts = parser.parse_args(argv)
    runSmb(dbPath=opts.dbPath, logLevel=opts.logLevel,
           sensorPeriod=opts.sensorPeriod,
           doGUI=(not opts.noGUI))
    
if __name__ == "__main__":
    main()

# TODO: get t2 loop to place nice with the other tasks
