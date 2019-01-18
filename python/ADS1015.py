# the ADS1015 is uesed to read the current feedback
# from the AUIPS7121R ICs and thus measure
# the Bang-Bang heater current

import smbus as smbus  # Rpi's I2C bus driver
from utilities import getbytes_from_reg_bits
import quieres


class ADS1015(object):

    def __init__(self, smbdb):
        self.db = smbdb
        self.RegAddrs = []
        # Open I2C-Bus
        self.i2c_bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

        # I2C-Adress and Register of ads1015
        self.i2c_address = 0x48  # I2C address of ADS1015 w/ ADDR pin at GND
        self.__ads1015_initialize()

    def __delete__(self, instance):
        self.i2c_bus.close()

    # <editor-fold desc="******** Public Methods ***************************">

    def ads1015_read_current_bb(self, bb_idx):  # bang-banag id (1 or 2)
        if 1 <= bb_idx <= 2:
            self.ads1015_select_input(bb_idx - 1)
            conv_data = self.__ads1015_read_register_to_dict('Conversion')
            return conv_data['data']
        else:
            return 0

    def ads1015_select_input(self, input_id):
        # 000: AINP = AIN0 and AINN = AIN1(default)
        # 001: AINP = AIN0 and AINN = AIN3
        # 010: AINP = AIN1 and AINN = AIN3
        # 011: AINP = AIN2 and AINN = AIN3
        # 100: AINP = AIN0 and AINN = GND
        # 101: AINP = AIN1 and AINN = GND
        # 110: AINP = AIN2 and AINN = GND
        # 111: AINP = AIN3 and AINN = GND
        reg_dict = self.__ads1015_read_register_to_dict('Config')
        if input_id == 0:
            reg_dict["mux"] = 0
        if input_id == 1:
            reg_dict["mux"] = 3
        self.__ads1015_write_register('Config', **reg_dict)

    # </editor-fold>

    # <editor-fold desc="***************** Private Methods ******************************">

    def __ads1015_initialize(self):
        self.RegAddrs = quieres.db_table_data_to_dictionary(self.db, 'tblADS1015Registers')
        # Fetch default Config reg values from db.
        dict_config_reg = quieres.db_ads1015_fetch_names_n_values(self.db, 'Config')
        # Write Config Register.
        self.__ads1015_write_register('Config', **dict_config_reg)
        value = self.__ads1015_read_register_to_dict('Config')
        print(value)

    def __ads1015_write_register(self, reg_name, **kwargs):
        reg_dict = quieres.db_ads1015_register_data_to_dictionary(self.db, reg_name)
        write_bytes = getbytes_from_reg_bits(kwargs, reg_dict)
        regid = self.__search_reg_address_from_name(reg_name)
        rbytes = write_bytes.to_bytes((write_bytes.bit_length() + 7) // 8, byteorder='big')
        bytelist = []
        for val in rbytes:
            bytelist.append(val)
        try:
            self.i2c_bus.write_i2c_block_data(self.i2c_address, regid, bytelist)
        except IOError as e:
            errno, strerror = e.args
            print("I/O error({0}): {1}".format(errno, strerror))

    def __ads1015_read_register_to_dict(self, reg_name):
        regid = self.__search_reg_address_from_name(reg_name)
        data_16 = self.i2c_bus.read_i2c_block_data(self.i2c_address, regid, 2)
        value = int.from_bytes(data_16, byteorder='big', signed=False)
        reg_bit_data = quieres.db_ads1015_register_data_to_dictionary(self.db, reg_name)
        dict_register = dict()
        for item in reg_bit_data:
            keyname = item['NAME']
            dataval = (value >> item['SHIFT']) & item['MASK']
            dict_register[keyname] = dataval
        return dict_register

    def __search_reg_address_from_name(self, name):
        for a in self.RegAddrs:
            if a['NAME'] == name:
                return a['ADDRESS']
        return -1

    def __search_reg_bytes_from_name(self, name):
        for a in self.RegAddrs:
            if a['NAME'] == name:
                return a['BYTES']
        return -1

    # </editor-fold>
