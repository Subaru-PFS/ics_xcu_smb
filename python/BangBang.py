import RPi.GPIO as GPIO

import Gbl

class bang_bang(object):

    def __init__(self, idx, io):
        self.io = io
        self.idx = idx
        self.hi_pwr_en_pin = 0
        # Configure HI Power Enable Pins
        if self.idx == 0:
            self.hi_pwr_en_pin = self.io.pin_map['HI_PWR_EN1']
        elif self.idx == 1:
            self.hi_pwr_en_pin = self.io.pin_map['HI_PWR_EN2']

        with Gbl.ioLock:
            GPIO.setup(self.hi_pwr_en_pin, GPIO.OUT)
            GPIO.output(self.hi_pwr_en_pin, 0)

    def power_on_output(self):
        with Gbl.ioLock:
            GPIO.output(self.hi_pwr_en_pin, 1)

    def power_off_output(self):
        with Gbl.ioLock:
            GPIO.output(self.hi_pwr_en_pin, 0)

    def bang_bang_status(self):
        with Gbl.ioLock:
            status = bool(GPIO.input(self.hi_pwr_en_pin))
        return status
