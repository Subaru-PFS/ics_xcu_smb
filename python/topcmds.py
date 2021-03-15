import Gbl

def resetDacs(bus='gpio'):
    """Fully reset DACs, using the single GPIO RESET-BAR signal. """

    Gbl.gpio.dac_reset()
    for htr in Gbl.heaters:
        htr.connectDAC(bus=bus)

