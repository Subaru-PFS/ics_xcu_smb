"""
Created on Wed Jan 24 12:49:52 2018

@author: pi
"""
import spi_bus
import time
import Gbl
import AD7124_Reg_Addresses as RegAddrs
from math import log
import RPi.GPIO as GPIO
from Sensor import sensor
import ADC_helper_ftns as AdcHelper
import sqlite3


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
        self.spi_obj = spi_bus.RPi3Spi(0, idx, 3)
        self.adc_initialize()

    def __delete__(self, instance):
        self.spi_obj.close()

    # <editor-fold desc="*************** Properties*******************">


    # </editor-fold>

    # <editor-fold desc="************* AD7124 Public Methods ********************">

    def adc_initialize(self):
        """ Read database parameters """
        self.__get_adc_params_from_db()
        self.__get_sensor_constants_from_db()

        """ SET GPIO numering mode to use GPIO designation, NOT pin numbers """
        GPIO.setmode(GPIO.BCM)
        """ Set SPI0 ADC CS pins high """
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
        """ Write IO Control 1 Register """
        iout0_ch = RegAddrs.IoutCh['IoutCh0']
        iout1_ch = RegAddrs.IoutCh['IoutCh5']
        iout0 = RegAddrs.IoutCurrent['Current500ua']
        iout1 = RegAddrs.IoutCurrent['Current500ua']
        self.adc_write_io_control_1_reg(iout0_ch=iout0_ch, iout1_ch=iout1_ch, iout0=iout0,
                                        iout1=iout1, pdsw=False, gpio_ctrl1=True, gpio_ctrl2=False,
                                        gpio_dat1=False, gpio_dat2=False)

        value = self.adc_read_io_control_1_reg()
        print(value)

        self.adc_write_io_control_2_reg(vbias0=False, vbias1=False, vbias2=False, vbias3=False, vbias4=False,
                                        vbias5=False, vbias6=False, vbias7=False)
        value = self.adc_read_io_control_2_reg()
        print(value)

        self.adc_write_error_en_reg()

        mode = RegAddrs.OperatingMode['ContinuousMode']
        power_mode = RegAddrs.PowerMode['FullPower']
        clk_sel = RegAddrs.ClkSel['InternalClk']
        self.adc_write_adc_control_reg(clk_sel=clk_sel, mode=mode, power_mode=power_mode,
                                       ref_en=True, n_cs_en=True, data_status=False,
                                       cont_read=False, dout_n_rdy_del=True)
        value = self.adc_read_adc_control_reg()
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

        """ CH0 - PT1000"""
        input_p = RegAddrs.InputSel['AIN1Input']
        input_n = RegAddrs.InputSel['AIN4Input']
        self.adc_write_channel_regs(ch_name='Channel_0', ainp=input_p, ainm=input_n, setup=0, enable=True)
        value = self.adc_read_channel_regs('Channel_0')
        print(value)

        """ CH1 - RT1 Thermistor """
        input_p = RegAddrs.InputSel['AIN5Input']
        input_n = RegAddrs.InputSel['AIN6Input']
        self.adc_write_channel_regs(ch_name='Channel_1', ainp=input_p, ainm=input_n, setup=1, enable=True)
        value = self.adc_read_channel_regs('Channel_1')
        print(value)

        """ CH2 - IOVDD """
        input_p = RegAddrs.InputSel['IOVDD6PInput']
        input_n = RegAddrs.InputSel['IOVDD6MInput']
        self.adc_write_channel_regs(ch_name='Channel_2', ainp=input_p, ainm=input_n, setup=1, enable=True)
        value = self.adc_read_channel_regs('Channel_2')
        print(value)

        """ CH2 - AVDD """
        input_p = RegAddrs.InputSel['AVDD6PInput']
        input_n = RegAddrs.InputSel['AVDD6MInput']
        self.adc_write_channel_regs(ch_name='Channel_3', ainp=input_p, ainm=input_n, setup=1, enable=True)
        value = self.adc_read_channel_regs('Channel_3')
        print(value)

        """ CH5 - Internal Sensor """
        input_p = RegAddrs.InputSel['TEMPInput']
        input_n = RegAddrs.InputSel['AVSSInput']
        self.adc_write_channel_regs(ch_name='Channel_5', ainp=input_p, ainm=input_n, setup=3, enable=True)
        value = self.adc_read_channel_regs('Channel_5')
        print(value)

        """ CH6 - Regerence In """
        input_p = RegAddrs.InputSel['REFInput']
        input_n = RegAddrs.InputSel['AIN7Input']
        self.adc_write_channel_regs(ch_name='Channel_6', ainp=input_p, ainm=input_n, setup=2, enable=True)
        value = self.adc_read_channel_regs('Channel_6')
        print(value)
        print("After Ch Programming")

    def adc_write_configurations(self):
        burnoutid = RegAddrs.BurnoutCurrent['BurnoutOff']

        refid = RegAddrs.RefSel['RefIn1']
        gain = AdcHelper.select_gain_to_strings(self._adc_gain)
        pgaid = RegAddrs.PgaSel[gain]
        self.adc_write_configuration_reg(cfgname='Config_0', pga=pgaid, ref_sel=refid, ain_bufm=True, ain_bufp=True,
                                         ref_bufm=True, ref_bufp=True, burnout=burnoutid, bipolar=True)
        value = self.adc_read_configuration_reg('Config_0')
        print(value)

        pgaid = RegAddrs.PgaSel['Pga1']
        refid = RegAddrs.RefSel['RefInternal']
        self.adc_write_configuration_reg(cfgname='Config_1', pga=pgaid, ref_sel=refid, ain_bufm=True, ain_bufp=True,
                                         ref_bufm=True, ref_bufp=True,  burnout=burnoutid, bipolar=False)
        value = self.adc_read_configuration_reg('Config_1')
        print(value)

        pgaid = RegAddrs.PgaSel['Pga1']
        refid = RegAddrs.RefSel['RefAVdd']
        self.adc_write_configuration_reg(cfgname='Config_2',  pga=pgaid, ref_sel=refid, ain_bufm=True, ain_bufp=True,
                                         ref_bufm=True, ref_bufp=True, burnout=burnoutid, bipolar=False)
        value = self.adc_read_configuration_reg('Config_2')
        print(value)

        pgaid = RegAddrs.PgaSel['Pga1']
        refid = RegAddrs.RefSel['RefInternal']
        burnoutid = RegAddrs.BurnoutCurrent['BurnoutOff']
        self.adc_write_configuration_reg(cfgname='Config_3', pga=pgaid, ref_sel=refid, ain_bufm=True, ain_bufp=True,
                                         ref_bufm=True, ref_bufp=True, burnout=burnoutid, bipolar=True)
        value = self.adc_read_configuration_reg('Config_3')
        print(value)

    def adc_write_io_control_1_reg(self, **kwargs):
        reg_dict = self.__adc_retrieve_reg_bits_from_db('tblAdcIoControl1Reg')
        write_bytes = self.__adc_getbytes_from_reg_bits(kwargs, reg_dict)
        return self.__adc_write_register('IOCon1', write_bytes)

    def adc_read_io_control_1_reg(self):
        data_24 = self.__adc_read_register('IOCon1', 3)
        data_24.pop(0)
        value = int.from_bytes(data_24, byteorder='big', signed=False)
        reg_dict = dict()
        reg_dict['value'] = value
        reg_dict['iout0_ch'] = value & 0x00000f
        reg_dict['iout1_ch'] = (value >> 4) & 0x00000f
        reg_dict['iout0'] = (value >> 8) & 0x000007
        reg_dict['iout1'] = (value >> 11) & 0x000007
        reg_dict['pdsw'] = (value >> 15) & 0x000001
        reg_dict['gpio_ctrl1'] = (value >> 18) & 0x000001
        reg_dict['gpio_ctrl2'] = (value >> 19) & 0x000001
        reg_dict['gpio_dat1'] = (value >> 22) & 0x000001
        reg_dict['gpio_dat2'] = (value >> 23) & 0x000001
        return reg_dict

    def adc_write_io_control_2_reg(self, **kwargs):
        reg_dict = self.__adc_retrieve_reg_bits_from_db('tblAdcIoControl2Reg')
        write_bytes = self.__adc_getbytes_from_reg_bits(kwargs, reg_dict)
        return self.__adc_write_register('IOCon2', write_bytes)

    def adc_read_io_control_2_reg(self):
        data_24 = self.__adc_read_register('IOCon2', 2)
        data_24.pop(0)
        value = int.from_bytes(data_24, byteorder='big', signed=False)
        reg_dict = dict()
        reg_dict['value'] = value
        reg_dict['vbias0'] = value & 0b0000000000000001
        reg_dict['vbias1'] = value & 0b0000000000000010
        reg_dict['vbias2'] = value & 0b0000000000010000
        reg_dict['vbias3'] = value & 0b0000000000100000
        reg_dict['vbias4'] = value & 0b0000010000000000
        reg_dict['vbias5'] = value & 0b0000100000000000
        reg_dict['vbias6'] = value & 0b0100000000000000
        reg_dict['vbias7'] = value & 0b1000000000000000
        return reg_dict

    def adc_write_adc_control_reg(self, **kwargs):
        reg_dict = self.__adc_retrieve_reg_bits_from_db('tblAdcAdcControlReg')
        write_bytes = self.__adc_getbytes_from_reg_bits(kwargs, reg_dict)
        return self.__adc_write_register('ADC_Control', write_bytes)

    def adc_read_adc_control_reg(self):
        data_24 = self.__adc_read_register('ADC_Control', 2)
        data_24.pop(0)
        value = int.from_bytes(data_24, byteorder='big', signed=False)
        reg_dict = dict()
        reg_dict['value'] = value
        reg_dict['clk_sel'] = value & 0x0003
        reg_dict['mode'] = (value >> 2) & 0x000F
        reg_dict['power_mode'] = (value >> 6) & 0x0003
        reg_dict['ref_en'] = (value >> 8) & 0x0001
        reg_dict['cs_en'] = (value >> 9) & 0x0001
        reg_dict['data_status'] = (value >> 10) & 0x0001
        reg_dict['cont_read'] = (value >> 11) & 0x0001
        reg_dict['dout_rdy_del'] = (value >> 12) & 0x0001
        return reg_dict

    def adc_write_configuration_reg(self, **kwargs):
        reg_dict = self.__adc_retrieve_reg_bits_from_db('tblAdcConfigurationRegs')
        write_bytes = self.__adc_getbytes_from_reg_bits(kwargs, reg_dict)
        return self.__adc_write_register(kwargs['cfgname'], write_bytes)

    def adc_read_configuration_reg(self, config_name):
        data_24 = self.__adc_read_register(config_name, 2)
        data_24.pop(0)
        value = int.from_bytes(data_24, byteorder='big', signed=False)
        reg_dict = dict()
        reg_dict['value'] = value
        reg_dict['PGA'] = value & 0x0007
        reg_dict['ref_sel'] = (value >> 3) & 0x0003
        reg_dict['ain_bufm'] = (value >> 5) & 0x0001
        reg_dict['ain_bufp'] = (value >> 6) & 0x0001
        reg_dict['ref_bufm'] = (value >> 7) & 0x0001
        reg_dict['burnout'] = (value >> 9) & 0x0003
        reg_dict['bipolar'] = (value >> 11) & 0x0001
        return reg_dict

    def enable_channel(self, ch_name, enable):
        """
        :brief sets the AD7124 channel enable status
        value is also stored in software register list of the device.
        :param ch_name: uint8_t internal channel to select
        :param enable: bool enable channel
        :return: int esult from write operation.
        """
        data_32 = self.__adc_read_register(ch_name, 3)
        value = int.from_bytes(data_32, byteorder='big', signed=False)
        if value < 0:
            return value
        if enable is True:
            value |= b.AD7124_CH_MAP_REG_CH_ENABLE()
        else:
            value &= ~b.AD7124_CH_MAP_REG_CH_ENABLE()
        return self.__adc_write_register(ch_name, value)

    def adc_write_channel_regs(self, **kwargs):
        regid = RegAddrs.search_reg_address_from_name(kwargs['ch_name'])
        if regid > 0:
            reg_dict = self.__adc_retrieve_reg_bits_from_db('tblAdcChannelRegs')
            write_bytes = self.__adc_getbytes_from_reg_bits(kwargs, reg_dict)
            return self.__adc_write_register(kwargs['ch_name'], write_bytes)
        else:
            return -1

    def adc_read_channel_regs(self, ch_name):
        data_24 = self.__adc_read_register(ch_name, 2)
        data_24.pop(0)
        value = int.from_bytes(data_24, byteorder='big', signed=False)
        reg_dict = dict()
        reg_dict['value'] = value
        reg_dict['ainm'] = value & 0x000f
        reg_dict['ainp'] = (value >> 4) & 0x000f
        reg_dict['setup'] = value >> 12 & 0x000f
        reg_dict['enable'] = value >> 15 & 0x0001
        return reg_dict

    def adc_read_error_register(self):
        data_24 = self.__adc_read_register('Error', 3)
        data_24.pop(0)
        value = int.from_bytes(data_24, byteorder='big', signed=False)
        reg_dict = dict()
        reg_dict['value'] = value
        reg_dict['rom_crc_err'] = value & 0x0001
        reg_dict['mm_crc_err'] = (value >> 1) & 0x0001
        reg_dict['spi_crc_err'] = (value >> 2) & 0x0001
        reg_dict['spi_write_err'] = (value >> 3) & 0x0001
        reg_dict['spi_read_err'] = (value >> 4) & 0x0001
        reg_dict['spi_clk_cnt_err'] = (value >> 5) & 0x0001
        reg_dict['spi_ignore_err'] = (value >> 6) & 0x0001
        reg_dict['aldo_psm_error'] = (value >> 7) & 0x0001
        reg_dict['dldo_psm_err'] = (value >> 9) & 0x0001
        reg_dict['ref_det_err'] = (value >> 11) & 0x0001
        reg_dict['ainm_uv_err'] = (value >> 12) & 0x0001
        reg_dict['ainm_ov_err'] = (value >> 13) & 0x0001
        reg_dict['ainp_uv_err'] = (value >> 14) & 0x0001
        reg_dict['ainp_ov_err'] = (value >> 15) & 0x0001
        reg_dict['adc_sat_err'] = (value >> 16) & 0x0001
        reg_dict['adc_conv_err'] = (value >> 17) & 0x0001
        reg_dict['adc_cal_err'] = (value >> 18) & 0x0001
        reg_dict['ldo_cap_err'] = (value >> 19) & 0x0001

        return reg_dict

    def adc_read_status_register(self):
        data_8 = self.__adc_read_register('Status', 1)
        data_8.pop(0)
        value = int.from_bytes(data_8, byteorder='big', signed=False)
        reg_dict = dict()
        reg_dict['value'] = value
        reg_dict['ch_active'] = value & 0x0f
        reg_dict['por_flag'] = (value >> 4) & 0x01
        reg_dict['err'] = (value >> 6) & 0x01
        reg_dict['n_rdy'] = (value >> 7) & 0x01
        return reg_dict

    def adc_write_error_en_reg(self):
        self.__adc_write_register('Error_En', 0x7F018)

    def adc_write_filter_reg(self, **kwargs):
        cfilter = RegAddrs.FilterType[kwargs['filter_type_name']]
        postfilter = RegAddrs.PostFilterType[kwargs['postfilter_name']]

        reg_dict = self.__adc_retrieve_reg_bits_from_db('tblAdcFilterRegs')
        write_bytes = self.__adc_getbytes_from_reg_bits(kwargs, reg_dict)
        return self.__adc_write_register(kwargs['filter_name'], write_bytes)

    def adc_write_gain_reg(self, gain_ch_name, gain):
        """
        :brief Sets the AD7124 Filter
        :param gain_ch_name: string gain_ch_name e.g. "Gain_0"
        :param gain: uint8_t gain
        :return: int result from write operation.
        """

        return self.__adc_write_register(gain_ch_name, gain)

    def adc_reset(self):
        """ Reset the ADC """
        wrbuf = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        self.spi_obj.writebytes(wrbuf)
        self.__adc_write_register('ADC_Control', 0x13D0)

    def adc_read_id(self):
        data_32 = self.__adc_read_register('ID', 1)
        data_32.pop(0)
        print(data_32)
        chipid = int.from_bytes(data_32, byteorder='big', signed=False)

        print("ID = %d" % chipid)

    # </editor-fold>

    # <editor-fold desc="************* AD7124 Private Methods ********************">
    def __wait_end_of_conversion(self,  timeout_s):
        starttime = time.time()
        nready = 1
        while nready is 1:
            data_8 = self.adc_read_status_register()
            nready = data_8['n_rdy']
            currtime = time.time()
            if currtime - starttime > timeout_s:
                print("timeout %f" % (currtime - starttime))
                return -1
        return data_8['ch_active']  # return current channel#

    def __read_reg(self, regid, byte_len):
        """
         * @brief Reads a register of the AD7124
         * @param  address - address of the register
         * @return value of the register
        """
        regid |= self._READ_FLAG
        byte_list = [regid]
        for i in range(byte_len):
            byte_list.append(self._DUMMY_BYTE)

        resp = self.spi_obj.xfer2(byte_list)
        return resp

    def __write_reg(self, regid, reg_val):
        """
         * @brief Writes a register of the AD7124
         * @param uint8 address - address of the register
         * @param uint8 reg_val - value to be written
         * @return none
        """
        bytelist = [regid]
        for val in reg_val:
            bytelist.append(val)
        self.spi_obj.xfer2(bytelist)

    def __adc_read_register(self, reg_name, byte_len):
        """
        * @brief Reads and returns the value of a device register. The read
        * value is also stored in software register list of the device.
        *
        * @param reg - string: Which register to read from.
        *
        * @return - uint8: Returns the value read from the specified register.
        """
        regid = RegAddrs.search_reg_address_from_name(reg_name)
        resp = self.__read_reg(regid, byte_len)
        return resp

    def __adc_write_register(self, reg_name, value):
        """
        * @brief Writes the specified value to a device register. The
        *        value to be written is also stored in the software
        *        register list of the device.
        *
        * @param device - The handler of the instance of the driver.
        * @param reg - string: Which register to write to.
        * @param value - uint32: The value to be written to the
        *                reigster of the device.
        *
        * @return uint32: Returns 0 for success or negative error code.
        """
        regid = RegAddrs.search_reg_address_from_name(reg_name)
        rbytes = value.to_bytes((value.bit_length() + 7) // 8, byteorder='big')
        self.__write_reg(regid, rbytes)

    def __get_adc_params_from_db(self):
        con = sqlite3.connect("smb.db")
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM tblAdcParams WHERE PK_ADC_ID = " + str(self._sens_num))
        params = cur.fetchall()
        con.close()
        for param in params:
            if param is None:
                print("no records found")
            else:
                current = param[1]
                self._adc_excitation_mode = Gbl.ExcitationCurrents.get(current, 0)
                # print("Current = %d Mode = %d " % (current, self._adc_excitation_mode))
                self._temp_unit = param[2]
                # print("Temperatue Uint = %s" % self._temp_unit)
                self._sns_type = param[3]
                # print("Sensor type = %s" % self._sns_type)
                self._adc_filter = param[4]
                # print("Filter = %d" % self._adc_filter)
                self._therm_resistance = param[5]
                # print("Thermister Resistance = %d" % self._therm_resistance)
                self._therm_beta = param[6]
                # print("Thermister Beta = %d" % self._therm_beta)
                self._adc_gain = param[7]
                # print("ADC Gain = %d" % self._adc_gain)
                self._ref_resistor = param[8]
                # print("ref resistor = %d" % self._ref_resistor)

    def __get_sensor_constants_from_db(self):
        con = sqlite3.connect("smb.db")
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        sql = "SELECT * FROM tblPolynomialCostants WHERE Device = " + "'" + self._sns_type + "'" + " LIMIT 1"
        cur.execute(sql)
        rows = cur.fetchall()

        for row in rows:
            if row is None:
                print("no records found")
            else:
                self.sns.sensor_type = row[0]
                self.sns.const_0 = row[1]
                self.sns.const_1 = row[2]
                self.sns.const_2 = row[3]
                self.sns.const_3 = row[4]
                self.sns.const_4 = row[5]
                self.sns.const_5 = row[6]
                self.sns.const_6 = row[7]
                self.sns.const_7 = row[8]

        con.close()

    def __adc_retrieve_reg_bits_from_db(self, tblname):
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

    # </editor-fold>
