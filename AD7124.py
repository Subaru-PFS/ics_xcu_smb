import time
from math import log
from Sensor import sensor
import math
import utilities
import GPIO_config
from utilities import getbytes_from_reg_bits
import quieres


class AD7124(object):
    """
    ADC Class, there is one sensor per ADC
    The primary channel that the imput sensor is connected to is chanel 0.

     Attributes
    ----------
    idx : int
        index of object in memory, starts at zero
    smbdb : obj
        reference to database object
    tlm_dict : dict
        global dictionary that holds updated telemetry values
     """

    def __init__(self, idx, smbdb, tlm_dict, spi_obj):
        self.pins = GPIO_config.io()
        self.db = smbdb
        self.idx = idx  # index of ADC (0 to 11)
        self._sens_num = idx + 1  # Sensor number (1 to 12)
        parameters = quieres.db_adc_fetch_params(self.db, self._sens_num)  # ID, units, sensor type, gain
        self._temp_unit = parameters['temperature_unit']  # (0=K 1=C 2=F)
        self._sns_type_id = parameters['sensor_type']
        self._adc_gain = parameters['gain']
        self._ref_resistor = 3920  # R2 or R26 on Rev-H
        self.tlm_dict = tlm_dict
        self._DUMMY_BYTE = 0xff
        self._READ_FLAG = 0b01000000
        self._adc_excitation_code = 1
        self._adc_filter = 1
        self.RegAddrs = []
        self.spi_obj = spi_obj
        self.__adc_initialize()
        self.sns = sensor(self.db, self._sns_type_id)  # Create sensor object for this ADC.

    def __delete__(self, instance):
        self.spi_obj.close()

    # <editor-fold desc="******************** ADC Properties ********************">

    @property
    def adc_filter(self):
        return self._adc_filter

    @adc_filter.setter
    def adc_filter(self, value):
        if value < 0 or value > 7:
            raise ValueError("Filter value out of range")
        self._adc_filter = value

    @property
    def temp_unit(self):
        return self._temp_unit

    @temp_unit.setter
    def temp_unit(self, value):
        self._temp_unit = value

    @property
    def sns_type_id(self):
        return self._sns_type_id

    @sns_type_id.setter
    def sns_type_id(self, value):
        self._sns_type_id = value

    # </editor-fold>

    # <editor-fold desc="******************* AD7124 Public Methods *******************">

    def set_filter_type(self, value):
        reg_name = 'Filter_0'  # filter 0 is RTD channel
        reg_dict = self.adc_read_register_to_dict(reg_name)

        switcher = {
            0: 0,
            1: 1,
            2: 2,
            3: 4,
            4: 5,
            5: 7
        }
        reg_dict["filter"] = switcher.get(value, 0)

        self.__adc_write_register(reg_name, **reg_dict)
        self._adc_filter = value
        quieres.db_adc_update_register_field(self.db, 'filter', self._sens_num, value)

    def set_post_filter_type(self, value):
        reg_name = 'Filter_0'  # filter 0 is RTD channel
        reg_dict = self.adc_read_register_to_dict(reg_name)

        switcher = {
            0: 2,
            1: 3,
            2: 5,
            3: 6,
        }

        reg_dict["post_filter"] = switcher.get(value, 0)

        self.__adc_write_register(reg_name, **reg_dict)
        self._adc_filter = value
        quieres.db_adc_update_register_field(self.db, 'post_filter', self._sens_num, value)

    def adc_set_temp_units(self, value):
        quieres.db_update_adc_params(self.db, value, 'temperature_unit', self._sens_num)
        self._temp_unit = value

    def adc_set_sensor_type(self, value):
        quieres.db_update_adc_params(self.db, value, 'sensor_type', self._sens_num)
        self._sns_type_id = value
        reg_dict = self.adc_read_register_to_dict('IOCon1')

        switcher = {
            1: 1,
            2: 0,
            3: 0,
        }

        dat1 = switcher.get(value, 1)
        reg_dict['gpio_dat1'] = dat1
        quieres.db_adc_update_register_field(self.db, 'gpio_dat1', self._sens_num, dat1)
        self.__adc_write_register('IOCon1', **reg_dict)

    def adc_set_sensor_wiring(self, value):
        reg_name = "IOCon1"
        reg_dict = self.adc_read_register_to_dict(reg_name)
        reg_dict["pdsw"] = value
        self.__adc_write_register(reg_name, **reg_dict)
        quieres.db_adc_update_register_field(self.db, 'pdsw', self._sens_num, value)

    def set_exciatation_current(self, value):
        reg_name = "IOCon1"
        reg_dict = self.adc_read_register_to_dict(reg_name)
        reg_dict["iout0"] = value
        self.__adc_write_register(reg_name, **reg_dict)
        self._adc_excitation_code = value
        quieres.db_adc_update_register_field(self.db, 'iout0', self._sens_num, value)

    def temperature_from_ntc_thermistor(self, rt):
        t_ref = 25
        r_at25 = self.sns.c0
        beta = self.sns.c1
        temperature_k = (t_ref + 273.15) * beta / beta + (t_ref + 273.15) * (math.log10(rt) - math.log10(r_at25))
        temperature_c = utilities.temp_k_to_c(temperature_k)
        temperature_f = utilities.temp_k_to_f(temperature_k)

        if self._temp_unit == 0:
            return temperature_k
        elif self._temp_unit == 1:
            return temperature_c
        elif self._temp_unit == 2:
            return temperature_f
        else:
            return temperature_k

    def temperature_from_rtd(self, rt):

        # Formula gleanded from Honeywell RTD datasheet
        r0 = self.sns.c0  # Resistance at 0C
        a = self.sns.c1  # RTD alpha
        g = self.sns.c2  # RTD gamma
        b = self.sns.c3  # RTD beta

        A = a + (a * g / 100)
        B = -a * g / 100 ** 2
        C = -a * b / 100 ** 4

        temperature_c = (-A + math.sqrt(A ** 2 - 4 * B * (1 - rt / r0))) / (2 * B)
        temperature_k = temperature_c + 273.15
        temperature_f = utilities.temp_k_to_f(temperature_k)

        if self._temp_unit == 0:
            return temperature_k
        elif self._temp_unit == 1:
            return temperature_c
        elif self._temp_unit == 2:
            return temperature_f
        else:
            return temperature_k

    def read_conversion_data(self):
        int_ref = 2.50  # ADC internal reference voltage
        # avdd = 3.3
        ch_flgs = [False, False, False, False, True, False, False]
        done = False
        rtd_temperature = 0.0
        ntc_temperature = 0.0
        while not done:
            channel = self.__wait_end_of_conversion(1)
            data_24 = self.__adc_read_register('Data', 3)  # read three conversion bytes
            data_24.pop(0)
            conversion = int.from_bytes(data_24, byteorder='big', signed=False)

            # Temp Sensor Channel
            if channel == 0:
                ch_flgs[0] = True
                rt = (conversion - (2 ** 23)) * self._ref_resistor / (self._adc_gain * (2 ** 23))
                self.logger.debug('cnv=%g res=%g adc_gain=%g rt=%g',
                                  conversion - (2 ** 23),
                                  self._ref_resistor,
                                  self._adc_gain, rt)
                # RTD PT100 or PT1000
                if self._sns_type_id == 1 or self._sns_type_id == 2:
                    rtd_temperature = self.temperature_from_rtd(rt)

                # NTC Thermistor
                elif self._sns_type_id == 3:
                    ntc_temperature = self.temperature_from_ntc_thermistor(rt)

                voltage = rt * self.__adc_exciation_setting_to_current(self._adc_excitation_code)
                dkey = 'adc_counts' + str(self._sens_num)
                self.tlm_dict[dkey] = conversion
                dkey = 'adc_sns_volts' + str(self._sens_num)
                self.tlm_dict[dkey] = voltage
                dkey = 'adc_sns_ohms' + str(self._sens_num)
                self.tlm_dict[dkey] = rt
                dkey = 'rtd' + str(self._sens_num)
                self.tlm_dict[dkey] = rtd_temperature
                dkey = 'adc_ext_therm1' + str(self._sens_num)
                self.tlm_dict[dkey] = ntc_temperature

            # External 10K Thermistor
            elif channel == 1:
                if ch_flgs[6] is True:
                    ch_flgs[1] = True
                    beta = 3570
                    r_at_25 = 10000
                    voltage = (conversion * int_ref) / 2**24
                    itherm = self.tlm_dict['itherm' + str(self._sens_num)]
                    rt = voltage / itherm

                    if conversion > 0:  # avoid divied by zero
                        tempk = (25 + 273.15) * beta / (beta + (25 + 273.15) * (log(rt) - log(r_at_25)))
                    else:
                        tempk = 0
                    dkey = 'adc_ext_therm' + str(self._sens_num)
                    self.tlm_dict[dkey] = tempk

            # IOVDD +
            elif channel == 2:
                ch_flgs[2] = True
                voltage = (conversion * int_ref) / 2**24
                voltage *= 6
                dkey = 'adc_vddio' + str(self._sens_num)
                self.tlm_dict[dkey] = voltage

            # ADC Internal Reference
            elif channel == 3:
                ch_flgs[3] = True
                voltage = (conversion * int_ref) / 2**24
                # voltage *= 6
                dkey = 'adc_ref_volt' + str(self._sens_num)
                self.tlm_dict[dkey] = voltage

            # REFIN1
            elif channel == 4:
                ch_flgs[4] = True
                refin1 = (conversion * int_ref) / 2**24
                dkey = 'refin' + str(self._sens_num)
                self.tlm_dict[dkey] = refin1

            # internal temp reading
            elif channel == 5:
                ch_flgs[5] = True
                temperature = ((float(conversion) - float(0x800000)) / 13584.0)
                dkey = 'adc_int_temp' + str(self._sens_num)
                self.tlm_dict[dkey] = temperature

            # VR8 used for themistor
            elif channel == 6:
                ch_flgs[6] = True
                vr8 = (conversion * int_ref) / 2**24
                dkey = 'itherm' + str(self._sens_num)
                ir8 = vr8/5620
                self.tlm_dict[dkey] = ir8
            else:
                print("bad channel")
                done = True

            if ch_flgs[0] & ch_flgs[1] & ch_flgs[2] & ch_flgs[3] & ch_flgs[4] & ch_flgs[5] & ch_flgs[6] is True:
                done = True

    def adc_set_filter_rate(self, rate):
        reg_dict = self.adc_read_register_to_dict("filter")

        print(rate)

    # </editor-fold>

    # <editor-fold desc="******************* AD7124 Private Methods *******************">

    def __adc_initialize(self):

        self.RegAddrs = quieres.db_table_data_to_dictionary(self.db, 'tblAdcRegisters')
        self.__adc_reset()
        self.__adc_config_channels()
        self.__adc_write_configurations()

        # Configure IOCon1 reg
        dict_io_ctrl_reg1 = quieres.db_adc_fetch_names_n_values(self.db, 'IOCon1', self._sens_num)
        self.__adc_write_register('IOCon1', **dict_io_ctrl_reg1)
        value = self.adc_read_register_to_dict('IOCon1')
        if value['gpio_dat1'] == 0:
            self._ref_resistor = 39200  # R26 on Ref-H
        else:
            self._ref_resistor = 3920  # R2 on Rev-H
        if dict_io_ctrl_reg1 != value:
            print('Error Reading Register')

        # Configure IOCon2 reg
        dict_io_ctrl_reg2 = quieres.db_adc_fetch_names_n_values(self.db, 'IOCon2', self._sens_num)
        self.__adc_write_register('IOCon2', **dict_io_ctrl_reg2)
        value = self.adc_read_register_to_dict('IOCon2')
        if dict_io_ctrl_reg2 != value:
            print('Error Reading Register')

        # Configure Error_En reg
        dict_error_en_reg = quieres.db_adc_fetch_names_n_values(self.db, 'Error_En', self._sens_num)
        self.__adc_write_register('Error_En', **dict_error_en_reg)
        value = self.adc_read_register_to_dict('Error_En')
        if dict_error_en_reg != value:
            print('Error Reading Register')

        # Configure ADC_Control reg
        dict_control_reg = quieres.db_adc_fetch_names_n_values(self.db, 'ADC_Control', self._sens_num)
        self.__adc_write_register('ADC_Control', **dict_control_reg)
        value = self.adc_read_register_to_dict('ADC_Control')
        if dict_control_reg != value:
            print('Error Reading Register')

        # time.sleep(.1)

    def adc_read_register_to_dict(self, reg_name):
        reg_bit_data = quieres.db_adc_register_data_to_dictionary(self.db, reg_name, self._sens_num)
        reg_bytes = self.__search_reg_bytes_from_name(reg_name)
        data_24 = self.__adc_read_register(reg_name, reg_bytes)
        data_24.pop(0)
        value = int.from_bytes(data_24, byteorder='big', signed=False)
        dict_reg = dict()
        for item in reg_bit_data:
            keyname = item['NAME']
            dataval = (value >> item['SHIFT']) & item['MASK']
            dict_reg[keyname] = dataval
        return dict_reg

    def __adc_write_register(self, reg_name, **kwargs):
        reg_dict = quieres.db_adc_register_data_to_dictionary(self.db, reg_name, self._sens_num)
        write_bytes = getbytes_from_reg_bits(kwargs, reg_dict)
        regid = self.__search_reg_address_from_name(reg_name)
        rbytes = write_bytes.to_bytes((write_bytes.bit_length() + 7) // 8, byteorder='big')

        bytelist = [regid]
        for val in rbytes:
            bytelist.append(val)

        self.pins.adc_sel(self.idx)
        self.spi_obj.xfer2(bytelist)

    def __wait_end_of_conversion(self, timeout_s):
        starttime = time.time()
        nready = 1
        data_8 = 0x00
        while nready is 1:
            # data_8 = self.adc_read_status_register()
            data_8 = self.adc_read_register_to_dict('Status')
            nready = data_8['n_rdy']
            currtime = time.time()
            if currtime - starttime > timeout_s:
                print("timeout %f" % (currtime - starttime))
                return -1
        return data_8['ch_active']  # return current channel#

    def __adc_read_register(self, reg_name, byte_len):
        regid = self.__search_reg_address_from_name(reg_name)
        regid |= self._READ_FLAG
        byte_list = [regid]
        for i in range(byte_len):
            byte_list.append(self._DUMMY_BYTE)
        self.pins.adc_sel(self.idx)  # select ADC
        resp = self.spi_obj.xfer2(byte_list)
        return resp

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

    @staticmethod
    def __adc_exciation_setting_to_current(x):
        # constants are from polynomial fit of excitation modes (0 - 5) fit to currents (0, 50, 100, 250, 750, 1000)
        curr = -8.3333*x**5 + 89.5833*x**4 - 312.5000*x**3 + 435.4167*x**2 - 154.1667*x
        return curr/1000000  # convert to uA

    def __adc_config_channels(self):
        try:
            for i in range(16):
                reg_name = 'Channel_' + str(i)
                reg_dict = quieres.db_adc_fetch_names_n_values(self.db, reg_name, self._sens_num)
                self.__adc_write_register(reg_name, **reg_dict)
                result_dict = self.adc_read_register_to_dict(reg_name)
                if reg_dict["enable"] == 1:
                    if result_dict != reg_dict:
                        raise ValueError
        except ValueError as err:
            print(err.args)

    def __adc_write_configurations(self):
        try:
            for i in range(8):
                reg_name = 'Config_' + str(i)
                reg_dict = quieres.db_adc_fetch_names_n_values(self.db, reg_name, self._sens_num)
                self.__adc_write_register(reg_name, **reg_dict)
                result_dict = self.adc_read_register_to_dict(reg_name)
                if result_dict != reg_dict:
                    raise ValueError

        except ValueError as err:
            print(err.args)

    def __adc_reset(self):
        """ Reset the ADC """
        self.pins.adc_sel(self.idx)  # select ADC
        wrbuf = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        self.spi_obj.writebytes(wrbuf)

    # </editor-fold>

# TODO finish development of "adc_set_filter_rate" function