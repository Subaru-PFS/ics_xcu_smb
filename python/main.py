#!/usr/bin/env python3
import logging
import queue
import sys
import time

import spidev

import ADS1015
import GPIO_config
import Gbl
from AD7124 import AD7124 as ad7124
from BangBang import bang_bang as bb
from SmbGuiWindow import MainWindow
import heaterDacs
import heaters
import cmd_loop
from sensor_loop import SensorThread
from tcpip import TcpServer
import topcmds

from PyQt5 import QtWidgets
import PyQt5.QtSql as qtSql

def runSmb(dbPath=None, logLevel=logging.INFO, dbLogLevel=logging.WARN,
           sensorPeriod=1, doGUI=True):
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
                        format = "%(asctime)s.%(msecs)03dZ %(name)-10s %(levelno)s %(filename)s:%(lineno)d %(message)s",
                        level=logging.DEBUG)
    
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

    logging.getLogger('db').setLevel(dbLogLevel)
    
    # db = smb_db()
    qxmit = queue.Queue()
    qxmit.empty()
    qcmd = queue.Queue()
    qcmd.empty()

    tlm = Gbl.telemetry

    # create GPIO object
    Gbl.gpio = gpio = GPIO_config.Gpio()

    # Create DAC objects.
    dacs = heaterDacs.HeaterDacs(gpio)
    Gbl.heaters = [heaters.PidHeater(i, smbdb, dacs) for i in range(2)]

    # Create SPI Bus object
    Gbl.spi = spi = spidev.SpiDev()  # create spi object
    spi_id = 0
    cs_id = 0
    spi.open(spi_id, cs_id)
    spi.max_speed_hz = 2000000
    spi.mode = 3
    spi.cshigh = True

    # Create ADC objects.
    Gbl.adcs = adcs = [ad7124(i, smbdb, tlm, spi, gpio) for i in range(12)]

    # Create ADS1015 object
    ads1015 = ADS1015.ADS1015(smbdb)

    # Create Bang-Bang heater objects
    bang_bangs = [bb(i, gpio) for i in range(2)]

    # Get data, service PID etc.
    # Once this is started, all access to io resources (GPIO, I2C, SPI) must use Gbl.ioLock
    #
    sensorThread = SensorThread(smbdb, tlm, bang_bangs, adcs, Gbl.heaters, ads1015,
                                sensorPeriod=sensorPeriod)
    sensorThread.start()

    # Setup socket thread. Must be merged with the cmdThread
    t1 = TcpServer(smbdb, qcmd, qxmit)
    t1.start()

    cmdThread = cmd_loop.CmdLoop(smbdb, tlm, bang_bangs, adcs, Gbl.heaters, ads1015,
                                 qcmd, qxmit)
    cmdThread.start()

    if doGUI:
        app = QtWidgets.QApplication(sys.argv)
        main_window = MainWindow(smbdb, bang_bangs, adcs, Gbl.heaters, ads1015, qcmd)
        main_window.show()

        app.exec_()
    else:
        # If we are the real main thread, because there is no GUI,
        # sleep forever, or at least until something like a ctrl-c
        # hits us.
        import select

        try:
            select.select([],[],[],None)
        except (KeyboardInterrupt, Exception) as e:
            logger.warning('exiting main program due to: %s', e)

    cmdThread.pleaseExit()
    cmdThread.join()

    sensorThread.pleaseExit()
    sensorThread.join()

    # There is an atexit handler to reset the GPIO configuration.
    
    
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
    parser.add_argument('--dbLogLevel', type=int, default=logging.WARN)
    parser.add_argument('--doGUI', action='store_true',
                        help='do not start X GUI')
    parser.add_argument('--sensorPeriod', type=float, default=1.0,
                        help='how often to sample the sensors')

    opts = parser.parse_args(argv)
    runSmb(dbPath=opts.dbPath, logLevel=opts.logLevel,
           dbLogLevel=opts.dbLogLevel,
           sensorPeriod=opts.sensorPeriod,
           doGUI=(opts.doGUI))
    
if __name__ == "__main__":
    main()

