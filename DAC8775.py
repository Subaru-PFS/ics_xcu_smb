import DAC8775_Reg_Addresses as RegAddrs
import spi_bus
import time

from  GPIO_config import gpio

class DAC(object):

    def __init__(self, idx):
        self.idx = idx
        self._DUMMY_BYTE = 0x00
        self._READ_FLAG = 0x80
        self._LOW = bool(0)
        self._HIGH = bool(1)
        self.spi_obj = spi_bus.RPi3Spi(1, cs_id = idx, mode=2, max_speed_hz = 1000)
        self.pins=gpio()

    def __delete__(self, instance):
        self.spi_obj.close()

    def dac_initialize(self):
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
        self.pins.dac0_enable()
        self.dac_write_register('dac_channel_offset_calibration', write_bytes)
        self.pins.dac1_disable()

        """ Read offset register """
        data_24 = self.dac_read_register('dac_channel_offset_calibration')
        offset = int.from_bytes(data_24, byteorder='big', signed=False)
        print("offset=0x%x" % offset)

    def dac_read_register(self, reg_name):

        regid = RegAddrs.search_reg_address_from_name(reg_name)
        regid |= self._READ_FLAG
        byte_list = [regid, self._DUMMY_BYTE, self._DUMMY_BYTE]
        self.pins.dac0_enable()
        time.sleep(.0001)
        self.spi_obj.writebytes(byte_list)
        self.pins.dac1_disable()
        self.pins.dac0_enable()
        time.sleep(.0001)
        resp = self.spi_obj.readbytes(3)
        self.pins.dac1_disable()
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
        self.pins.dac0_enable()
        self.pins.dac_reset(self._LOW)
        self.pins.dac_reset(self._HIGH)
        self.pins.dac1_disable()

    def dac_read_id(self):
        data_32 = self.dac_read_register('device_ID', 1)
        print(data_32)
        data_32.pop(2)
        data_32.pop(1)
        chipid = int.from_bytes(data_32, byteorder='big', signed=False)
        return chipid
