import time
import GPIO_config
import RPi.GPIO as GPIO
import utilities

import Gbl

class DacSpi(object):

    def __init__(self, idx, io):
        self.idx = idx
        self.lsbfirst = False
        self.io = io
        self.mosi = self.io.pin_map['SPI1_MOSI']
        self.miso = self.io.pin_map['SPI1_MISO']
        self.sclk = self.io.pin_map['SPI1_SCLK']
        self.usleep = lambda x: time.sleep(x / 1000000.0)
        self.no_cs = True
        self.bits_per_word = 8
        self.threewire = False
        self.loop = False

    def xfer(self, dataword):
        ret_val = 0
        ret_list = [0, 0, 0]

        # Can see putting this in cython -- CPL
        #
        with Gbl.ioLock:
            self.io.dac_sel(self.idx)

            j = 0
            for abytes in dataword:
                for i in range(8):
                    if abytes & 0x80:
                        bit = 1
                    else:
                        bit = 0
                    misobit = self.__clock_dac(bit)
                    position = (j * 8) + i
                    if misobit == 1:
                        ret_val += 2**position
                    abytes = abytes << 1 & 0xff
                j += 1

            self.io.dac_sel(3)

        self.usleep(200)
        ret_list[0] = ret_val & 0xff
        ret_list[1] = ret_val >> 8 & 0xff
        ret_list[2] = ret_val >> 16 & 0xff
        ret_list[0] = utilities.reverse_bits(ret_list[0])
        ret_list[1] = utilities.reverse_bits(ret_list[1])
        ret_list[2] = utilities.reverse_bits(ret_list[2])
        return ret_list

    def __oneUs(self):
        """ Pause something like a microsecond on a Pi 3. """
        return
    
    def __clock_dac(self, value=0):  # clocks a single dac bit

        if value == 1:
            GPIO.output(self.mosi, 1)
        else:
            GPIO.output(self.mosi, 0)
        self.__oneUs()
        GPIO.output(self.sclk, 0)
        self.__oneUs()          # I do not see why the GPIO call does not always provide 1us delay
        bitval = GPIO.input(self.miso)
        GPIO.output(self.sclk, 1)
        self.__oneUs()
        return bitval
