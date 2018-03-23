import spidev


class RPi3Spi(spidev.SpiDev):

    def __init__(self, spi_id, cs_id, mode=3, max_speed_hz = 97600, parent=None):
        super().__init__(spi_id, cs_id)
        self.spi_id = spi_id
        self.cs_id = cs_id
        self.mode = mode
        self.max_speed_hz = max_speed_hz
        self.open(self.spi_id, self.cs_id)
        self.spi_initialize()

    def spi_initialize(self):
        self.no_cs = False
        self.bits_per_word = 8
        self.threewire = False
        self.loop = False
        self.lsbfirst = False

        """Notes on spidev
        Unless the spi.max_speed_hz field is a value accepted by the driver, the script will fail when you run it.
        The field can be set to these values on the raspberry pi:

        SPEED	SPI.MAX_SPEED_HZ VALUE
        125.0 MHz	125000000
        62.5 MHz	62500000
        31.2 MHz	31200000
        15.6 MHz	15600000
        7.8 MHz	    7800000
        3.9 MHz	    3900000
        1953 kHz	1953000
        976 kHz	    976000
        488 kHz	    488000
        244 kHz	    244000
        122 kHz	    122000
        61 kHz	    61000
        30.5 kHz	30500
        15.2 kHz	15200
        7629 Hz	7629"""

    def spi_close(self):
        self.close()

    def __delete__(self, instance):
        self.close()
