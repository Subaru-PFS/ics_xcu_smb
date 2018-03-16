"""
Created on Wed Jan 24 12:49:52 2018

@author: pi
"""
import spi_bus
import time
import db
import Gbl
import AD7124_Reg_Addresses as RegAddrs
import AD7124_Reg_bits as b
from math import log
import RPi.GPIO as GPIO
from Sensor import sensor
import ADC_helper_ftns as AdcHelper


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

    @property
    def adc_excitation_mode(self):
        return self._adc_excitation_mode

    @adc_excitation_mode.setter
    def adc_excitation_mode(self, value):
        if value < 0 or value > 7:
            raise ValueError("Excitation mode val out of range")
        self._adc_excitation_mode = value

    @property
    def temp_unit(self):
        return self._temp_unit

    @temp_unit.setter
    def temp_unit(self, value):
        if value != "K" or value != "C" or value != "F":
            raise ValueError("Invalid Unit Type")
        self._temp_unit = value

    @property
    def sns_type(self):
        return self._sns_type

    @sns_type.setter
    def sns_type(self, value):
        if value != "DT670" or value != "RTD" or value != "RAW":
            raise ValueError("Invalid Sensor Type")
        self._sns_type = value

    @property
    def adc_filter(self):
        return self._adc_filter

    @adc_filter.setter
    def adc_filter(self, value):
        if value < 0 or value > 7:
            raise ValueError("Filter val out of range")
        self._adc_filter = value

    @property
    def therm_resistance(self):
        return self._therm_resistance

    @therm_resistance.setter
    def therm_resistance(self, value):
        if value < 1 or value > 10000:
            raise ValueError("Thermister Resistance Out of Range")
        self._therm_resistance = value

    @property
    def therm_beta(self):
        return self._therm_beta

    @therm_beta.setter
    def therm_beta(self, value):
        if value < 1 or value > 10000:
            raise ValueError("Thermister Beta Out of Range")
        self._therm_beta = value

    @property
    def adc_gain(self):
        return self._adc_gain

    @adc_gain.setter
    def adc_gain(self, value):
        if value < 1 or value > 128:
            raise ValueError("Gain Out of Range")
        self._adc_gain = value

    @property
    def ref_resistor(self):
        return self._ref_resistor

    @therm_resistance.setter
    def therm_resistance(self, value):
        if value < 0 or value > 10000:
            raise ValueError("Ref Resistance Out of Range")
        self._ref_resistor = value
    # </editor-fold>

    def adc_initialize(self):
        self.get_adc_params_from_db()
        self.get_sensor_constants_from_db()
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
        self.adc_set_config_regs()
        """ iout0_ch_name, iout1_ch_name, iout0_name, iout1_name, pdsw, gpio_ctrl1, gpio_ctrl2, gpio_dat1, gpio_dat2 """
        self.set_io_reg1('IoutCh0', 'IoutCh5', 'Current500ua', 'Current500ua', False, True, False, False, False)
        self.set_io_reg2(False, False, False, False, False, False, False, False)
        self.config_error_register()
        self.set_adc_control('ContinuousMode', 'FullPower', True, 'InternalClk')

    def read_conversion_data(self):

        ch_flgs = [False, False, False, False, True, False, False]
        done = False
        while not done:
            channel = self.__wait_end_of_conversion(1)
            data_32 = self.adc_read_register('Data', 3)
            data_32.pop(0)
            conversion = int.from_bytes(data_32, byteorder='big', signed=False)

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
            data_32 = self.adc_read_register("Channel_" + str(i), 2)
            data_32.pop(0)
            print(data_32)

        # Channel_num, configuration, +input, -input, Enabled?
        self.set_channel('Channel_0', 0, 'AIN1Input', 'AIN4Input', True)  # CH0 - PT1000
        self.set_channel('Channel_1', 1, 'AIN5Input', 'AIN6Input', True)  # CH1 - RT1 Thermistor
        self.set_channel('Channel_2', 1, 'IOVDD6PInput', 'IOVDD6MInput', True)  # CH2 - IOVDD
        self.set_channel('Channel_3', 1, 'AVDD6PInput', 'AVDD6MInput', True)  # CH2 - AVDD
        self.set_channel('Channel_5', 3, 'TEMPInput', 'AVSSInput', True)  # CH5 - Internal Sensor
        self.set_channel('Channel_6', 2, 'REFInput', 'AIN7Input', True)  # CH6 - Regerence In
        print("After Ch Programming")
        for i in range(7):
            data_32 = self.adc_read_register("Channel_" + str(i), 2)
            data_32.pop(0)
            print(data_32)

    def adc_set_config_regs(self):
        """  cfg_num, Reference, Gain, Bipolar?, Burnoutcurrent """
        gain = AdcHelper.select_gain_to_strings(self._adc_gain)
        self.set_config('Config_0', 'RefIn1', gain, True, 'BurnoutOff')
        self.set_config('Config_1', 'RefInternal', 'Pga1', False, 'BurnoutOff')
        self.set_config('Config_2', 'RefAVdd', 'Pga1', False, 'BurnoutOff')
        self.set_config('Config_3', 'RefInternal', 'Pga1', True, 'BurnoutOff')

    def get_adc_params_from_db(self):
        con = db.create_connection('smb.db')
        cur = con.cursor()
        cur.execute("SELECT * FROM tblAdcParams WHERE PK_ADC_ID = " + str(self._sens_num))

        params = cur.fetchall()

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

    def set_io_reg1(self, iout0_ch_name, iout1_ch_name, iout0_name, iout1_name,
                    pdsw, gpio_ctrl1, gpio_ctrl2, gpio_dat1, gpio_dat2):
        """
        :param iout0_ch_name:
        :param iout1_ch_name:
        :param iout0_name:
        :param iout1_name:
        :param pdsw:
        :param gpio_ctrl1:
        :param gpio_ctrl2:
        :param gpio_dat1:
        :param gpio_dat2:
        :return:
        """

        iout0_ch = RegAddrs.IoutCh[iout0_ch_name]
        iout1_ch = RegAddrs.IoutCh[iout1_ch_name]
        iout0 = RegAddrs.IoutCurrent[iout0_name]
        iout1 = RegAddrs.IoutCurrent[iout1_name]

        value = (b.AD7124_IO_CTRL1_REG_IOUT1(iout1) |
                 b.AD7124_IO_CTRL1_REG_IOUT0(iout0) |
                 b.AD7124_IO_CTRL1_REG_IOUT_CH1(iout1_ch) |
                 b.AD7124_IO_CTRL1_REG_IOUT_CH0(iout0_ch) |
                 (b.AD7124_IO_CTRL1_REG_GPIO_DAT1() if gpio_dat1 else 0) |
                 (b.AD7124_IO_CTRL1_REG_GPIO_DAT2() if gpio_dat2 else 0) |
                 (b.AD7124_IO_CTRL1_REG_GPIO_CTRL1() if gpio_ctrl1 else 0) |
                 (b.AD7124_IO_CTRL1_REG_GPIO_CTRL2() if gpio_ctrl2 else 0) |
                 (b.AD7124_IO_CTRL1_REG_PDSW() if pdsw else 0))

        return self.adc_write_register('IOCon1', value)

    def set_io_reg2(self, vbias0, vbias1, vbias2, vbias3, vbias4, vbias5, vbias6, vbias7):

        value = ((b.AD7124_IO_CTRL2_REG_GPIO_VBIAS7() if vbias0 else 0) |
                 (b.AD7124_IO_CTRL2_REG_GPIO_VBIAS6() if vbias1 else 0) |
                 (b.AD7124_IO_CTRL2_REG_GPIO_VBIAS5() if vbias2 else 0) |
                 (b.AD7124_IO_CTRL2_REG_GPIO_VBIAS4() if vbias3 else 0) |
                 (b.AD7124_IO_CTRL2_REG_GPIO_VBIAS3() if vbias4 else 0) |
                 (b.AD7124_IO_CTRL2_REG_GPIO_VBIAS2() if vbias5 else 0) |
                 (b.AD7124_IO_CTRL2_REG_GPIO_VBIAS1() if vbias6 else 0) |
                 (b.AD7124_IO_CTRL2_REG_GPIO_VBIAS0() if vbias7 else 0))

        return self.adc_write_register('IOCon2', value)

    def set_config_filter(self, filter_name, filter_type_name, postfilter_name, filt_datarate_sel, rej60, single):
        """
        :brief Sets the AD7124 Filter
        :param filter_name: string Configuration Register to use
        :param filter_type_name: string Filter Type
        :param postfilter_name: string Post Filter Type
        :param filt_datarate_sel: uint16_t
        :param rej60: bool
        :param single: bool
        :return: int
        """

        cfilter = RegAddrs.FilterType[filter_type_name]
        postfilter = RegAddrs.PostFilterType[postfilter_name]

        value = (b.AD7124_FILT_REG_FILTER(cfilter) |
                 b.AD7124_FILT_REG_POST_FILTER(postfilter) |
                 b.AD7124_FILT_REG_FS(filt_datarate_sel) |
                 (b.AD7124_FILT_REG_REJ60() if rej60 else 0) |
                 (b.AD7124_FILT_REG_SINGLE_CYCLE() if single else 0))

        return self.adc_write_register(filter_name, value)

    def set_config_gain(self, gain_ch_name, gain):
        """
        :brief Sets the AD7124 Filter
        :param gain_ch_name: string gain_ch_name e.g. "Gain_0"
        :param gain: uint8_t gain
        :return: int result from write operation.
        """

        return self.adc_write_register(gain_ch_name, gain)

    def get_sensor_constants_from_db(self):
        con = db.create_connection('smb.db')
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

    def __wait_end_of_conversion(self,  timeout_s):
        starttime = time.time()
        nready = 1
        data_8 = 0x00
        while nready > 0:
            data_8 = self.read_status_register()
            nready = data_8 & b.AD7124_STATUS_REG_RDY()
            currtime = time.time()

            if currtime - starttime > timeout_s:
                print("timeout %f" % (currtime - starttime))
                return -1
        data_8 &= 0x0f
        return data_8  # return current channel#

    # <editor-fold desc="************* AD7124 Methods ********************">
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

    def adc_read_register(self, reg_name, byte_len):
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

    def adc_write_register(self, reg_name, value):
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

    def set_adc_control(self, op_modename, power_modename, ref_en, clk_selname):
        """
        :brief Sets the AD7124 Control Register
        Buffering is automatically configured
        :param op_modename: string Operationg Mode
        :param power_modename: string Power Mode
        :param ref_en: bool Enable reference
        :param clk_selname: uint8_t clock select
        :return: int result from write operation.
        """
        op_mode = RegAddrs.OperatingMode[op_modename]
        power_mode = RegAddrs.PowerMode[power_modename]
        clk_sel = RegAddrs.ClkSel[clk_selname]

        value = (b.AD7124_ADC_CTRL_REG_MODE(op_mode) |
                 b.AD7124_ADC_CTRL_REG_POWER_MODE(power_mode) |
                 b.AD7124_ADC_CTRL_REG_CLK_SEL(clk_sel) |
                 (b.AD7124_ADC_CTRL_REG_REF_EN() if ref_en else 0) |
                 b.AD7124_ADC_CTRL_REG_DOUT_RDY_DEL())

        return self.adc_write_register('ADC_Control', value)

    def adc_reset(self):
        """ Reset the ADC """
        wrbuf = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        self.spi_obj.writebytes(wrbuf)
        self.adc_write_register('ADC_Control', 0x13D0)

    def adc_read_id(self):
        data_32 = self.adc_read_register('ID', 1)
        data_32.pop(0)
        print(data_32)
        chipid = int.from_bytes(data_32, byteorder='big', signed=False)

        print("ID = %d" % chipid)

    def set_config(self, cfgname, refname, pganame, bipolar, burnoutname):
        """
        :brief Sets the AD7124 Configuration Register
        :param cfgname: string configuration register name
        :param refname: string reference to use for conversion
        :param pganame: uint8_t Pga Select
        :param bipolar: bool bipolar:True, unipolaer:False
        :param burnoutname: uint8_t burnout current to use
        :return: int result from write operation.
        """
        refid = RegAddrs.RefSel[refname]
        pgaid = RegAddrs.PgaSel[pganame]
        burnoutid = RegAddrs.BurnoutCurrent[burnoutname]

        value = (b.AD7124_CFG_REG_REF_SEL(refid) |
                 b.AD7124_CFG_REG_PGA(pgaid) |
                 b.AD7124_CFG_REG_BURNOUT(burnoutid) |
                 b.AD7124_CFG_REG_REF_BUFP() | b.AD7124_CFG_REG_REF_BUFM() |
                 b.AD7124_CFG_REG_AIN_BUFP() | b.AD7124_CFG_REG_AINN_BUFM() |
                 (b.AD7124_CFG_REG_BIPOLAR() if bipolar else 0))

        return self.adc_write_register(cfgname, value)

    def enable_channel(self, ch_name, enable):
        """
        :brief sets the AD7124 channel enable status
        value is also stored in software register list of the device.
        :param ch_name: uint8_t internal channel to select
        :param enable: bool enable channel
        :return: int esult from write operation.
        """
        data_32 = self.adc_read_register(ch_name, 3)
        value = int.from_bytes(data_32, byteorder='big', signed=False)
        if value < 0:
            return value
        if enable is True:
            value |= b.AD7124_CH_MAP_REG_CH_ENABLE()
        else:
            value &= ~b.AD7124_CH_MAP_REG_CH_ENABLE()
        return self.adc_write_register(ch_name, value)

    def set_channel(self, ch_name, cfg, ainp, ainm, enable):
        """
        :brief Sets the AD7124 Internal Channel
        :param ch_name: string internal channel to select
        :param cfg: uint8_t configuration register to use
        :param ainp: string Analog input plus
        :param ainm: string Analog input minus
        :param enable: bool enable channel
        :return: int result from write operation.
        """
        regid = RegAddrs.search_reg_address_from_name(ch_name)
        if regid > 0:
            input_p = RegAddrs.InputSel[ainp]
            input_n = RegAddrs.InputSel[ainm]

            value = (b.AD7124_CH_MAP_REG_SETUP(cfg) |
                     b.AD7124_CH_MAP_REG_AINP(input_p) |
                     b.AD7124_CH_MAP_REG_AINM(input_n) |
                     (b.AD7124_CH_MAP_REG_CH_ENABLE() if enable else 0))

            return self.adc_write_register(ch_name, value)
        else:
            return -1

    def read_error_register(self):
        data_32 = self.adc_read_register('Error', 3)
        data_32.pop(0)
        value = int.from_bytes(data_32, byteorder='big', signed=False)
        return value

    def read_status_register(self):
        data_8 = self.adc_read_register('Status', 1)
        data_8.pop(0)
        value = int.from_bytes(data_8, byteorder='big', signed=False)
        return value

    def config_error_register(self):
        self.adc_write_register('Error_En', 0x7F018)
    # </editor-fold>
