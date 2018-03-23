#!/usr/bin/env python3
import sys
from PyQt4 import QtGui
from SmbGuiWindow import MainWindow
from tasks_loop import DoTasks
import Gbl
import ADC
from PID_heater import PidHeater
import SMB_Cmd_handler as SmbCmds


def main():

    Gbl.cmdlist = SmbCmds.retrieve_smb_cmds_from_db()

    tlm = Gbl.telemetry

    """ Create DAC Objects"""
    heaters = [PidHeater(i, tlm) for i in range(1)]

    """ Create ADC Objects"""
    adcs = [ADC.ADC(i, tlm) for i in range(2)]

    # Get data, service PID etc.
    t2 = DoTasks(tlm, adcs)
    t2.start()

    app = QtGui.QApplication(sys.argv)
    main_window = MainWindow(adcs, heaters)
    main_window.show()
    app.exec_()
    t2.join()


if __name__ == "__main__":
    main()
