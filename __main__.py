""" Main DMB Module """
import spidev
import sys
import ADC
import GUI
import Gbl
import SMB_Cmd_handler
import tcpip
import multiprocessing
import logging
import db
import threading
from queue import Queue

""" Serial Periphreal Interface """
Gbl.spi0 = spidev.SpiDev()


def spi_init():
    """Initialize the spi bus """
    exit_code = Gbl.spi0.open(0, 0)
    print(exit_code)
    Gbl.spi0.max_speed_hz = 122000
    Gbl.spi0.mode = 0b11
    Gbl.spi0.bits_per_word = 8
    Gbl.spi0.threewire = False
    Gbl.cmd_queue=Queue()


def system_init():
    """ init system """

    spi_init()
    objs = [ADC.ADC(i) for i in range(1)]
    for obj in objs:
        Gbl.adc.append(obj)


def main(args=None):
    """The main routine."""
    if args is None:
        args = sys.argv[1:]

    con=db.create_connection('smb.db')
    db.PopulateCmdList(con)

    system_init()
    # Gbl.app = GUI.QApplication(sys.argv)
    # ex = GUI.App()
    # sys.exit(Gbl.app.exec_())

    logging.basicConfig(level=logging.DEBUG)
    #server = tcpip.Server("10.0.0.4", 1024)

    threads = []
    t=threading.Thread(target=tcpip.ThreadedSocketServer.listenToClient())
    threads.append(t)
    t.start()


if __name__ == "__main__":
    main()