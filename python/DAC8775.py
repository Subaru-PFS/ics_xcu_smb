import logging
import time

from utilities import getbytes_from_reg_bits
import quieres
from spi_bus import DacSpi

import Gbl

class DAC(object):
    """
    DAC8775 object. There are two of these on one heater board
    """

    # <editor-fold desc="******************* Public Methods *******************">

    def __init__(self, idx, smbdb, spi, io, doReset=False):
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

        self.spi_obj = DacSpi(self.idx, io)
        self.pins = io
        self.__dac_initialize(doReset=doReset)

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
        self.logger.debug('heater %d wrote reg %s/%d = 0x%04x/%d (%s)',
                          self.idx, regname, regid,
                          write_bytes, write_bytes,
                          kwargs)

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
        dict_register['register'] = '0x%04x' % (value)
        for item in reg_bit_data:
            keyname = item['NAME']
            dataval = (value >> item['SHIFT']) & item['MASK']
            dict_register[keyname] = dataval

        self.logger.debug('heater %d read reg %s/%d = 0x%04x/%d (%s)',
                          self.idx, reg_name, (regid & ~self._READ_FLAG),
                          value, value,
                          dict_register)
        return dict_register

    def select_dac(self, dac='none'):
        dac = dac.lower()

        with Gbl.ioLock:
            dict_sel_dac_reg = self.dac_read_register('select_dac')
            if dac == 'a':
                dict_sel_dac_reg['cha'] = True
                dict_sel_dac_reg['chb'] = False
                dict_sel_dac_reg['chc'] = False
                dict_sel_dac_reg['chd'] = False
            elif dac == 'b':
                dict_sel_dac_reg['cha'] = False
                dict_sel_dac_reg['chb'] = True
                dict_sel_dac_reg['chc'] = False
                dict_sel_dac_reg['chd'] = False
            elif dac == 'c':
                dict_sel_dac_reg['cha'] = False
                dict_sel_dac_reg['chb'] = False
                dict_sel_dac_reg['chc'] = True
                dict_sel_dac_reg['chd'] = False
            elif dac == 'd':
                dict_sel_dac_reg['cha'] = False
                dict_sel_dac_reg['chb'] = False
                dict_sel_dac_reg['chc'] = False
                dict_sel_dac_reg['chd'] = True
            elif dac == 'all':
                dict_sel_dac_reg['cha'] = True
                dict_sel_dac_reg['chb'] = True
                dict_sel_dac_reg['chc'] = True
                dict_sel_dac_reg['chd'] = True
            else:
                dict_sel_dac_reg['cha'] = False
                dict_sel_dac_reg['chb'] = False
                dict_sel_dac_reg['chc'] = False
                dict_sel_dac_reg['chd'] = False
            self.dac_write_register('select_dac', **dict_sel_dac_reg)
        self.logger.debug('selected DAC %s' % (dac))
        
    def dac_write_dac_data_reg(self, value):
        """ Write a DAC data value.

        Args
        ----
        value : int 
          Must be 0...0xffff. Clipped to that.

        """

        if value < 0:
            self.logger.warn('clipping heater %d request %s up to 0', self.idx, value)
            value = 0
        if value > 0xffff:
            self.logger.warn('clipping heater %d request %s down to 0xffff', self.idx, value)
            value = 0xffff

        regid = self.__search_reg_address_from_name('DAC_data')
        rbytes = value.to_bytes(2, byteorder='big')
        bytelist = bytearray([regid])
        bytelist.extend(rbytes)

        with Gbl.ioLock:
            self.spi_obj.xfer(bytelist)
        self.logger.debug('htr %d: wrote data reg: 0x%04x, %s', self.idx,
                          value, ','.join(['0x%02x'%b for b in bytelist]))

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

        self.logger.debug('htr %d: read data reg: 0x%04x, %s', self.idx,
                          dacdata, ','.join(['0x%02x'%b for b in data_24]))
        
        return dacdata

    def dac_check_status(self):
        retries = 2
        doReset = dict()
        while retries > 0:
            retries -= 1
            status = self.dac_read_register('status')
            self.logger.debug('htr %d status: %s', self.idx, status)
            badBits = {'fa', 'fb', 'fc', 'fd', 'wdt', 'cre', 'tmp'}
            goodBits = {'pga', 'pgb', 'pgc', 'pgd'}
            for b in badBits:
                if status[b]:
                    self.logger.warn('htr %d error: %s is set', self.idx, b)
                    doReset[b] = 1
            for b in goodBits:
                if not status[b]:
                    self.logger.warn('htr %d error: %s is not set', self.idx, b)

            if doReset and retries > 0:
                self.dac_write_register('status', **doReset)
                time.sleep(0.001)
            else:
                retries = 0
            
    # def dac_aliveness_check(self):
    #     self.dac_write_register('reset_config', 'tblDacResetConfigReg',
    #                             ubt=True, poc=False, clr=False, trn=False, ref_en=False,
    #                             clrena=False, clrenb=False, clrenc=False, clrend=False)
    #     reg_dict = self.dac_read_register('status', 'tblDacStatusReg')
    #     okay = bool(reg_dict['err'])
    #     return okay

    # </editor-fold>

    # <editor-fold desc="******************* Private Methods *******************">

    def __dac_initialize(self, doReset=False):
        """ Reset the DAC """
        self.RegAddrs = quieres.db_table_data_to_dictionary(self.db,'tblDacRegisters')

        with Gbl.ioLock:
            if doReset:
                # write reset reg
                self.dac_write_register('reset', rst=1)
                self.logger.warning("htr %d reset", self.idx)

            # write reset config reg (use external reference).
            reset_config_dict = quieres.db_dac_fetch_names_n_values(self.db,'reset_config', self.dac_num)
            self.dac_write_register('reset_config', **reset_config_dict)
            resetconfig = self.dac_read_register('reset_config')
            # if reset_config_dict != resetconfig:
            self.logger.info("htr %d reset_config: %s", self.idx, resetconfig)

            # Write Select Buck Boost Register (Select A,B,C & D).
            buck_boost_dict = quieres.db_dac_fetch_names_n_values(self.db, 'Select_Buck_Boost_converter', self.dac_num)
            self.dac_write_register('Select_Buck_Boost_converter', **buck_boost_dict)
            buckboostsel = self.dac_read_register('Select_Buck_Boost_converter')
            self.logger.info("htr %d select_buck_boost: %s", self.idx, buckboostsel)

            # Write Config Buck-Boost reg.
            cfg_buck_boost_dict = quieres.db_dac_fetch_names_n_values(self.db, 'configuration_Buck_Boost_converter', self.dac_num)
            self.dac_write_register('configuration_Buck_Boost_converter', **cfg_buck_boost_dict)
            buckboostconfig = self.dac_read_register('configuration_Buck_Boost_converter')
            self.logger.info("htr %d config_buck_boost: %s", self.idx, buckboostconfig)

            # Write Select DAC Register.
            sel_dac_dict = quieres.db_dac_fetch_names_n_values(self.db, 'select_dac', self.dac_num)
            self.dac_write_register('select_dac', **sel_dac_dict)
            dacsel = self.dac_read_register('select_dac')
            self.logger.info("htr %d select_dac: %s", self.idx, dacsel)

            # Write Config Dac Register.
            cfg_dac_dict = quieres.db_dac_fetch_names_n_values(self.db, 'configuration_dac', self.dac_num)
            self.dac_write_register('configuration_dac', **cfg_dac_dict)
            daccnfg = self.dac_read_register('configuration_dac')
            self.logger.info("htr %d config_dac: %s", self.idx, daccnfg)

            # Write Program DAC Data.
            self.dac_write_dac_data_reg(0x0000)
            # Read Config Dac Register.
            dacdata = self.dac_read_dac_data_reg()
            self.logger.info("htr %d dac value = 0x04%x", self.idx, dacdata)

            

    def __search_reg_address_from_name(self, name):
        for a in self.RegAddrs:
            if a['NAME'] == name:
                return a['ADDRESS']

        return -1

    # </editor-fold>
