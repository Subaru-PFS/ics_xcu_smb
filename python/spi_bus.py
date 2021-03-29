import logging
import time
import GPIO_config
import RPi.GPIO as GPIO
import utilities

import Gbl

class DacSpi(object):

    def __init__(self, idx, io):
        self.logger =  logging.getLogger('DAC_SPI')
        self.logger.setLevel(logging.DEBUG)
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
        self.xfer = self.xfer2

    def xfer1(self, dataword):
        ret_val = 0
        ret_list = [0, 0, 0]

        # Can see putting this in cython -- CPL
        #
        outval = 0
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
                    outval <<= 1
                    outval |= bit
                j += 1

            self.io.dac_sel(3)

        self.usleep(200)
        ret_list[0] = ret_val & 0xff
        ret_list[1] = ret_val >> 8 & 0xff
        ret_list[2] = ret_val >> 16 & 0xff
        ret_list[0] = utilities.reverse_bits(ret_list[0])
        ret_list[1] = utilities.reverse_bits(ret_list[1])
        ret_list[2] = utilities.reverse_bits(ret_list[2])

        self.logger.debug('bb %d: out=%s in=%s (0x%06x 0x%06x)', self.idx,
                          utilities.adcListToHex(dataword),
                          utilities.adcListToHex(ret_list),
                          outval, ret_val)


        return ret_list

    def xfer2(self, datalist):
        # Prepare a simple sequence of bits.
        outval = 0
        for byte in datalist:
            outval <<= 8
            outval |= byte

        # Now walk over those, and capture MISO in the same order.
        retval = 0
        ret_list = [0, 0, 0]
        sent = 0
        with Gbl.ioLock:
            self.io.dac_sel(self.idx)

            for i in list(range(24))[::-1]:
                outbit = outval & (1 << i)
                misobit = self.__clock_dac(outbit)
                retval <<= 1
                retval |= misobit

                sent <<= 1
                sent |= (outbit != 0)

            self.io.dac_sel(3)

        time.sleep(2e-6)

        ret_list[2] = retval & 0xff
        ret_list[1] = retval >> 8 & 0xff
        ret_list[0] = retval >> 16 & 0xff

        self.logger.debug('bb %d: out=%s in=%s (0x%06x 0x%06x)', self.idx,
                          utilities.adcListToHex(datalist),
                          utilities.adcListToHex(ret_list),
                          sent, retval)

        return ret_list

    def __oneUs(self):
        """ Pause something like a microsecond on a Pi 3. """
        time.sleep(1e-3)
    
    def __clock_dac(self, value=0):  # clocks a single dac bit

        if value == 1:
            GPIO.output(self.mosi, 1)
        else:
            GPIO.output(self.mosi, 0)
        self.__oneUs()
        GPIO.output(self.sclk, 1)
        self.__oneUs()          # I do not see why the GPIO call does not always provide 1us delay
        bitval = GPIO.input(self.miso)
        GPIO.output(self.sclk, 0)
        self.__oneUs()
        return bitval
