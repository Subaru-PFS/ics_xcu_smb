#!/usr/bin/env python3
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from SmbGuiWindow import MainWindow
from tasks_loop import DoTasks
from tcpip import TcpServer
import Gbl
import ADC
from BangBang import bang_bang as bb
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

    # Create Bang-Bang heater objects
    bang_bangs = [bb(i) for i in range(2)]

    # Setup socket thread.
    t1 = TcpServer(db, qcmd, qxmit)
    t1.start()

    # Get data, service PID etc.
    t2 = DoTasks(db, tlm, bang_bangs, adcs, heaters, qcmd, qxmit)
    t2.start()

    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow(db, bang_bangs, adcs, heaters, qcmd)
    main_window.show()
    app.exec_()

    t1.join()
    t2.join()
    qxmit.join()
    qcmd.join()


if __name__ == "__main__":
    main()
