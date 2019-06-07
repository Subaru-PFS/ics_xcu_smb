import logging
import time
import math

import numpy as np

from Sensor import sensor
import utilities
from utilities import getbytes_from_reg_bits
import quieres

import Gbl

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

    def __init__(self, idx, smbdb, tlm_dict, spi_obj, io, logLevel=logging.INFO):
        self.logger = logging.getLogger('ADC_%02d' % (idx))
        self.logger.setLevel(logLevel)
        self.pins = io
        self.db = smbdb
        self.idx = idx  # index of ADC (0 to 11)
        self._sens_num = idx + 1  # Sensor number (1 to 12)
        parameters = quieres.db_adc_fetch_params(self.db, self._sens_num)  # ID, units, sensor type, gain
        self.activeAchannels = []
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

        self.lastReading = np.nan
        
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
        switcher = {
            0: 0,
            1: 1,
            2: 2,
            3: 4,
            4: 5,
            5: 7
        }
        reg_name = 'Filter_0'  # filter 0 is RTD channel

        with Gbl.ioLock:
            reg_dict = self.adc_read_register_to_dict(reg_name)
            reg_dict["filter"] = switcher.get(value, 0)
            self.__adc_write_register(reg_name, **reg_dict)

        self._adc_filter = value
        quieres.db_adc_update_register_field(self.db, 'filter', self._sens_num, value)

    def set_post_filter_type(self, value):
        switcher = {
            0: 2,
            1: 3,
            2: 5,
            3: 6,
        }
        reg_name = 'Filter_0'  # filter 0 is RTD channel

        with Gbl.ioLock:
            reg_dict = self.adc_read_register_to_dict(reg_name)
            reg_dict["post_filter"] = switcher.get(value, 0)
            self.__adc_write_register(reg_name, **reg_dict)
            self._adc_filter = value
        quieres.db_adc_update_register_field(self.db, 'post_filter', self._sens_num, value)

    def adc_set_temp_units(self, value):
        quieres.db_update_adc_params(self.db, value, 'temperature_unit', self._sens_num)
        self._temp_unit = value

    def adc_set_sensor_type(self, value):
        switcher = {
            1: 1,
            2: 0,
            3: 0,
        }

        quieres.db_update_adc_params(self.db, value, 'sensor_type', self._sens_num)
        dat1 = switcher.get(value, 1)

        with Gbl.ioLock:
            reg_dict = self.adc_read_register_to_dict('IOCon1')
            reg_dict['gpio_dat1'] = dat1
            self.__adc_write_register('IOCon1', **reg_dict)
            self._sns_type_id = value
        quieres.db_adc_update_register_field(self.db, 'gpio_dat1', self._sens_num, dat1)

    def adc_set_sensor_wiring(self, value):
        reg_name = "IOCon1"

        with Gbl.ioLock:
            reg_dict = self.adc_read_register_to_dict(reg_name)
            reg_dict["pdsw"] = value
            self.__adc_write_register(reg_name, **reg_dict)
        quieres.db_adc_update_register_field(self.db, 'pdsw', self._sens_num, value)

    def set_exciatation_current(self, value):
        reg_name = "IOCon1"

        with Gbl.ioLock:
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

        try:
            temperature_c = (-A + math.sqrt(A ** 2 - 4 * B * (1 - rt / r0))) / (2 * B)
        except ValueError:
            self.logger.warn('conversion error for %s, sns=%s', rt, self.sns)
            temperature_c = np.nan
        temperature_k = temperature_c + 273.15

        if self._temp_unit == 0:
            return temperature_k
        elif self._temp_unit == 1:
            return temperature_c
        elif self._temp_unit == 2:
            temperature_f = utilities.temp_k_to_f(temperature_k)
            return temperature_f
        else:
            return temperature_k

    def read_conversion_data(self):
        int_ref = 2.50  # ADC internal reference voltage
        # avdd = 3.3
        ch_flgs = [not(active) for active in self.activeChannels]
        done = False
        rtd_temperature = 0.0
        ntc_temperature = 0.0

        # Split this into an acquire and a process step? Drop several of these channela?
        while not done:
            with Gbl.ioLock:
                channel = self.__wait_end_of_conversion(1)
                data_24 = self.__adc_read_register('Data', 3)  # read three conversion bytes
            self.logger.debug('conversion %d %d %s', self.idx, channel, data_24)
            data_24.pop(0)
            conversion = int.from_bytes(data_24, byteorder='big', signed=False)

            # Temp Sensor Channel
            if channel == 0:
                ch_flgs[0] = True
                if conversion == 2**24-1:
                    conversion = np.nan
                rt = (conversion - (2 ** 23)) * self._ref_resistor / (self._adc_gain * (2 ** 23))
                self.logger.debug('cnv=%g res=%g adc_gain=%g rt=%g type=%d',
                                  conversion - (2 ** 23),
                                  self._ref_resistor,
                                  self._adc_gain, rt,
                                  self._sns_type_id)
                # RTD PT100 or PT1000
                if self._sns_type_id == 1 or self._sns_type_id == 2:
                    rtd_temperature = self.temperature_from_rtd(rt)

                    if (rtd_temperature <= 1 or rtd_temperature > 380
                        or np.isfinite(self.lastReading) and abs(rtd_temperature - self.lastReading) > 30):
                        
                        self.logger.warning('ADC %d: replacing out-of-range reading %s with %s',
                                            self._sens_num, rtd_temperature, self.lastReading)
                        rtd_temperature = self.lastReading
                        self.lastReading = np.nan
                    else:
                        self.lastReading = rtd_temperature

                    dkey = 'rtd' + str(self._sens_num)
                    self.tlm_dict[dkey] = rtd_temperature

                # NTC Thermistor
                elif self._sns_type_id == 3:
                    ntc_temperature = self.temperature_from_ntc_thermistor(rt)
                    dkey = 'adc_ext_therm1' + str(self._sens_num)
                    self.tlm_dict[dkey] = ntc_temperature

                # Engineering units
                voltage = rt * self.__adc_exciation_setting_to_current(self._adc_excitation_code)
                dkey = 'adc_counts' + str(self._sens_num)
                self.tlm_dict[dkey] = conversion
                dkey = 'adc_sns_volts' + str(self._sens_num)
                self.tlm_dict[dkey] = voltage
                dkey = 'adc_sns_ohms' + str(self._sens_num)
                self.tlm_dict[dkey] = rt

            # External 10K Thermistor
            elif channel == 1:
                if ch_flgs[6] is True:
                    ch_flgs[1] = True
                    beta = 3570
                    r_at_25 = 10000
                    voltage = (conversion * int_ref) / 2**24
                    itherm = self.tlm_dict['itherm' + str(self._sens_num)]
                    dkey = 'adc_ext_therm' + str(self._sens_num)

                    try:
                        rt = voltage / itherm
                        tempk = (25 + 273.15) * beta / (beta + (25 + 273.15) * (math.log(rt) - math.log(r_at_25)))
                    except ZeroDivisionError:
                        self.logger.warn('conversion error on external thermistor. conv=%s voltage=%s int_ref=%s itherm=%s',
                                         conversion, voltage, int_ref, itherm)
                        tempk = self.tlm_dict[dkey]  # Use previous reading
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
                if conversion == 0:
                    self.logger.warn('ADC %d: VR8 is 0', self.idx)
                vr8 = (conversion * int_ref) / 2**24
                dkey = 'itherm' + str(self._sens_num)
                ir8 = vr8/5620
                self.tlm_dict[dkey] = ir8
            else:
                self.logger.warn("bad channel: %s", channel)
                done = True

            if all(ch_flgs):
                done = True

    def adc_set_filter_rate(self, rate):
        reg_dict = self.adc_read_register_to_dict("filter")

        print(rate)

    # </editor-fold>

    # <editor-fold desc="******************* AD7124 Private Methods *******************">

    def __adc_initialize(self):

        with Gbl.ioLock:
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
                self.logger.warn('Error Reading IOCon1 Register: expected %s vs %s' % (dict_io_ctrl_reg1, value))

            # Configure IOCon2 reg
            dict_io_ctrl_reg2 = quieres.db_adc_fetch_names_n_values(self.db, 'IOCon2', self._sens_num)
            self.__adc_write_register('IOCon2', **dict_io_ctrl_reg2)
            value = self.adc_read_register_to_dict('IOCon2')
            if dict_io_ctrl_reg2 != value:
                self.logger.warn('Error Reading IOCon2 Register: expected %s vs %s' % (dict_io_ctrl_reg2, value))

            # Configure Error_En reg
            dict_error_en_reg = quieres.db_adc_fetch_names_n_values(self.db, 'Error_En', self._sens_num)
            self.__adc_write_register('Error_En', **dict_error_en_reg)
            value = self.adc_read_register_to_dict('Error_En')
            if dict_error_en_reg != value:
                self.logger.warn('Error Reading Error_En Register: expected %s vs %s' % (dict_error_en_reg, value))

            # Configure ADC_Control reg
            dict_control_reg = quieres.db_adc_fetch_names_n_values(self.db, 'ADC_Control', self._sens_num)
            self.__adc_write_register('ADC_Control', **dict_control_reg)
            value = self.adc_read_register_to_dict('ADC_Control')
            if dict_control_reg != value:
                self.logger.warn('Error Reading ADC_Control Register: expected %s vs %s' % (dict_control_reg, value))

    def adc_read_register_to_dict(self, reg_name, muffleLog=False):
        reg_bit_data = quieres.db_adc_register_data_to_dictionary(self.db, reg_name, self._sens_num)
        reg_bytes = self.__search_reg_bytes_from_name(reg_name)
        data_24 = self.__adc_read_register(reg_name, reg_bytes, muffleLog=muffleLog)
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

        with Gbl.ioLock:
            self.logger.debug('adc_writing %02d %s 0x%04x', self.idx, reg_name, write_bytes)
            self.pins.adc_sel(self.idx)
            self.spi_obj.xfer2(bytelist)

    def log_errors(self):
        errors = self.adc_read_register_to_dict('Error')
        self.logger.error("errors=%s" % (errors))
        
    def __wait_end_of_conversion(self, timeout_s):
        starttime = time.time()
        nready = 1
        data_8 = 0x00
        while nready == 1:
            # data_8 = self.adc_read_status_register()
            data_8 = self.adc_read_register_to_dict('Status', muffleLog=True)
            nready = data_8['n_rdy']
            currtime = time.time()
            if currtime - starttime > timeout_s:
                self.logger.warn("timeout %f, data=%s" % (currtime - starttime, data_8))
                self.log_errors()
                return -1
        return data_8['ch_active']  # return current channel#

    def __adc_read_register(self, reg_name, byte_len, muffleLog=False):
        regid = self.__search_reg_address_from_name(reg_name)
        regid |= self._READ_FLAG
        byte_list = [regid]
        for i in range(byte_len):
            byte_list.append(self._DUMMY_BYTE)
        with Gbl.ioLock:
            self.pins.adc_sel(self.idx)  # select ADC
            resp = self.spi_obj.xfer2(byte_list)
        if not muffleLog:
            self.logger.debug('adc_readreg %02d %s %s', self.idx, reg_name, ["0x%02x" % b for b in resp])
        
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
            self.activeChannels = []
            for i in range(16):
                reg_name = 'Channel_' + str(i)
                reg_dict = quieres.db_adc_fetch_names_n_values(self.db, reg_name, self._sens_num)
                with Gbl.ioLock:
                    self.__adc_write_register(reg_name, **reg_dict)
                    result_dict = self.adc_read_register_to_dict(reg_name)
                self.activeChannels.append(reg_dict["enable"] == 1)
                if reg_dict["enable"] == 1:
                    if result_dict != reg_dict:
                        raise ValueError("ADC %d channel %d configuration mismatch; expected %s got %s" % (self.idx,
                                                                                                           i, reg_dict,
                                                                                                           result_dict))
                                         
        except ValueError as err:
            self.logger.warn(err.args)

    def __adc_write_configurations(self):
        try:
            for i in range(8):
                reg_name = 'Config_' + str(i)
                reg_dict = quieres.db_adc_fetch_names_n_values(self.db, reg_name, self._sens_num)
                with Gbl.ioLock:
                    self.__adc_write_register(reg_name, **reg_dict)
                    result_dict = self.adc_read_register_to_dict(reg_name)
                if result_dict != reg_dict:
                    raise ValueError("ADC %d configuration %d mismatch; expected %s got %s" % (self.idx,
                                                                                               i, reg_dict, result_dict))

        except ValueError as err:
            self.logger.warn(err.args)

    def __adc_reset(self):
        """ Reset the ADC """
        with Gbl.ioLock:
            self.pins.adc_sel(self.idx)  # select ADC
            wrbuf = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
            self.spi_obj.writebytes(wrbuf)

    # </editor-fold>

# TODO finish development of "adc_set_filter_rate" function
