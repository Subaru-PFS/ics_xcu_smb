import logging
import time

from utilities import getbytes_from_reg_bits
import quieres
import Gbl

class DAC(object):
    """
    DAC8775 object. There are two of these on one heater board
    """

    def __init__(self, idx, smbdb, dacs, doReset=False):
        self.logger = logging.getLogger('heaters')
        self.logger.setLevel(logging.INFO)
        self.db = smbdb
        self.idx = idx
        self.dac_num = idx + 1
        self.dacs = dacs

        self.__dac_initialize(doReset=doReset)

    def dac_register_value(self, regname, **kwargs):
        reg_dict = quieres.db_dac_register_data_to_dictionary(self.db, regname, self.dac_num)

        if 'register' in kwargs:
            del kwargs['register']

        newValue = getbytes_from_reg_bits(kwargs, reg_dict)
        return newValue

    def dac_value_dictionary(self, regname, value):
        reg_bit_data = quieres.db_dac_register_data_to_dictionary(self.db, regname, self.dac_num)
        dict_register = dict()
        dict_register['register'] = value
        for item in reg_bit_data:
            keyname = item['NAME']
            dataval = (value >> item['SHIFT']) & item['MASK']
            dict_register[keyname] = dataval
        return dict_register

    def dac_write_register(self, regname, **kwargs):
        newValue = self.dac_register_value(regname, **kwargs)

        self.dacs.writeReg(self.idx, regname, newValue)
        self.logger.debug('heater %d wrote reg %s = 0x%04x/%d (%s)',
                          self.idx, regname,
                          newValue, newValue,
                          kwargs)
        return newValue

    def dac_read_register(self, regname):
        value = self.dacs.readReg(self.idx, regname)
        dict_register =  self.dac_value_dictionary(regname, value)

        self.logger.debug('heater %d read reg %s = 0x%04x/%d (%s)',
                          self.idx, regname,
                          value, value,
                          dict_register)
        return dict_register

    def dac_write_raw(self, regnum, value):
        with Gbl.ioLock:
            self.dacs.writeReg(self.idx, regnum, value)
            checkValue = self.dacs.readReg(self.idx, regnum)

        self.logger.debug('heater %d wrote reg %d=0x%04x, read=0x%04x',
                          self.idx, regnum,
                          value, checkValue)
        return checkValue

    def dac_check_status(self, badOnly=False):
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
            if not badOnly:
                for b in goodBits:
                    if not status[b]:
                        self.logger.warn('htr %d error: %s is not set', self.idx, b)

            if doReset and retries > 0:
                self.dac_write_register('status', **doReset)
                time.sleep(0.001)
            else:
                retries = 0
            
    def _initialize_one_register(self, registerName, **config):
        self.logger.info("htr %d initializing %s: %s", self.idx, registerName, config)
        wrote = self.dac_write_register(registerName, **config)
        readBack = self.dac_read_register(registerName)

        ok = True
        for k,v in config.items():
            if v != readBack[k]:
                ok = False
        if not ok:
            self.logger.warning("MISMATCH on htr %d %s wrote 0x%04x %s",
                                self.idx, registerName, wrote, config)
            self.logger.warning("MISMATCH on htr %d %s read  0x%04x %s",
                                self.idx, registerName, readBack['register'], readBack)
        else:
            self.logger.info("htr %d %s: %s", self.idx, registerName, readBack)

    def __dac_initialize(self, doReset=True):
        """ Reset the DAC """

        with Gbl.ioLock:
            if doReset:
                # software reset sets all registers to 0.
                self.dac_write_register('reset', reset=1)
                self.logger.warning("htr %d reset", self.idx)
                time.sleep(0.01)

            # Need to revisit this list and sequence -- CPL.
            for regName in ('select_dac', 'reset_config',
                            'Select_Buck_Boost_converter',
                            'configuration_Buck_Boost_converter',
                            'configuration_dac'):
                if regName == 'select_dac':
                    config_dict = dict(dsdo=1, cha=1, chb=1, chc=1, chd=1)
                elif regName == 'reset_config':
                    config_dict = dict(clrena=1, clrenb=1, clrenc=1, clrend=1)
                elif regName == 'Select_Buck_Boost_converter':
                    config_dict = dict(dca=1, dcb=1, dcc=1, dcd=1)
                elif regName == 'configuration_Buck_Boost_converter':
                    config_dict = dict(pnsel=1)
                # elif regName == 'configuration_dac':
                #     config_dict = dict()
                else:
                    config_dict = quieres.db_dac_fetch_names_n_values(self.db, regName, self.dac_num)
                self._initialize_one_register(regName, **config_dict)

            # Initialize DAC
            self.dacs.writeDacData(self.idx, 'all', 0)

            # Check DAC output levels
            dacdata = [self.dacs.readDacData(self.idx, i) for i in 'abcd']
            self.logger.info("htr %d dac values = %s", self.idx, dacdata)

            self.dac_check_status(badOnly=True)
