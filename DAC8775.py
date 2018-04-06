import spi_bus
from GPIO_config import gpio
from db import db_table_data_to_dictionary, db_dac_register_data_to_dictionary


class DAC(object):

    # <editor-fold desc="******************* Properties *******************">

    # </editor-fold>

    # <editor-fold desc="******************* Public Methods *******************">

    def __init__(self, idx):
        self.idx = idx
        self.RegAddrs = []
        self._DUMMY_BYTE = 0x00
        self._READ_FLAG = 0x80
        self._LOW = bool(0)
        self._HIGH = bool(1)
        self.spi_obj = spi_bus.RPi3Spi(1, cs_id=idx, mode=2, max_speed_hz=1000)
        self.pins = gpio()
        self.dac_initialize()

    def __delete__(self, instance):
        self.spi_obj.close()

    def dac_initialize(self):
        """ Reset the DAC """
        self.RegAddrs = db_table_data_to_dictionary('tblDacRegisters')
        self.dac_reset()
        # status = self.dac_aliveness_check()
        # if status is True:
        #     print("DAC aliveness test passed")
        # else:
        #     print("DAC aliveness test failed!")

        chipid = self.dac_read_register('device_ID')
        print(chipid)

        # write reset config reg (use external reference).
        self.dac_write_register('reset_config',
                                ubt=False, poc=False, clr=False, trn=False, ref_en=True,
                                clrena=False, clrenb=False, clrenc=False, clrend=False)
        # Read reset config.
        resetconfig = self.dac_read_register('reset_config')
        print(resetconfig)

        # Write Select Buck Boost Register (Select A,B,C & D).
        self.dac_write_register('Select_Buck_Boost_converter',
                                dca=True, dcb=True, dcc=True, dcd=True)
        # Read Select Buck Boost Register.
        buckboostsel = self.dac_read_register('Select_Buck_Boost_converter')
        print(buckboostsel)

        # Write Config Buck-Boost reg.
        self.dac_write_register('configuration_Buck_Boost_converter',
                                pnsel=3, nclmp=7, pclmp=8, cclp=0)
        # Read Config Buck Boost Register.
        buckboostconfig = self.dac_read_register('configuration_Buck_Boost_converter')
        print(buckboostconfig)

        # Write Select DAC Register.
        self.dac_write_register('select_dac',
                                wen=False, wpd=0, cren=False, dsdo=True,
                                cha=True, chb=True, chc=True, chd=True,
                                clsla=False, clslb=False, clslc=False, clsld=False)
        # Read Select DAC Register.
        dacsel = self.dac_read_register('select_dac')
        print(dacsel)

        # Write Config Dac Register.
        self.dac_write_register('configuration_dac',
                                range=6, sren=False, sr_step=0, srclk_rate=0xf,
                                oten=False, hten=False, sclim=0)
        # Read Config Dac Register.
        daccnfg = self.dac_read_register('configuration_dac')
        print(daccnfg)

        # Write Program DAC Data.
        self.dac_write_dac_data_reg(0x0000)
        # Read Config Dac Register.
        dacdata = self.dac_read_dac_data_reg()
        print("Dac cfg = 0x%x" % dacdata)

    def dac_write_register(self, regname,  **kwargs):
        reg_dict = db_dac_register_data_to_dictionary(regname)
        write_bytes = self.__dac_getbytes_from_reg_bits(kwargs, reg_dict)

        regid = self.__search_reg_address_from_name(regname)
        rbytes = write_bytes.to_bytes((write_bytes.bit_length() + 7) // 8, byteorder='big')
        bytelist = [regid]
        for val in rbytes:
            bytelist.append(val)
        while len(bytelist) < 3:
            bytelist.insert(1, self._DUMMY_BYTE)
        self.spi_obj.xfer(bytelist)

    def dac_read_register(self, reg_name):
        regid = self.__search_reg_address_from_name(reg_name)
        regid |= self._READ_FLAG
        byte_list = [regid, self._DUMMY_BYTE, self._DUMMY_BYTE]
        self.spi_obj.xfer2(byte_list)

        regid = self.__search_reg_address_from_name('no_operation')
        regid |= self._READ_FLAG
        byte_list = [regid, self._DUMMY_BYTE, self._DUMMY_BYTE]
        data_24 = self.spi_obj.xfer2(byte_list)
        data_24.pop(0)
        value = int.from_bytes(data_24, byteorder='big', signed=False)
        reg_bit_data = db_dac_register_data_to_dictionary(reg_name)
        dict_register = dict()
        for item in reg_bit_data:
            keyname = item['NAME']
            dataval = (value >> item['SHIFT']) & item['MASK']
            dict_register[keyname] = dataval
        return dict_register

    def dac_write_dac_data_reg(self, write_bytes):
        regid = self.__search_reg_address_from_name('DAC_data')
        rbytes = write_bytes.to_bytes((write_bytes.bit_length() + 7) // 8, byteorder='big')
        bytelist = [regid]
        for val in rbytes:
            bytelist.append(val)
        while len(bytelist) < 3:
            bytelist.insert(1, self._DUMMY_BYTE)
        self.spi_obj.xfer(bytelist)

        # self.__dac_write_register('DAC_data', write_bytes)

    def dac_read_dac_data_reg(self):

        regid = self.__search_reg_address_from_name('DAC_data')
        regid |= self._READ_FLAG
        byte_list = [regid, self._DUMMY_BYTE, self._DUMMY_BYTE]
        self.spi_obj.xfer2(byte_list)

        regid = self.__search_reg_address_from_name('no_operation')
        regid |= self._READ_FLAG
        byte_list = [regid, self._DUMMY_BYTE, self._DUMMY_BYTE]
        data_24 = self.spi_obj.xfer2(byte_list)

        data_24.pop(0)
        dacdata = int.from_bytes(data_24, byteorder='big', signed=False)
        return dacdata

    def dac_reset(self):
        self.pins.dac_reset(self._LOW)
        self.pins.dac_reset(self._HIGH)

    # def dac_aliveness_check(self):
    #     self.dac_write_register('reset_config', 'tblDacResetConfigReg',
    #                             ubt=True, poc=False, clr=False, trn=False, ref_en=False,
    #                             clrena=False, clrenb=False, clrenc=False, clrend=False)
    #     reg_dict = self.dac_read_register('status', 'tblDacStatusReg')
    #     okay = bool(reg_dict['err'])
    #     return okay

    # </editor-fold>

    # <editor-fold desc="******************* Private Methods *******************">

    def __search_reg_address_from_name(self, name):
        for a in self.RegAddrs:
            if a['NAME'] == name:
                return a['ADDRESS']

        return -1

    def __dac_getbytes_from_reg_bits(self, kwargs, reg_dict):
        write_bytes = 0x0000
        for kword in kwargs:
            for item in reg_dict:
                if item["NAME"] == kword:
                    name = item["NAME"]
                    value = int(kwargs[name])
                    shift = item["SHIFT"]
                    mask = item["MASK"]
                    write_bytes = write_bytes | ((value & mask) << shift)
        return write_bytes

    # </editor-fold>
