#!/usr/bin/env python3
import sys
from PyQt4 import QtGui

import db
from SmbGuiWindow import MainWindow
from tasks_loop import DoTasks
from tcpip import TcpServer
import Gbl
import ADC
from heaters import PidHeater
import queue
# from tcpip import ThreadedSocketServer

def main():

    qxmit = queue.Queue()
    qxmit.empty()
    qcmd = queue.Queue()
    qcmd.empty()

    Gbl.cmdlist = db.db_table_data_to_dictionary('tblSmbCmds')

    tlm = Gbl.telemetry

    """ Create DAC Objects"""
    heaters = [PidHeater(i, tlm) for i in range(1)]

    """ Create ADC Objects"""
    adcs = [ADC.ADC(i, tlm) for i in range(2)]

    # Setup Socket Thread
    t1 = TcpServer(qcmd, qxmit)
    t1.start()


    # Get data, service PID etc.
    t2 = DoTasks(tlm, adcs, heaters, qcmd, qxmit)
    t2.start()

    app = QtGui.QApplication(sys.argv)
    main_window = MainWindow(adcs, heaters, qcmd)
    main_window.show()
    app.exec_()
    t2.join()


if __name__ == "__main__":
    main()
