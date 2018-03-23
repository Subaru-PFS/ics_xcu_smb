import DAC8775_Reg_Addresses as RegAddrs
import spi_bus
from GPIO_config import gpio
import sqlite3


class DAC(object):

    # <editor-fold desc="*************** Properties*******************">

    # </editor-fold>

    # <editor-fold desc="********** Public Methods *****************">

    def __init__(self, idx):
        self.idx = idx
        self._DUMMY_BYTE = 0x00
        self._READ_FLAG = 0x80
        self._LOW = bool(0)
        self._HIGH = bool(1)
        self.spi_obj = spi_bus.RPi3Spi(1, cs_id=idx, mode=2, max_speed_hz=1000)
        self.pins = gpio()

    def __delete__(self, instance):
        self.spi_obj.close()

    def dac_initialize(self):
        """ Reset the DAC """
        self.dac_reset()
        status = self.dac_aliveness_check()
        if status is True:
            print("DAC aliveness test passed")
        else:
            print("DAC aliveness test failed!")

        chipid = self.dac_read_id()
        print("Chipid=0x%x" % chipid)

        """ write reset config reg (use external reference) """
        self.dac_write_reset_config_reg(ubt=False, poc=False, clr=False, trn=False, ref_en=True,
                                        clrena=False, clrenb=False, clrenc=False, clrend=False)
        """ Read reset config  """
        resetconfig = self.dac_read_reset_config_reg()
        print("Config=0x%x" % resetconfig)

        """ Write Select Buck Boost Register (Select A,B,C & D) """
        self.dac_write_buck_bosst_reg(dca=True, dcb=True, dcc=True, dcd=True)
        """ Read Select Buck Boost Register """
        buckboostsel = self.dac_read_buck_boost_reg()
        print("BuckBoostSel=0x%x" % buckboostsel)

        """ Write Config Buck-Boost reg """
        self.dac_write_config_buck_boost_reg(pnsel=3, nclmp=7, pclmp=8, cclp=0)
        """ Read Config Buck Boost Register """
        buckboostconfig = self.dac_read_config_buck_boost_reg()
        print("BuckBoost Config=0x%x" % buckboostconfig)

        """ Write Select DAC Register """
        self.dac_write_select_dac_reg(wen=False, wpd=0, cren=False, dsdo=True,
                                      cha=True, chb=True, chc=True, chd=True,
                                      clsla=False, clslb=False, clslc=False, clsld=False)
        """ Read Select DAC Register """
        dacsel = self.dac_read_select_dac_reg()
        print(dacsel)

        """ Write Config Dac Register"""
        self.dac_write_config_dac_reg(range=4, sren=False, sr_step=0, srclk_rate=0,
                                      oten=True, hten=False, sclim=0)
        """ Read Config Dac Register """
        daccnfg = self.dac_read_config_dac_reg()
        print("Dac cfg=0x%x" % daccnfg)

        """ Write Program DAC Data """
        self.dac_write_dac_data_reg(0xffff)
        """ Read Config Dac Register """
        dacdata = self.dac_read_dac_data_reg()
        print("Dac cfg = 0x%x" % dacdata)

    def dac_write_select_dac_reg(self, **kwargs):
        reg_dict = self.__dac_retrieve_reg_bits_from_db('tblDacSelectDacReg')
        write_bytes = self.__dac_getbytes_from_reg_bits(kwargs, reg_dict)
        self.__dac_write_register('select_dac', write_bytes)

    def dac_read_select_dac_reg(self):
        self.__dac_read_register('select_dac')
        data_24 = self.__dac_read_register('no_operation')
        data_24.pop(0)
        value = int.from_bytes(data_24, byteorder='big', signed=False)
        reg_dict = dict()
        reg_dict['value'] = value
        reg_dict['wen'] = value & 0x000001
        reg_dict['wpd'] = (value >> 1) & 0x01
        reg_dict['cren'] = (value >> 2) & 0x01
        reg_dict['dsdo'] = (value >> 3) & 0x01
        reg_dict['cha'] = (value >> 4) & 0x01
        reg_dict['chb'] = (value >> 5) & 0x01
        reg_dict['chc'] = (value >> 6) & 0x01
        reg_dict['chd'] = (value >> 7) & 0x01
        reg_dict['clsla'] = (value >> 8) & 0x01
        reg_dict['clslb'] = (value >> 9) & 0x01
        reg_dict['clslc'] = (value >> 10) & 0x01
        reg_dict['clsld'] = (value >> 11) & 0x01
        return reg_dict

    def dac_write_config_dac_reg(self, **kwargs):
        reg_dict = self.__dac_retrieve_reg_bits_from_db('tblDacConfigDacReg')
        write_bytes = self.__dac_getbytes_from_reg_bits(kwargs, reg_dict)
        self.__dac_write_register('configuration_dac', write_bytes)

    def dac_read_config_dac_reg(self):
        self.__dac_read_register('configuration_dac')
        data_24 = self.__dac_read_register('no_operation')
        data_24.pop(0)
        daccnfg = int.from_bytes(data_24, byteorder='big', signed=False)
        return daccnfg

    def dac_write_config_buck_boost_reg(self, **kwargs):
        reg_dict = self.__dac_retrieve_reg_bits_from_db('tblDacConfigBuckBoostReg')
        write_bytes = self.__dac_getbytes_from_reg_bits(kwargs, reg_dict)
        self.__dac_write_register('configuration_Buck_Boost_converter', write_bytes)

    def dac_read_config_buck_boost_reg(self):
        self.__dac_read_register('configuration_Buck_Boost_converter')
        data_24 = self.__dac_read_register('no_operation')
        data_24.pop(0)
        buckboostconfig = int.from_bytes(data_24, byteorder='big', signed=False)
        return buckboostconfig

    def dac_write_buck_bosst_reg(self, **kwargs):
        reg_dict = self.__dac_retrieve_reg_bits_from_db('tblDacBuckBoostReg')
        write_bytes = self.__dac_getbytes_from_reg_bits(kwargs, reg_dict)
        self.__dac_write_register('Select_Buck_Boost_converter', write_bytes)

    def dac_read_buck_boost_reg(self):
        self.__dac_read_register('Select_Buck_Boost_converter')
        data_24 = self.__dac_read_register('no_operation')
        data_24.pop(0)
        buckboostsel = int.from_bytes(data_24, byteorder='big', signed=False)
        return buckboostsel

    def dac_write_reset_config_reg(self, **kwargs):
        reg_dict = self.__dac_retrieve_reg_bits_from_db('tblDacResetConfigReg')
        write_bytes = self.__dac_getbytes_from_reg_bits(kwargs, reg_dict)
        self.__dac_write_register('reset_config', write_bytes)

    def dac_read_reset_config_reg(self):
        self.__dac_read_register('reset_config')
        data_24 = self.__dac_read_register('no_operation')
        data_24.pop(0)
        resetconfig = int.from_bytes(data_24, byteorder='big', signed=False)
        return resetconfig

    def dac_write_dac_data_reg(self, write_bytes):
        self.__dac_write_register('DAC_data', write_bytes)

    def dac_read_dac_data_reg(self):
        self.__dac_read_register('DAC_data')
        data_24 = self.__dac_read_register('no_operation')
        data_24.pop(0)
        dacdata = int.from_bytes(data_24, byteorder='big', signed=False)
        return dacdata

    def dac_reset(self):
        self.pins.dac_reset(self._LOW)
        self.pins.dac_reset(self._HIGH)

    def dac_aliveness_check(self):
        self.dac_write_reset_config_reg(ubt=True, poc=False, clr=False, trn=False, ref_en=False,
                                        clrena=False, clrenb=False, clrenc=False, clrend=False)
        self.__dac_read_register('status')
        data_24 = self.__dac_read_register('no_operation')
        data_24.pop(0)
        resetconfig = int.from_bytes(data_24, byteorder='big', signed=False)
        resetconfig = (resetconfig >> 6) & 0x0001
        resp = bool(resetconfig)
        return resp

    def dac_read_id(self):
        self.__dac_read_register('device_ID')
        data_24 = self.__dac_read_register('no_operation')
        data_24.pop(0)
        chipid = int.from_bytes(data_24, byteorder='big', signed=False)
        return chipid

    # </editor-fold>

    # <editor-fold desc="************** Private Methods *************">

    def __dac_write_register(self, reg_name, value):
        regid = RegAddrs.search_reg_address_from_name(reg_name)
        rbytes = value.to_bytes((value.bit_length() + 7) // 8, byteorder='big')
        bytelist = [regid]
        for val in rbytes:
            bytelist.append(val)
        while len(bytelist) < 3:
            bytelist.insert(1, self._DUMMY_BYTE)
        self.spi_obj.xfer(bytelist)

    def __dac_read_register(self, reg_name):
        regid = RegAddrs.search_reg_address_from_name(reg_name)
        regid |= self._READ_FLAG
        byte_list = [regid, self._DUMMY_BYTE, self._DUMMY_BYTE]
        resp = self.spi_obj.xfer2(byte_list)
        return resp

    def __dac_retrieve_reg_bits_from_db(self, tblname):
        # Builds a dict of dicts from garden sqlite db
        reg_dict = {}
        conn = sqlite3.connect("smb.db")
        # Need to allow write permissions by others
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        qry = 'select * from ' + tblname + ' as data ORDER BY SHIFT'
        c.execute(qry)
        tuple_list = c.fetchall()
        conn.close()
        # Building dict from table rows

        for item in tuple_list:
            reg_dict[item] = {
                "PARENT_REG": item[0],
                "NAME": item[1],
                "MASK": item[2],
                "SHIFT": item[3],
                "VALUE": item[4]
            }

        return reg_dict

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
