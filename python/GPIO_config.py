import atexit
import logging
import signal

import RPi.GPIO as GPIO

import Gbl

# One reason for using this module is to register cleanup routines
# which deallocate the GPIO resources. Nice to do: avoids noisy complaints 
# and allocation failures. 
#
def sigCleanup(signum, frame):
    logging.warn("caught signal %s", signum)
    raise SystemExit()
    
def cleanup():
    try:
        GPIO.cleanup()
    except RuntimeWarning:
        return
    
    logging.warn('reset GPIO configuration on exit.')
    
class Gpio(object):
    def __init__(self):
        """
        @dictionary GPIO Pin Numbers
        @Maps DAC singals to GPIO PINS.
        """
        self.pin_map = {
            "SDA_0": 2,
            "SCL_0": 3,
            "HI_PWR_EN1": 5,
            "HI_PWR_EN2": 6,
            "nADC_CS1": 7,
            "nADC_CS0": 24,
            "SPI0_MISO": 9,
            "SPI0_MOSI": 10,
            "SPI0_SCLK": 11,
            "nADC_BANK1_SEL": 16,
            "nADC_BANK3_SEL": 22,
            "GPIO24": 24,
            "nADC_SYNC": 26,
            "nADC_BANK2_SEL": 27,

            # DACs
            "nDAC_ALARM": 4,
            "nDAC_RESET": 12,
            "nLDAC": 13,
            "nDAC_CS0": 18,
            "SPI1_MISO": 19,
            "SPI1_MOSI": 20,
            "SPI1_SCLK": 21,
            "DAC_CLR": 23,
            "nDAC_BANK_SEL": 25,

        }

        atexit.register(cleanup)
        signal.signal(signal.SIGTERM, sigCleanup)

        self.configureGpio()

    def output(self, pin, state):
        """Direct access to GPIO.output(). """
        state = bool(state)
        GPIO.output(pin, state)

    def input(self, pin):
        """Direct access to GPIO.input(). """
        return GPIO.input(pin)

    def configureGpio(self):
        with Gbl.ioLock:
            """ SET GPIO numbering mode to use GPIO designation, NOT pin numbers """
            GPIO.setmode(GPIO.BCM)

            # Set /ADC_SC0 to output.
            pin = self.pin_map['nADC_CS0']
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 1)

            # Set /ADC SC1 to output.
            pin = self.pin_map['nADC_CS1']
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 1)

            # Set nADC_BANK1_SEL to output
            pin = self.pin_map['nADC_BANK1_SEL']
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 1)  # disable

            # Set nADC_BANK2_SEL to output
            pin = self.pin_map['nADC_BANK2_SEL']
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 1)  # disable

            # Set nADC_BANK3_SEL to output
            pin = self.pin_map['nADC_BANK3_SEL']
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 1)  # disable

            # Set SPI1_SCLK to output.
            pin = self.pin_map['SPI1_SCLK']
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 1)  # idle high

            # Set SPI1_MOSI to output.
            pin = self.pin_map['SPI1_MOSI']
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)  # normally low

            # Set SPI1_MISO to input.
            pin = self.pin_map['SPI1_MISO']
            # GPIO.setup(pin, GPIO.IN)
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # Set /DAC_BANK_SEL to output.
            pin = self.pin_map['nDAC_BANK_SEL']
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)  # disable bank select

            # Set /DAC_SC0 to output.
            pin = self.pin_map['nDAC_CS0']
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 1)

            # Set ADC /SYNC to output.
            pin = self.pin_map['nADC_SYNC']
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)

            # Set DAC /RESET to output.
            pin = self.pin_map['nDAC_RESET']
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 1)  # put DAC in run mode

            # Set DAC /LDAC to output and low level for Asynchronous Mode
            pin = self.pin_map['nLDAC']
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)

            # Set DAC CLR to output.
            pin = self.pin_map['DAC_CLR']
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)

            # Set DAC /Alarm to input.
            pin = self.pin_map['nDAC_ALARM']
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # There are 12 ADCs divided into three banks of 4. To enbale an
    # ADC select the bank using the bank_sel lines and then the chip
    # using the chip_sel lines.

    def adc_sel(self, adc_id):
        cs0 = self.pin_map['nADC_CS0']
        cs1 = self.pin_map['nADC_CS1']
        bs1 = self.pin_map['nADC_BANK1_SEL']
        bs2 = self.pin_map['nADC_BANK2_SEL']
        bs3 = self.pin_map['nADC_BANK3_SEL']
        adc_mux_id = adc_id % 4

        # deselect all chips first
        # GPIO.output(bs1, 1)
        # GPIO.output(bs2, 1)
        # GPIO.output(bs3, 1)

        with Gbl.ioLock:
            if adc_id in range(0, 4):
                GPIO.output(bs1, 0)
                GPIO.output(bs2, 1)
                GPIO.output(bs3, 1)

            elif adc_id in range(4, 8):
                GPIO.output(bs1, 1)
                GPIO.output(bs2, 0)
                GPIO.output(bs3, 1)

            elif adc_id in range(8, 12):
                GPIO.output(bs1, 1)
                GPIO.output(bs2, 1)
                GPIO.output(bs3, 0)
            else:
                GPIO.output(bs1, 1)
                GPIO.output(bs2, 1)
                GPIO.output(bs3, 1)

            # deselect chip first
            if adc_mux_id >= 0 and adc_mux_id < 3:
                GPIO.output(cs1, 1)
                GPIO.output(cs0, 1)
            else:
                GPIO.output(cs1, 0)
                GPIO.output(cs0, 0)

            # now select the one you want
            if adc_mux_id == 0:
                GPIO.output(cs1, 0)
                GPIO.output(cs0, 0)

            elif adc_mux_id == 1:
                GPIO.output(cs1, 0)
                GPIO.output(cs0, 1)

            elif adc_mux_id == 2:
                GPIO.output(cs1, 1)
                GPIO.output(cs0, 0)

            elif adc_mux_id == 3:
                GPIO.output(cs1, 1)
                GPIO.output(cs0, 1)

            else:
                GPIO.output(cs1, 1)
                GPIO.output(cs0, 1)

