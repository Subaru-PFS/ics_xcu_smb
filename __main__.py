#!/usr/bin/env python3
import sys
from PyQt4 import QtGui
from SmbGuiWindow import MainWindow
from tasks_loop import DoTasks
from tcpip import TcpServer
import Gbl
import ADC
from heaters import PidHeater
import queue
from db import smb_db

def main():

    db = smb_db()
    qxmit = queue.Queue()
    qxmit.empty()
    qcmd = queue.Queue()
    qcmd.empty()

    tlm = Gbl.telemetry

    # Create DAC objects.
    heaters = [PidHeater(i, db, tlm) for i in range(1)]

    # Create ADC objects.
    adcs = [ADC.ADC(i, db, tlm) for i in range(2)]

    # Setup socket thread.
    t1 = TcpServer(qcmd, qxmit)
    t1.start()

    # Get data, service PID etc.
    t2 = DoTasks(tlm, adcs, heaters, qcmd, qxmit)
    t2.start()

    app = QtGui.QApplication(sys.argv)
    main_window = MainWindow(db, adcs, heaters, qcmd)
    main_window.show()
    app.exec_()

    t1.join()
    t2.join()
    qxmit.join()
    qcmd.join()


if __name__ == "__main__":
    main()
