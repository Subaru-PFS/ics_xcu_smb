import logging

from utilities import getbytes_from_reg_bits
import quieres

import Gbl

class DAC(object):
    """
    DAC8775 object. There are two of these on one heater board
    """

    # <editor-fold desc="******************* Public Methods *******************">

    def __init__(self, idx, smbdb, spi, io):
        self.logger = logging.getLogger('heaters')
        self.db = smbdb
        self.idx = idx
        self.dac_num = idx + 1
        self.RegAddrs = []
        self._DUMMY_BYTE = 0x00
        self._READ_FLAG = 0x80
        self._LOW = bool(0)
        self._HIGH = bool(1)
        # self.spi_obj = spi_bus.RPi3Spi(1, mode=0, cs_id=0, max_speed_hz=1000)

        self.spi_obj = spi # DacSpi(self.idx)
        self.pins = io
        self.__dac_initialize()

    def dac_write_register(self, regname, **kwargs):

        reg_dict = quieres.db_dac_register_data_to_dictionary(self.db, regname, self.dac_num)
        write_bytes = getbytes_from_reg_bits(kwargs, reg_dict)

        regid = self.__search_reg_address_from_name(regname)
        rbytes = write_bytes.to_bytes((write_bytes.bit_length() + 7) // 8, byteorder='big')
        bytelist = [regid]
        for val in rbytes:
            bytelist.append(val)
        while len(bytelist) < 3:
            bytelist.insert(1, self._DUMMY_BYTE)

        with Gbl.ioLock:
            self.spi_obj.xfer(bytelist)

    def dac_read_register(self, reg_name):
        data_24 = [0, 0, 0]
        regid = self.__search_reg_address_from_name(reg_name)
        regid |= self._READ_FLAG
        byte_list = [regid, self._DUMMY_BYTE, self._DUMMY_BYTE]

        with Gbl.ioLock:
            self.spi_obj.xfer(byte_list)
            byte_list = [0, 0, 0]
            data_24 = self.spi_obj.xfer(byte_list)
        data_24.pop(0)

        value = int.from_bytes(data_24, byteorder='big', signed=False)
        reg_bit_data = quieres.db_dac_register_data_to_dictionary(self.db, reg_name, self.dac_num)
        dict_register = dict()
        for item in reg_bit_data:
            keyname = item['NAME']
            dataval = (value >> item['SHIFT']) & item['MASK']
            dict_register[keyname] = dataval
            self.logger.debug('heater %d read reg %s/%d, %s= 0x%04x/%d, 0x%04x/%d',
                              self.idx, reg_name, (regid & ~self._READ_FLAG),
                              keyname, value, value,
                              dataval, dataval)
        return dict_register

    def dac_write_dac_data_reg(self, write_bytes):

        regid = self.__search_reg_address_from_name('DAC_data')
        rbytes = write_bytes.to_bytes((write_bytes.bit_length() + 7) // 8, byteorder='big')
        bytelist = [regid]
        for val in rbytes:
            bytelist.append(val)
        while len(bytelist) < 3:
            bytelist.insert(1, self._DUMMY_BYTE)

        with Gbl.ioLock:
            self.spi_obj.xfer(bytelist)
        self.logger.debug('wrote data reg: %s', ','.join(['0x%02x'%b for b in bytelist]))
        
    def dac_read_dac_data_reg(self):

        regid = self.__search_reg_address_from_name('DAC_data')
        regid |= self._READ_FLAG
        byte_list = [regid, self._DUMMY_BYTE, self._DUMMY_BYTE]

        with Gbl.ioLock:
            self.spi_obj.xfer(byte_list)
            regid = self.__search_reg_address_from_name('no_operation')
            regid |= self._READ_FLAG
            byte_list = [regid, self._DUMMY_BYTE, self._DUMMY_BYTE]
            data_24 = self.spi_obj.xfer(byte_list)
        data_24.pop(0)
        dacdata = int.from_bytes(data_24, byteorder='big', signed=False)

        return dacdata

    # def dac_aliveness_check(self):
    #     self.dac_write_register('reset_config', 'tblDacResetConfigReg',
    #                             ubt=True, poc=False, clr=False, trn=False, ref_en=False,
    #                             clrena=False, clrenb=False, clrenc=False, clrend=False)
    #     reg_dict = self.dac_read_register('status', 'tblDacStatusReg')
    #     okay = bool(reg_dict['err'])
    #     return okay

    # </editor-fold>

    # <editor-fold desc="******************* Private Methods *******************">

    def __dac_initialize(self):
        """ Reset the DAC """
        self.RegAddrs = quieres.db_table_data_to_dictionary(self.db,'tblDacRegisters')

        with Gbl.ioLock:
            # write reset config reg (use external reference).
            reset_config_dict = quieres.db_dac_fetch_names_n_values(self.db,'reset_config', self.dac_num)
            self.dac_write_register('reset_config', **reset_config_dict)
            resetconfig = self.dac_read_register('reset_config')
            # if reset_config_dict != resetconfig:
            print(resetconfig)

            # Write Select Buck Boost Register (Select A,B,C & D).
            buck_boost_dict = quieres.db_dac_fetch_names_n_values(self.db, 'Select_Buck_Boost_converter', self.dac_num)
            self.dac_write_register('Select_Buck_Boost_converter', **buck_boost_dict)
            buckboostsel = self.dac_read_register('Select_Buck_Boost_converter')
            print(buckboostsel)

            # Write Config Buck-Boost reg.
            cfg_buck_boost_dict = quieres.db_dac_fetch_names_n_values(self.db, 'configuration_Buck_Boost_converter', self.dac_num)
            self.dac_write_register('configuration_Buck_Boost_converter', **cfg_buck_boost_dict)
            buckboostconfig = self.dac_read_register('configuration_Buck_Boost_converter')
            print(buckboostconfig)

            # Write Select DAC Register.
            sel_dac_dict = quieres.db_dac_fetch_names_n_values(self.db, 'select_dac', self.dac_num)
            self.dac_write_register('select_dac', **sel_dac_dict)
            dacsel = self.dac_read_register('select_dac')
            print(dacsel)

            # Write Config Dac Register.
            cfg_dac_dict = quieres.db_dac_fetch_names_n_values(self.db, 'configuration_dac', self.dac_num)
            self.dac_write_register('configuration_dac', **cfg_dac_dict)
            daccnfg = self.dac_read_register('configuration_dac')
            print(daccnfg)

            # Write Program DAC Data.
            self.dac_write_dac_data_reg(0x0000)
            # Read Config Dac Register.
            dacdata = self.dac_read_dac_data_reg()
            print("Dac cfg = 0x%x" % dacdata)

    def __search_reg_address_from_name(self, name):
        for a in self.RegAddrs:
            if a['NAME'] == name:
                return a['ADDRESS']

        return -1

    # </editor-fold>
