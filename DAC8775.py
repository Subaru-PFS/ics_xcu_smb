import DAC8775_Reg_Addresses as RegAddrs
import spi_bus
import time
import db
import RPi.GPIO as GPIO


class DAC(object):
    """ DAC Class """

    def __init__(self, idx, tlm_dict):
        self._DUMMY_BYTE = 0x00
        self._READ_FLAG = 0x80
        self._ENABLE = bool(0)
        self._DISABLE = bool(1)
        self.tlm_dict = tlm_dict
        self.htr_num = idx + 1
        self.spi_obj = spi_bus.RPi3Spi(1, idx, mode=2, max_speed_hz=7629)
        self.__dac_initialize()

    def __delete__(self, instance):
        self.spi_obj.close()

    def __dac_initialize(self):
        """ SET GPIO numbering mode to use GPIO designation, NOT pin numbers """
        GPIO.setmode(GPIO.BCM)

        if self.htr_num == 1:
            """ Set SPI1 DAC CS (SYNC) pin high """
            pin = RegAddrs.gpio['nDAC_CS']
            GPIO.setup(pin, GPIO.OUT)  # SPI1-CS0
            GPIO.output(pin, 1)

            """ Set DAC /RESET to output"""
            pin = RegAddrs.gpio['nRESET']
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 1)  # put DAC in run mode

            """ Set DAC /LDAC to output """
            pin = RegAddrs.gpio['nLDAC']
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 1)

            """ Set DAC CLR to output"""
            pin = RegAddrs.gpio['DAC_CLR']
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)

            """ Set DAC /Alarm to input"""
            pin = RegAddrs.gpio['nALARM']
            GPIO.setup(pin, GPIO.IN)

            """ Reset the DAC """
            self.dac_reset()

        """ Read ID register """
        # for i in range(4):
        #     data_24 = self.dac_read_register('device_ID')
        #     print(data_24)
        #     data_24.pop(2)
        #     data_24.pop(1)
        #     idval = int.from_bytes(data_24, byteorder='big', signed=False)
        # print("ID=0x%x" % idval)

        """ Write to offset register """
        write_bytes = 0x1234
        self.__set_chip_select(self._ENABLE)
        self.dac_write_register('dac_channel_offset_calibration', write_bytes)
        self.__set_chip_select(self._DISABLE)

        """ Read offset register """
        data_24 = self.dac_read_register('dac_channel_offset_calibration')
        offset = int.from_bytes(data_24, byteorder='big', signed=False)
        print("offset=0x%x" % offset)

    def __set_nldac(self, state):
        value = int(state)
        pin = RegAddrs.gpio['nLDAC']
        if self.htr_num == 1:
            GPIO.output(pin, value)

    def __set_chip_select(self, state):
        value = int(state)
        pin = RegAddrs.gpio['nDAC_CS']
        if self.htr_num == 1:
            GPIO.output(pin, value)

    def dac_read_register(self, reg_name):

        regid = RegAddrs.search_reg_address_from_name(reg_name)
        regid |= self._READ_FLAG
        byte_list = [regid, self._DUMMY_BYTE, self._DUMMY_BYTE]
        self.__set_chip_select(self._ENABLE)
        time.sleep(.0001)
        self.spi_obj.writebytes(byte_list)
        self.__set_chip_select(self._DISABLE)
        self.__set_chip_select(self._ENABLE)
        time.sleep(.0001)
        resp = self.spi_obj.readbytes(3)
        self.__set_chip_select(self._DISABLE)
        return resp

    def dac_write_register(self, reg_name, value):
        regid = RegAddrs.search_reg_address_from_name(reg_name)
        rbytes = value.to_bytes((value.bit_length() + 7) // 8, byteorder='big')
        bytelist = [regid]
        for val in rbytes:
            bytelist.append(val)
        while (len(bytelist) < 3):
            bytelist.insert(1, self._DUMMY_BYTE)
        self.spi_obj.writebytes(bytelist)

    def dac_reset(self):
        self.__set_chip_select(self._ENABLE)
        rst_pin = RegAddrs.gpio['nRESET']
        GPIO.output(rst_pin, 0)  # put DAC in reset mode
        GPIO.output(rst_pin, 1)  # put DAC in run
        clrpin = RegAddrs.gpio['DAC_CLR']
        GPIO.output(clrpin, 1)  # Clear the DAC
        GPIO.output(clrpin, 0)  # Remove the clear
        self.__set_chip_select(self._DISABLE)

    def dac_read_id(self):
        data_32 = self.dac_read_register('device_ID', 1)
        print(data_32)
        data_32.pop(2)
        data_32.pop(1)
        chipid = int.from_bytes(data_32, byteorder='big', signed=False)
        return chipid
