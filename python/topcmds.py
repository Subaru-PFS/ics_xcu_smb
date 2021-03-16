import time
import Gbl

def resetDacs(bus='gpio', noConnect=False):
    """Fully reset DACs, using the single GPIO RESET-BAR signal. """

    Gbl.gpio.dac_reset()
    time.sleep(0.1)
    if not noConnect:
        for htr in Gbl.heaters:
            htr.connectDAC(bus=bus)
