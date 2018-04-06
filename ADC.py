"""
Created on Wed Jan 24 12:49:52 2018

@author: Joe Orndorff - Johns Hopkins University
"""
import spi_bus
import time
import Gbl
from math import log
import RPi.GPIO as GPIO
from Sensor import sensor
import ADC_helper_ftns as AdcHelper

from db import (db_adc_fetch_params, db_table_data_to_dictionary,
                db_adc_fetch_sensor_constants, db_fetch_names_n_values,
                db_adc_register_data_to_dictionary)


class ADC(object):
    """ ADC Class """
    sns = sensor()

    def __init__(self, idx, tlm_dict):
        self._sens_num = idx + 1
        self.tlm_dict = tlm_dict
        self._DUMMY_BYTE = 0xff
        self._READ_FLAG = 0b01000000
        self._adc_gain = 1
        self._therm_resistance = 1000
        self._temp_unit = 'K'
        self._adc_excitation_mode = 1
        self._therm_beta = 3000
        self._sns_type = 'PT1000'
        self._adc_filter = 1
        self._ref_resistor = 1
        self.RegAddrs = []
        self.spi_obj = spi_bus.RPi3Spi(0, idx, 3)
        self.adc_initialize()

    def __delete__(self, instance):
        self.spi_obj.close()

    # <editor-fold desc="******************* Properties *******************">

    # </editor-fold>

    # <editor-fold desc="******************* AD7124 Public Methods *******************">

    def adc_initialize(self):
        # Read database parameters.
        parameters = db_adc_fetch_params(self._sens_num)
        self.__config_adc_params(**parameters)
        const_dict = db_adc_fetch_sensor_constants(self._sns_type)
        self.__adc_config_sensor_constants(**const_dict)
        self.RegAddrs = db_table_data_to_dictionary('tblAdcRegisters')

        # SET GPIO numering mode to use GPIO designation, NOT pin numbers.
        GPIO.setmode(GPIO.BCM)
        # Set SPI0 ADC CS pins high.
        if self._sens_num == 1:
            GPIO.setup(8, GPIO.OUT)  # SPIO-CS0
            GPIO.output(8, 1)
        elif self._sens_num == 2:
            GPIO.setup(7, GPIO.OUT)  # SPI0-CS1
            GPIO.output(7, 1)
        else:
            print("BAD ADC specified")
        self.adc_reset()
        self.adc_config_channels()
        self.adc_write_configurations()

        # Fetch default reg values from db.
        dict_io_ctrl_reg1 = db_fetch_names_n_values('IOCon1', self._sens_num)
        # Write IO Control 1 Register.
        # self.adc_write_register('IOCon1', 'tblAdcIoControl1Reg',**dict_io_ctrl_reg1 )
        self.adc_write_register('IOCon1', **dict_io_ctrl_reg1)
        value = self.adc_read_register('IOCon1')
        print(value)

        # Fetch default reg values from db.
        dict_io_ctrl_reg2 = db_fetch_names_n_values('IOCon2', self._sens_num)
        # Write IO Control 2 Register.
        self.adc_write_register('IOCon2', **dict_io_ctrl_reg2)
        value = self.adc_read_register('IOCon2')
        print(value)

        # Fetch default reg values from db.
        dict_error_en_reg = db_fetch_names_n_values('Error_En', self._sens_num)
        # Write Error Enable Register.
        self.adc_write_register('Error_En', **dict_error_en_reg)
        value = self.adc_read_register('Error_En')
        print(value)

        # Fetch default reg values from db.
        dict_control_reg = db_fetch_names_n_values('ADC_Control', self._sens_num)
        # Write Control Register
        self.adc_write_register('ADC_Control', **dict_control_reg)
        value = self.adc_read_register('ADC_Control')
        print(value)

    def read_conversion_data(self):

        ch_flgs = [False, False, False, False, True, False, False]
        done = False
        while not done:
            channel = self.__wait_end_of_conversion(1)
            data_24 = self.__adc_read_register('Data', 3)
            data_24.pop(0)
            conversion = int.from_bytes(data_24, byteorder='big', signed=False)

            # RTD
            if channel == 0:

                ch_flgs[0] = True
                voltage = (conversion * 1.72) / 2 ** 24

                # r_rtd = voltage / 430e-6
                r_rtd = ((conversion - 2 ** 23) * self._ref_resistor) / (self._adc_gain * 2 ** 23)
                r_rtd *= 10

                dkey = 'adc_counts' + str(self._sens_num)
                self.tlm_dict[dkey] = conversion
                dkey = 'adc_sns_volts' + str(self._sens_num)
                self.tlm_dict[dkey] = voltage
                dkey = 'adc_sns_ohms' + str(self._sens_num)
                self.tlm_dict[dkey] = r_rtd / 10
                # temp = 1.558666E-13x^5 - 5.484495E-10x^4 + 7.077527E-07x^3 - 3.990938E-04x^2
                # + 3.422648E-01^x + 1.503395E+01
                temperature_k = ((self.sns.const_5 * (r_rtd ** 5))
                                 + (self.sns.const_4 * (r_rtd ** 4))
                                 + (self.sns.const_3 * (r_rtd ** 3))
                                 + (self.sns.const_2 * (r_rtd ** 2))
                                 + (self.sns.const_1 * r_rtd)
                                 + self.sns.const_0)
                dkey = 'rtd' + str(self._sens_num)
                self.tlm_dict[dkey] = temperature_k

            # External 10K Thermistor
            elif channel == 1:
                ch_flgs[1] = True
                beta = 3570
                r_at_25 = 10000
                voltage = (conversion * 2.50) / pow(2, 24)
                rt = voltage / 500e-6
                tempk = (25 + 273.15) * beta / (beta + (25 + 273.15) * (log(rt) - log(r_at_25)))
                dkey = 'adc_ext_therm' + str(self._sens_num)
                self.tlm_dict[dkey] = tempk

            # IOVDD +
            elif channel == 2:
                ch_flgs[2] = True
                voltage = (conversion * 2.50) / pow(2, 24)
                voltage *= 6
                dkey = 'adc_vddio' + str(self._sens_num)
                self.tlm_dict[dkey] = voltage

            # AVSS
            elif channel == 3:
                ch_flgs[3] = True
                voltage = (conversion * 2.50) / pow(2, 24)
                voltage *= 6
                dkey = 'adc_avss' + str(self._sens_num)
                self.tlm_dict[dkey] = voltage

            # internal temp reading
            elif channel == 5:
                ch_flgs[5] = True
                temperature_k = ((float(conversion) - float(0x800000)) / 13584.0)
                dkey = 'adc_int_temp' + str(self._sens_num)
                self.tlm_dict[dkey] = temperature_k

            # Ref Voltage
            elif channel == 6:
                ch_flgs[6] = True
                refvolt = (conversion * 3.3) / pow(2, 24)
                dkey = 'adc_ref_volt' + str(self._sens_num)
                self.tlm_dict[dkey] = refvolt
            else:
                print("bad channel")

            if ch_flgs[0] & ch_flgs[1] & ch_flgs[2] & ch_flgs[3] & ch_flgs[4] & ch_flgs[5] & ch_flgs[6] is True:
                done = True

    def adc_config_channels(self):
        print("Before Ch Programming")
        for i in range(7):
            data_32 = self.__adc_read_register("Channel_" + str(i), 2)
            data_32.pop(0)
            print(data_32)

        # CH0 - PT1000
        input_p = AdcHelper.InputSel['AIN1Input']
        input_n = AdcHelper.InputSel['AIN4Input']
        self.adc_write_register('Channel_0', ainp=input_p, ainm=input_n, setup=0, enable=True)
        value = self.adc_read_channel_regs('Channel_0')
        print(value)

        # CH1 - RT1 Thermistor
        input_p = AdcHelper.InputSel['AIN5Input']
        input_n = AdcHelper.InputSel['AIN6Input']
        self.adc_write_register('Channel_1', ainp=input_p, ainm=input_n, setup=1, enable=True)
        value = self.adc_read_channel_regs('Channel_1')
        print(value)

        # CH2 - IOVDD
        input_p = AdcHelper.InputSel['IOVDD6PInput']
        input_n = AdcHelper.InputSel['IOVDD6MInput']
        self.adc_write_register('Channel_2', ainp=input_p, ainm=input_n, setup=1, enable=True)
        value = self.adc_read_channel_regs('Channel_2')
        print(value)

        # CH2 - AVDD
        input_p = AdcHelper.InputSel['AVDD6PInput']
        input_n = AdcHelper.InputSel['AVDD6MInput']
        self.adc_write_register('Channel_3',  ainp=input_p, ainm=input_n, setup=1, enable=True)
        value = self.adc_read_channel_regs('Channel_3')
        print(value)

        # CH5 - Internal Sensor.
        input_p = AdcHelper.InputSel['TEMPInput']
        input_n = AdcHelper.InputSel['AVSSInput']
        self.adc_write_register('Channel_5', ainp=input_p, ainm=input_n, setup=3, enable=True)
        value = self.adc_read_channel_regs('Channel_5')
        print(value)

        # CH6 - Regerence In
        input_p = AdcHelper.InputSel['REFInput']
        input_n = AdcHelper.InputSel['AIN7Input']
        self.adc_write_register('Channel_6' , ainp=input_p, ainm=input_n, setup=2, enable=True)
        value = self.adc_read_channel_regs('Channel_6')
        print(value)
        print("After Ch Programming")

    def adc_write_configurations(self):
        burnoutid = AdcHelper.BurnoutCurrent['BurnoutOff']

        refid = AdcHelper.RefSel['RefIn1']
        gain = AdcHelper.select_gain_to_strings(self._adc_gain)
        pgaid = AdcHelper.PgaSel[gain]
        self.adc_write_register('Config_0',
                                pga=pgaid, ref_sel=refid, ain_bufm=True, ain_bufp=True,
                                ref_bufm=True, ref_bufp=True, burnout=burnoutid, bipolar=True)
        value = self.adc_read_configuration_regs('Config_0')
        print(value)

        pgaid = AdcHelper.PgaSel['Pga1']
        refid = AdcHelper.RefSel['RefInternal']
        self.adc_write_register('Config_1',
                                pga=pgaid, ref_sel=refid, ain_bufm=True, ain_bufp=True,
                                ref_bufm=True, ref_bufp=True, burnout=burnoutid, bipolar=False)
        value = self.adc_read_configuration_regs('Config_1')
        print(value)

        pgaid = AdcHelper.PgaSel['Pga1']
        refid = AdcHelper.RefSel['RefAVdd']
        self.adc_write_register('Config_2',
                                pga=pgaid, ref_sel=refid, ain_bufm=True, ain_bufp=True,
                                ref_bufm=True, ref_bufp=True, burnout=burnoutid, bipolar=False)
        value = self.adc_read_configuration_regs('Config_2')
        print(value)

        pgaid = AdcHelper.PgaSel['Pga1']
        refid = AdcHelper.RefSel['RefInternal']
        burnoutid = AdcHelper.BurnoutCurrent['BurnoutOff']
        self.adc_write_register('Config_3',
                                pga=pgaid, ref_sel=refid, ain_bufm=True, ain_bufp=True,
                                ref_bufm=True, ref_bufp=True, burnout=burnoutid, bipolar=True)
        value = self.adc_read_configuration_regs('Config_3')
        print(value)

    def adc_read_configuration_regs(self, config_name):
        reg_bit_data = db_adc_register_data_to_dictionary('Config_0', self._sens_num)
        data_16 = self.__adc_read_register(config_name, 2)
        data_16.pop(0)
        value = int.from_bytes(data_16, byteorder='big', signed=False)
        dict_reg = dict()
        for item in reg_bit_data:
            keyname = item['NAME']
            dataval = (value >> item['SHIFT']) & item['MASK']
            dict_reg[keyname] = dataval
        return dict_reg

    def adc_read_channel_regs(self, ch_name):
        data_16 = self.__adc_read_register(ch_name, 2)
        data_16.pop(0)
        value = int.from_bytes(data_16, byteorder='big', signed=False)
        reg_bit_data = db_adc_register_data_to_dictionary('Channel_0', self._sens_num)
        dict_adc_channel_regs = dict()
        for item in reg_bit_data:
            keyname = item['NAME']
            dataval = (value >> item['SHIFT']) & item['MASK']
            dict_adc_channel_regs[keyname] = dataval
        return dict_adc_channel_regs

    def adc_read_filter_regs(self, filter_name):
        data_24 = self.__adc_read_register(filter_name, 3)
        data_24.pop(0)
        value = int.from_bytes(data_24, byteorder='big', signed=False)
        reg_bit_data = db_adc_register_data_to_dictionary('ADC_Control', self._sens_num)
        dict_adc_cntrl_reg = dict()
        for item in reg_bit_data:
            keyname = item['NAME']
            dataval = (value >> item['SHIFT']) & item['MASK']
            dict_adc_cntrl_reg[keyname] = dataval
        return dict_adc_cntrl_reg

    def adc_set_filter_rate(self, rate):
        print(rate)


    def adc_reset(self):
        """ Reset the ADC """
        wrbuf = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        self.spi_obj.writebytes(wrbuf)

    def adc_write_register(self, reg_name,  **kwargs):
        reg_dict = db_adc_register_data_to_dictionary(reg_name, self._sens_num)
        write_bytes = self.__adc_getbytes_from_reg_bits(kwargs, reg_dict)
        regid = self.__search_reg_address_from_name(reg_name)
        rbytes = write_bytes.to_bytes((write_bytes.bit_length() + 7) // 8, byteorder='big')

        bytelist = [regid]
        for val in rbytes:
            bytelist.append(val)
        self.spi_obj.xfer2(bytelist)

    def adc_read_register(self, reg_name):
        reg_bit_data = db_adc_register_data_to_dictionary(reg_name, self._sens_num)
        bytes = self.__search_reg_bytes_from_name(reg_name)
        data_24 = self.__adc_read_register(reg_name, bytes)
        data_24.pop(0)
        value = int.from_bytes(data_24, byteorder='big', signed=False)
        dict_reg = dict()
        for item in reg_bit_data:
            keyname = item['NAME']
            dataval = (value >> item['SHIFT']) & item['MASK']
            dict_reg[keyname] = dataval
        return dict_reg

    # </editor-fold>

    # <editor-fold desc="******************* AD7124 Private Methods *******************">

    def __wait_end_of_conversion(self, timeout_s):
        starttime = time.time()
        nready = 1
        data_8 = 0x00
        while nready is 1:
            # data_8 = self.adc_read_status_register()
            data_8 = self.adc_read_register('Status')
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
        resp = self.spi_obj.xfer2(byte_list)
        return resp

    def __config_adc_params(self, **kwargs):

            current = kwargs['excitation_curr_uA']
            # self._adc_excitation_mode = Gbl.ExcitationCurrents.get(current, 0)
            self._temp_unit = kwargs['temperature_unit']
            self._sns_type = kwargs['sensor_type']
            self._adc_filter = kwargs['filter']
            self._therm_resistance = kwargs['therm_resistance']
            self._therm_beta = kwargs['therm_beta']
            self._adc_gain = kwargs['gain']
            self._ref_resistor = kwargs['ref_resistor']

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

    def __adc_getbytes_from_reg_bits(self, kwargs, reg_dict):
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

    def __adc_config_sensor_constants(self, **kwargs):

                self.sns.sensor_type = kwargs['Device']
                self.sns.const_0 = kwargs['C0']
                self.sns.const_1 = kwargs['C1']
                self.sns.const_2 = kwargs['C2']
                self.sns.const_3 = kwargs['C3']
                self.sns.const_4 = kwargs['C4']
                self.sns.const_5 = kwargs['C5']
                self.sns.const_6 = kwargs['C6']
                self.sns.const_7 = kwargs['C7']

    # </editor-fold>
