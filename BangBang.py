import RPi.GPIO as GPIO
from GPIO_config import io

class bang_bang(object):

    def __init__(self, idx):
        self.io = io()
        self.idx = idx
        self._output_state = 0
        # Configure HI Power Enable Pins
        if self.idx == 0:
            pin = self.io.pin_map['HI_PWR_EN1']
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)
        elif self.idx == 1:
            pin = self.io.pin_map['HI_PWR_EN2']
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)
            self.power_off_output()

    @property
    def output_state(self):
        return self._output_state

    @output_state.setter
    def output_state(self, value):
        self._output_state = value


    def power_on_output(self):
        if self.idx == 0:
            pin = self.io.pin_map['HI_PWR_EN1']
            GPIO.output(pin, 1)
            self._output_state=1
        elif self.idx == 1:
            pin = self.io.pin_map['HI_PWR_EN2']
            GPIO.output(pin, 1)
            self._output_state=1
        else:
            pin = self.io.pin_map['HI_PWR_EN1']
            GPIO.output(pin, 0)
            pin = self.io.pin_map['HI_PWR_EN2']
            GPIO.output(pin, 0)
            self._output_state=0

    def power_off_output(self):
        self._output_state = 0
        if self.idx == 0:
            pin = self.io.pin_map['HI_PWR_EN1']
            GPIO.output(pin, 0)
        elif self.idx == 1:
            pin = self.io.pin_map['HI_PWR_EN2']
            GPIO.output(pin, 0)
        else:
            pin = self.io.pin_map['HI_PWR_EN1']
            GPIO.output(pin, 0)
            pin = self.io.pin_map['HI_PWR_EN2']
            GPIO.output(pin, 0)
