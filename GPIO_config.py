import RPi.GPIO as GPIO


class gpio(object):


    def __init__(self, ):
        """ SET GPIO numbering mode to use GPIO designation, NOT pin numbers """
        GPIO.setmode(GPIO.BCM)

        """
        @dictionary GPIO Pin Numbers
        @Maps DAC singals to GPIO PINS.
        """
        self.pin_map = {
            "SDA_0": 2,
            "SCL_0": 3,
            "GPIO4": 4,
            "nLDAC": 6,
            "nADC_CS1": 7,
            "nADC_CS0": 8,
            "SPI0_MISO": 9,
            "SPI0_MOSI": 10,
            "SPI0_SCLK": 11,
            "DAC_CLR": 12,
            "nALARM": 13,
            "GPIO16": 16,
            "nDAC_CS1": 17,
            "nDAC_CS0": 18,
            "SPI1_MOSI": 20,
            "SPI1_SCLK": 21,
            "GPIO22": 22,
            "GPIO23": 23,
            "GPIO24": 24,
            "GPIO25": 25,
            "nRESET": 26,
            "GPIO27": 27,
        }

        # spi1clk = self.pin_map['SPI1_SCLK']
        # GPIO.setup(spi1clk, GPIO.HIGH)  # SPI1-CS0
        # GPIO.output(spi1clk,1)

        # Set SPI1 DAC CS (SYNC) pin high.
        # cs0 = self.pin_map['nDAC_CS0']
        # GPIO.setup(cs0, GPIO.OUT)  # SPI1-CS0
        # GPIO.output(cs0, 1)

        # Set DAC /RESET to output.
        pin = self.pin_map['nRESET']
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, 1)  # put DAC in run mode

        # Set DAC /LDAC to output.
        pin = self.pin_map['nLDAC']
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, 1)

        # Set DAC CLR to output.
        pin = self.pin_map['DAC_CLR']
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, 0)

        # Set DAC /Alarm to input.
        pin = self.pin_map['nALARM']
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def dac_reset(self, state):
        pin = self.pin_map['nRESET']
        GPIO.output(pin, state)

    def dac_ldac(self, state):
        pin = self.pin_map['nLDAC']
        GPIO.output(pin, state)

    def dac_clr(self, state):
        pin = self.pin_map['DAC_CLR']
        GPIO.output(pin, state)
