from DAC8775 import DAC
from db import db_fetch_heater_params


class PidHeater(object):
    """ pid_heater class """
    def __init__(self, idx, tlm_dict):
        self.dac = DAC(idx)
        self._heater_num = idx + 1
        self._heater_p_term = 1
        self._heater_i_term = 1
        self._heater_d_term = 1
        self._heater_current = 0
        self._heater_mode = 0
        self._heater_ctrl_sensor = 0
        self._heater_set_pt = 0.0
        self.tlm_dict = tlm_dict
        param_dict = db_fetch_heater_params(self._heater_num)
        self.config_heater_params(param_dict)

    @property
    def heater_p_term(self):
        print("Getting value")
        return self._heater_p_term

    @heater_p_term.setter
    def heater_p_term(self, value):
        if value < 0.0 or value > 100.0:
            raise ValueError("Heater P Term out of range")
        self._heater_p_term = value

    @property
    def heater_i_term(self):
        print("Getting value")
        return self._heater_i_term

    @heater_i_term.setter
    def heater_i_term(self, value):
        if value < 0.0 or value > 100.0:
            raise ValueError("Heater I Term out of range")
        self._heater_i_term = value

    @property
    def heater_d_term(self):
        print("Getting value")
        return self._heater_d_term

    @heater_d_term.setter
    def heater_d_term(self, value):
        if value < 0.0 or value > 100.0:
            raise ValueError("Heater D Term out of range")
        self._heater_d_term = value

    @property
    def heater_set_pt(self):
        print("Getting value")
        return self._heater_set_pt

    @heater_set_pt.setter
    def heater_set_pt(self, value):
        if value < 0.00 or value > 1000.00:
            raise ValueError("Heater set point out of range")
        self._heater_set_pt = value

    @property
    def heater_ctrl_sensor(self):
        print("Getting value")
        return self._heater_ctrl_sensor

    @heater_ctrl_sensor.setter
    def heater_ctrl_sensor(self, value):
        if value < 0 or value > 12:
            raise ValueError("Heater sensor# out of range")
        self._heater_ctrl_sensor = value

    @property
    def heater_mode(self):
        print("Getting value")
        return self._heater_mode

    @heater_mode.setter
    def heater_mode(self, value):
        if value < 0 or value > 3:
            raise ValueError("Heater Mode value out of range")
        self._heater_mode = value

    @property
    def heater_current(self):
        print("Getting value")
        return self._heater_current

    @heater_current.setter
    def heater_current(self, value):
        if value < 0 or value >= 1.00:
            raise ValueError("Heater current value out of range")
        self._heater_current = value

    def config_heater_params(self, htr_param_dict):
        self._heater_p_term = htr_param_dict['P']
        self._heater_i_term = htr_param_dict['I']
        self._heater_d_term = htr_param_dict['D']
        self._heater_set_pt = htr_param_dict['set_pt']
        self._heater_ctrl_sensor = htr_param_dict['ctrl_sensor']
        self._heater_mode = htr_param_dict['mode']
        self._heater_current = htr_param_dict['htr_current']

    def set_htr_mode(self, mode):
        if mode == 'Disabled':
            pass
        elif mode == 'current':
            pass

    def htr_enable_heater_current(self, state):
        """ select all four dac channels """
        dict_sel_dac_reg = self.dac.dac_read_register('dac_read_select_dac_reg','tblDacSelectDacReg')
        dict_sel_dac_reg['cha'] = True
        dict_sel_dac_reg['chb'] = True
        dict_sel_dac_reg['chc'] = True
        dict_sel_dac_reg['chd'] = True
        self.dac.dac_write_register('select_dac','tblDacSelectDacReg',**dict_sel_dac_reg)
        """ Now enable all four dac channels"""
        dict_dac_cfg_reg = self.dac.dac_read_register('configuration_dac','tblDacConfigDacReg')
        dict_dac_cfg_reg['oten'] = state
        self.dac.dac_write_register('configuration_dac','tblDacConfigDacReg',**dict_dac_cfg_reg)

    def htr_set_heater_current(self, current):
        """ Write Program DAC Data """
        self.set_all_currents_to_zero()

        if current > .024:
            self.select_one_dac('a')
            hexval = 0xffff
            self.dac.dac_write_dac_data_reg(hexval)
        elif current <= .024:
            self.select_one_dac('a')
            hexval = int((float(0xffff)/.024) * current)
            self.dac.dac_write_dac_data_reg(hexval)

        if current > .048:
            self.select_one_dac('b')
            hexval = 0xffff
            self.dac.dac_write_dac_data_reg(hexval)
        elif .024 < current <= .048:
            self.select_one_dac('b')
            hexval = int(float(0xffff) / .024 * (current - .024))
            self.dac.dac_write_dac_data_reg(hexval)

        if current > .072:
            self.select_one_dac('c')
            hexval = 0xffff
            self.dac.dac_write_dac_data_reg(hexval)
        elif .048 < current <= .072:
            self.select_one_dac('c')
            hexval = int(float(0xffff) / .024 * (current - .048))
            self.dac.dac_write_dac_data_reg(hexval)

        if current > 0.072:
            self.select_one_dac('d')
            hexval = int(float(0xffff) / .024 * (current - .072))
            self.dac.dac_write_dac_data_reg(hexval)

    def set_all_currents_to_zero(self):
        dict_sel_dac_reg = self.dac.dac_read_register('dac_read_select_dac_reg','tblDacSelectDacReg')
        dict_sel_dac_reg['cha'] = True
        dict_sel_dac_reg['chb'] = True
        dict_sel_dac_reg['chc'] = True
        dict_sel_dac_reg['chd'] = True
        self.dac.dac_write_register('select_dac','tblDacSelectDacReg',**dict_sel_dac_reg)
        self.dac.dac_write_dac_data_reg(0x0000)
        dict_sel_dac_reg['cha'] = False
        dict_sel_dac_reg['chb'] = False
        dict_sel_dac_reg['chc'] = False
        dict_sel_dac_reg['chd'] = False
        self.dac.dac_write_register('select_dac','tblDacSelectDacReg',**dict_sel_dac_reg)

    def select_one_dac(self, dac):
        dict_sel_dac_reg = self.dac.dac_read_register('dac_read_select_dac_reg','tblDacSelectDacReg')
        if dac == 'a' or dac == 'A':
            dict_sel_dac_reg['cha'] = True
            dict_sel_dac_reg['chb'] = False
            dict_sel_dac_reg['chc'] = False
            dict_sel_dac_reg['chd'] = False
        elif dac == 'b' or dac == 'B':
            dict_sel_dac_reg['cha'] = False
            dict_sel_dac_reg['chb'] = True
            dict_sel_dac_reg['chc'] = False
            dict_sel_dac_reg['chd'] = False
        elif dac == 'c' or dac == 'C':
            dict_sel_dac_reg['cha'] = False
            dict_sel_dac_reg['chb'] = False
            dict_sel_dac_reg['chc'] = True
            dict_sel_dac_reg['chd'] = False
        elif dac == 'd' or dac == 'C':
            dict_sel_dac_reg['cha'] = False
            dict_sel_dac_reg['chb'] = False
            dict_sel_dac_reg['chc'] = False
            dict_sel_dac_reg['chd'] = True
        else:
            dict_sel_dac_reg['cha'] = False
            dict_sel_dac_reg['chb'] = False
            dict_sel_dac_reg['chc'] = False
            dict_sel_dac_reg['chd'] = False
        self.dac.dac_write_register('select_dac','tblDacSelectDacReg',**dict_sel_dac_reg)
