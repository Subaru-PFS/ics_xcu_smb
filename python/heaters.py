import logging

from DAC8775 import DAC
import quieres

import Gbl

class PidHeater(object):
    """ pid_heater class """
    def __init__(self, idx, smbdb, tlm_dict, spi, io,
                 logLevel=logging.INFO):
        self.logger = logging.getLogger('heaters')
        self.logger.setLevel(logLevel)
        self.db = smbdb

        with Gbl.ioLock:
            self.dac = DAC(idx, self.db, spi, io)
        self._heater_num = idx + 1

        self._maxCurrent = 0.024
        self.maxTotalCurrent = 0.096
        self._heater_p_term = 1.0
        self._heater_i_term = 1.0
        self._heater_d_term = 1.0
        self._heater_current = 0.0
        self._heater_mode = 0
        self._heater_ctrl_sensor = 0
        self._heater_set_pt = 0.0
        self.tlm_dict = tlm_dict
        self.last_pv = 0.0  # last process variable
        self.mv_i = 0.0  # prescaled integration sum
        self.mv_min = 0.0
        self.mv_max = 100.0
        self.config_heater_params()

    # <editor-fold desc="******************* Properties *******************">

    @property
    def heater_p_term(self):
        return self._heater_p_term

    @heater_p_term.setter
    def heater_p_term(self, value):
        if value < self.mv_min or value > self.mv_max:
            raise ValueError("Heater P Term out of range")
        self._heater_p_term = value

    @property
    def heater_i_term(self):
        return self._heater_i_term

    @heater_i_term.setter
    def heater_i_term(self, value):
        if value < self.mv_min or value > self.mv_max:
            raise ValueError("Heater I Term out of range")
        self._heater_i_term = value

    @property
    def heater_d_term(self):
        return self._heater_d_term

    @heater_d_term.setter
    def heater_d_term(self, value):
        if value < self.mv_min or value > self.mv_max:
            raise ValueError("Heater D Term out of range")
        self._heater_d_term = value

    @property
    def heater_set_pt(self):
        return self._heater_set_pt

    @heater_set_pt.setter
    def heater_set_pt(self, value):
        if value < 0.00 or value > 1000.00:
            raise ValueError("Heater set point out of range")
        self._heater_set_pt = value

    @property
    def heater_ctrl_sensor(self):
        return self._heater_ctrl_sensor

    @heater_ctrl_sensor.setter
    def heater_ctrl_sensor(self, value):
        if value < 0 or value > 12:
            raise ValueError("Heater sensor# out of range")
        self._heater_ctrl_sensor = value

    @property
    def heater_mode(self):
        return self._heater_mode

    @heater_mode.setter
    def heater_mode(self, value):
        if value < 0 or value > 3:
            raise ValueError("Heater Mode value out of range")
        self._heater_mode = value

    @property
    def heater_current(self):
        return self._heater_current

    @heater_current.setter
    def heater_current(self, value):
        if value < 0 or value >= 1.00:
            raise ValueError("Heater current value out of range")
        self._heater_current = value

    # </editor-fold>

    # <editor-fold desc="******************* Public Methods *******************">

    def config_heater_params(self):
        htr_param_dict = quieres.db_fetch_heater_params(self.db, self._heater_num)
        self._heater_p_term = htr_param_dict['P']
        self._heater_i_term = htr_param_dict['I']
        self._heater_d_term = htr_param_dict['D']
        self._heater_set_pt = htr_param_dict['set_pt']
        self._heater_ctrl_sensor = htr_param_dict['ctrl_sensor']
        self._heater_mode = htr_param_dict['mode']
        self._heater_current = htr_param_dict['htr_current']

    def set_htr_mode(self, mode):
        if mode == 0:
            self.htr_enable_heater_current(False)
            self._heater_mode = 0
        elif mode == 1:
            self.htr_enable_heater_current(True)
            self._heater_mode = 1
        elif mode == 2:
            self.htr_enable_heater_current(True)
            self._heater_mode = 2
        quieres.db_update_htr_params(self.db, self._heater_mode, 'mode', self._heater_num)

    def htr_enable_heater_current(self, state):
        with Gbl.ioLock:
            # Select all four dac channels.
            dict_sel_dac_reg = self.dac.dac_read_register('select_dac')
            dict_sel_dac_reg['cha'] = True
            dict_sel_dac_reg['chb'] = True
            dict_sel_dac_reg['chc'] = True
            dict_sel_dac_reg['chd'] = True
            self.dac.dac_write_register('select_dac', **dict_sel_dac_reg)
            # Now enable all four dac channels.
            dict_dac_cfg_reg = self.dac.dac_read_register('configuration_dac')
            dict_dac_cfg_reg['oten'] = state
            self.dac.dac_write_register('configuration_dac', **dict_dac_cfg_reg)

    def htr_set_heater_fraction(self, fraction):
        return self.htr_set_heater_current(self.maxTotalCurrent * fraction)
        
    def htr_set_heater_current(self, current):
        """Set all the the current DAC registers for this heater. 

        Args
        ----
        current : float
          Requested current, clipped to 0 to 0.096A

        The output is the sum of four 0.024A DAC channels named 'A'
        through 'D'. These are turned on in order as the load
        requires.

        """

        maxTotalCurrent = self.maxTotalCurrent
        maxTotalBits = 4*0xffff

        if current < 0:
            current = 0.0
        if current > maxTotalCurrent:
            current = maxTotalCurrent

        totalRequest = int(maxTotalBits / maxTotalCurrent * current)
        totalRequest = max(0, min(maxTotalBits, totalRequest))
        baseRequest = totalRequest//4
        residualRequest = totalRequest%4
        self.logger.debug('htr %d: current=%0.4f base=0x%04x residual=%d',
                          self._heater_num, current, baseRequest, residualRequest)
        with Gbl.ioLock:
            self.update_one_dac('a', baseRequest + (residualRequest > 0))
            self.update_one_dac('b', baseRequest + (residualRequest > 1))
            self.update_one_dac('c', baseRequest + (residualRequest > 2))
            self.update_one_dac('d', baseRequest)
            self._heater_current = current

        quieres.db_update_htr_params(self.db, current, 'htr_current', self._heater_num)

    def set_all_currents_to_zero(self):
        with Gbl.ioLock:
            dict_sel_dac_reg = self.dac.dac_read_register('select_dac')
            dict_sel_dac_reg['cha'] = True
            dict_sel_dac_reg['chb'] = True
            dict_sel_dac_reg['chc'] = True
            dict_sel_dac_reg['chd'] = True
            self.dac.dac_write_register('select_dac', **dict_sel_dac_reg)
            self.dac.dac_write_dac_data_reg(0x0000)
            dict_sel_dac_reg['cha'] = False
            dict_sel_dac_reg['chb'] = False
            dict_sel_dac_reg['chc'] = False
            dict_sel_dac_reg['chd'] = False
            self.dac.dac_write_register('select_dac', **dict_sel_dac_reg)

    def select_one_dac(self, dac):
        dac = dac.lower()

        with Gbl.ioLock:
            dict_sel_dac_reg = self.dac.dac_read_register('select_dac')
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
            else:
                dict_sel_dac_reg['cha'] = False
                dict_sel_dac_reg['chb'] = False
                dict_sel_dac_reg['chc'] = False
                dict_sel_dac_reg['chd'] = False
            self.dac.dac_write_register('select_dac', **dict_sel_dac_reg)
        self.logger.debug('selected DAC %s' % (dac))
        
    def update_one_dac(self, dac, value):
        with Gbl.ioLock:
            self.select_one_dac(dac)
            self.dac.dac_write_dac_data_reg(value)

            self.select_one_dac(dac)
            check = self.dac.dac_read_dac_data_reg()

        if value != check:
            self.logger.warn('DAC readback failed. expected 0x%04x, got 0x%04x',
                             value, check)
            
        self.dac.dac_check_status()
            
    # </editor-fold>

    # <editor-fold desc="******************* PID Methods *******************">

    def pid_bounds_check(self, value):
        if value > self.mv_max:
            return self.mv_max

        elif value < self.mv_min:
            return self.mv_min
        else:
            return value

    def calculate_pid(self, pv):
        error = self._heater_set_pt - pv
        self.mv_i += self._heater_i_term * error
        self.mv_i = self.pid_bounds_check(self.mv_i)

        mv = (self._heater_p_term * error) + self.mv_i + (self._heater_d_term * (self.last_pv - pv))
        self.last_pv = pv

        return self.pid_bounds_check(mv)

    def updateControlLoop(self, adcs):
        if self.heater_mode != 2:
            return

        sensor = 'rtd%d' % (self.heater_ctrl_sensor)
        pv = Gbl.telemetry[sensor]
        output = self.calculate_pid(pv)
        
        self.logger.debug('htr %d: sensor=%s, setpoint=%g, pv=%g, value=%g',
                          self._heater_num, sensor, self.heater_set_pt,
                          pv, output)
    # </editor-fold>

