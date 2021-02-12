import logging
import threading
import time

import numpy as np

from DAC8775 import DAC
import quieres

import Gbl

class PidHeater(object):
    """ pid_heater class """

    LOOP_MODE_IDLE = 0
    LOOP_MODE_POWER = 1
    LOOP_MODE_SIMPLE_PID = 2
    LOOP_MODE_PID = 3

    TRACE_LOOP = 0x01
    
    def __init__(self, idx, smbdb, tlm_dict, spi, io):
        self.logger = logging.getLogger('heaters')
        self.logger.setLevel(logging.INFO)
        self.db = smbdb

        self.spi = spi
        self.io = io
        
        self._heater_num = idx + 1

        self._maxCurrent = 0.024
        self.maxTotalCurrent = 0.096
        self.currentLimit = self.maxTotalCurrent
        
        self._heater_p_term = 1.0
        self._heater_i_term = 1.0
        self._heater_d_term = 0.0
        self._heater_current = 0.0
        self._heater_mode = self.LOOP_MODE_IDLE
        self._heater_ctrl_sensor = 0
        self._heater_set_pt = 0.0
        self.tlm_dict = tlm_dict
        self.last_pv = 0.0  # last process variable
        self.mv_i = 0.0  # prescaled integration sum
        self.mv_min = 0.0
        self.mv_max = 5000.0

        # There is a newer loop implementation which uses physical parameters and 
        # which is controlled entirely by the external caller. 
        self.loopConfig = dict(P=1.0, I=1.0, offset=0.0,
                               rho=None, tau=None, tint=None, R=None,
                               lastSum=0.0,
                               maxTempRate=5.0/60,
                               failsafePower=40.0)

        # We want to support tweaking the loop while it is running.
        # Try to do that safely.
        self.configLock = threading.RLock()

        self.connectDAC()
        self.config_heater_params()

    def connectDAC(self):
        idx = self._heater_num - 1
        with Gbl.ioLock:
            restart = hasattr(self, 'dac')
            self.logger.info('htr %d: connecting DAC (restart %s, mode %d, current %0.4f)', 
                             self._heater_num, restart, 
                             self.heater_mode, self.heater_current)
            if restart:
                self.dac.dac_write_register('reset', rst=1)
                time.sleep(0.1)
                del self.dac
            self.dac = DAC(idx, self.db, self.spi, self.io)

            if restart:
                self.set_htr_mode(self.heater_mode)
                if self.heater_mode == self.LOOP_MODE_POWER:
                    self.htr_set_heater_current(self.heater_current)
        
    def __str__(self):
        configList = ["%s=%s" % (k,v) for k,v in self.loopConfig.items()]
        return "heater num=%d mode=%d sensor=%d %s" % (self._heater_num, self.heater_mode, 
                                                       self.heater_ctrl_sensor, " ".join(configList))
        
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
        if value < 0.00 or value > 320.0:
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
        if value < 0 or value > self.LOOP_MODE_PID:
            raise ValueError("Heater Mode value out of range")
        self.logger.info('htr %d: setting loop mode from %s to %s', 
                         self._heater_num, self._heater_mode, value)
        self._heater_mode = value

    @property
    def heater_current(self):
        return self._heater_current

    @heater_current.setter
    def heater_current(self, value):
        if value < 0 or value >= 1.00:
            raise ValueError("Heater current value out of range")
        self._heater_current = value

    def config_heater_params(self):
        htr_param_dict = quieres.db_fetch_heater_params(self.db, self._heater_num)
        self._heater_p_term = htr_param_dict['P']
        self._heater_i_term = htr_param_dict['I']
        self._heater_d_term = htr_param_dict['D']
        self._heater_set_pt = htr_param_dict['set_pt']
        self._heater_ctrl_sensor = htr_param_dict['ctrl_sensor']
        # self._heater_mode = htr_param_dict['mode']
        # self._heater_current = htr_param_dict['htr_current']

    def set_htr_mode(self, mode):
        if mode == self.LOOP_MODE_IDLE:
            self.htr_enable_heater_current(False)
            self.heater_mode = self.LOOP_MODE_IDLE
        elif mode == self.LOOP_MODE_POWER:
            self.htr_enable_heater_current(True)
            self.heater_mode = self.LOOP_MODE_POWER
        elif mode == self.LOOP_MODE_SIMPLE_PID:
            self.htr_enable_heater_current(True)
            self.heater_mode = self.LOOP_MODE_SIMPLE_PID
        elif mode == self.LOOP_MODE_PID:
            self.validate_loop_params() # Will raise exception on failure.
            self.htr_enable_heater_current(True)
            self.heater_mode = self.LOOP_MODE_PID
        else:
            self.logger.error('htr %d invalid mode request %s ignored',
                              self._heater_num, mode)
            
        quieres.db_update_htr_params(self.db, self.heater_mode, 'mode', self._heater_num)

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
          Requested current, clipped to 0 to 0.096A or less

        The output is the sum of four 0.024A DAC channels named 'A'
        through 'D'. These channels are increased one bit at a bit 
        in order as the load requires. I.e. the four channels never 
        have settings which differ from each other by more than 1.

        """

        maxTotalCurrent = self.maxTotalCurrent
        maxTotalBits = 4*0xffff

        if current < 0:
            current = 0.0
        if current > self.currentLimit:
            self.logger.warning('htr %d: requested current %0.4f > max limit %0.4f: CLIPPED!' %
                                (self._heater_num, current, self.currentLimit))
            current = self.currentLimit

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
            self.dac.select_dac('all')
            self.dac.dac_write_dac_data_reg(0x0000)
            self.dac.select_dac('none')

    def update_one_dac(self, dac, value):
        with Gbl.ioLock:
            self.dac.select_dac(dac)
            self.dac.dac_write_dac_data_reg(value)

            self.dac.select_dac(dac)
            check = self.dac.dac_read_dac_data_reg()

        if value != check:
            self.logger.warn('DAC readback failed. expected 0x%04x, got 0x%04x',
                             value, check)
            
        self.dac.dac_check_status()
            
    def pid_bounds_check(self, value):
        if value > self.mv_max:
            return self.mv_max

        elif value < self.mv_min:
            return self.mv_min
        else:
            return value

    def simple_loop(self, pv):
        error = self._heater_set_pt - pv

        # Decay integrated offset
        self.mv_i += self._heater_i_term * error
        self.mv_i = self.pid_bounds_check(self.mv_i)

        mv = (self._heater_p_term * error) + self.mv_i + (self._heater_d_term * (self.last_pv - pv))
        self.last_pv = pv

        return self.pid_bounds_check(mv)

    def validate_loop_params(self):
        """Check whether we can run a non-simple loop. Raises exception on failure. """

        cfg = self.loopConfig
        for k in 'rho', 'tau', 'tint', 'R', 'maxTempRate', 'failsafePower':
            if cfg[k] is None:
                raise RuntimeError('htr %d: heater physical parameter %s has not been set' % 
                                   (self._heater_num, k))

    def _loopStep(self, delta, loopPeriod):
        """Given a error, calculate and apply loop correction

        We know and use physical properties of the system: 
        - resistance of the heater loop (R ohms) 
        - thermal resistance of the path (rho K/W)
        - thermal time constant (tau seconds)

        Along with the sampling interval dt.
        
        So we take delta K, and calculate the desired W to apply.
        Then finally convert to our internal current A 
  
        Parameters
        ----------
        delta : float
            calculated error, in K
        loopPeriod : float
            measurement loop period, s
        """

        cfg = self.loopConfig
        
        A = cfg['P'] / cfg['rho']
        B = (cfg['I'] * loopPeriod)/(cfg['rho'] * cfg['tau'])
        k0 = cfg['tint'] / loopPeriod

        # lock around lastSum and impulse changes.
        with self.configLock:
            # deweight older deltas according to our time constant
            lastSum = cfg['lastSum']
            sum = delta + (1 - 1/k0)*lastSum

            P_i = -A*delta - B*sum + cfg['offset']
            if P_i < 0:
                P_i = 0
                
            # Convert power to current
            I_i = np.sqrt(P_i / cfg['R'])

            # Avoid windup on output saturation. I am not doing this right.
            if I_i == 0:
                if lastSum == 0:
                    sum = 0.0
                else:
                    sum = (1 - 1/k0)*lastSum
            elif I_i > self.currentLimit:
                I_i = self.currentLimit
                if lastSum == 0: # Loop just started
                    sum = delta
                else:
                    sum = (1 - 1/k0)*lastSum
            cfg['lastSum'] = sum

            # Hold the output current at a fixed value for some number of
            # samples.
            if cfg['impulseCount'] > 0:
                self.logger.warning('htr %d applying impulse current: %0.4fA', self._heater_num,
                                    cfg['impulseCurrent'])
                I_i = cfg['impulseCurrent']
                cfg['impulseCount'] -= 1

        if self.traceMask & self.TRACE_LOOP:
            self.logger.info('htr %d delta: %0.4f P_i: %0.4f I_i: %0.4f lastSum: %0.4f sum: %0.4f A: %0.4f B: %0.4f' %
                             (self._heater_num, delta, P_i, I_i * 1000, lastSum, sum, A, B))

        if self.heater_mode == self.LOOP_MODE_PID:
            self.htr_set_heater_current(I_i)
            
    def updateControlLoop(self, adcs, loopPeriod):
        """Handle updated temperature sensor readings.
      
        Args
        ----
        adcs : all the new readings, in K.
        """

        if self.heater_ctrl_sensor == 0:
            return

        sensor = 'rtd%d' % (self.heater_ctrl_sensor)
        pv = Gbl.telemetry[sensor]

        # Leave existing SMB loop unchanged.
        if self.heater_mode == self.LOOP_MODE_SIMPLE_PID:
            self.simple_loop(pv)
            return

        delta = pv - self._heater_set_pt

        if self.heater_mode != self.LOOP_MODE_PID:
            return

        if self.last_pv is not None and self.last_pv > 0:
            tempRate = abs(pv - self.last_pv) / loopPeriod * 60
        else:
            tempRate = 0.0
        self.last_pv = pv
        
        if tempRate > self.loopConfig['maxTempRate']:
            self.logger.critical('htr %d temp rate %0.2f K/min exceeds limit %0.2f: shutting down loop and setting to %0.2f percent',
                                 self._heater_num, tempRate, self.loopConfig['maxTempRate'], 
                                 self.loopConfig['failsafeFraction'] * 100)
            self.set_htr_mode(self.LOOP_MODE_POWER)
            self.htr_set_heater_fraction(self.loopConfig['failsafeFraction'])
            self.lastSum = 0.0
            return
        
        # We might want to first run a Kalman filter on the raw values, if only
        # to paper over sampling jitter.  Stretch goal.
            
        self._loopStep(delta, loopPeriod)

    def impulse(self, current, duration=None):
        """Perturb the loop by injecting an impulse

        Parameters
        ----------
        current : float
            Current to apply
        duration : int, optional
            Number of cycles to apply, by default None
        """

        if current < 0:
            current = 0
        if current > self.maxTotalCurrent:
            current =  self.maxTotalCurrent

        if duration is None:
            duration = 1
        if duration > 10:
            duration = 10

        with self.configLock:
            self.loopConfig['impulseCount'] = duration
            self.loopConfig['impulseCurrent'] = current

    def connect(self):
        self.connectDAC()

    def readReg(self, *, name=None):
        lev = self.dac.logger.level
        self.dac.logger.setLevel(10)
        ret = self.dac.dac_read_register(name)
        self.dac.logger.setLevel(lev)
        self.logger.debug('readReg name=%s returned %s' % (name, ret))
        return str(ret)

    def writeReg(self, *, regName=None, name=None, value=None):
        lev = self.dac.logger.level
        self.dac.logger.setLevel(10)
        kwArgs = dict(name=value)
        self.dac.dac_write_register(regName, **kwArgs)
        self.dac.logger.setLevel(lev)

        ret = self.dac.dac_read_register(regName)
        return ret

    def status(self, *, full=False):
        ret = 'mode=%s sensor=%d setpoint=%0.4f output=%0.3f' % (self.heater_mode,
                                                                 self.heater_ctrl_sensor,
                                                                 self.heater_set_pt,
                                                                 self.heater_current)
        if full:
            cfg = self.loopConfig
            ret2 = 'P=%d I=%d' % (cfg['P'], cfg['I'])
            ret3 = 'rho=%0.2f tau=%0.2f R=%0.2f tint=%0.2f maxCurrent=%0.3f failsafeFraction=%0.2f' % (cfg['rho'],
                                                                                                       cfg['tau'],
                                                                                                       cfg['R'],
                                                                                                       cfg['tint'],
                                                                                                       self.currentLimit,
                                                                                                       cfg['failsafeFraction'])
            ret = '%s %s %s' % (ret, ret2, ret3)

        return ret

    def configure(self, *, on=None,
                  setpoint=None,
                  trace=None,
                  P=None, I=None,
                  offset=None,
                  sensor=None,
                  rho=None, tau=None,
                  R=None, tint=None,
                  maxCurrent=None,
                  maxTempRate=None,
                  failsafeFraction=None,
                  loopCount=1):
        """Reconfigure heater loop based on command options.

        Parameters
        ----------
        on : bool
            Whether loop should be on
        setpoint : float
            Temperature, in K, to servo to.
        trace : int, optional
            Mask of diagnostic output
        P : int
            The P_i term
        I : int
            The I_i term
        offset : float
            The default output.
        sensor : int
            Which temperature sensor to servo from.
            If this is 0, we neither calculate nor apply signal.
        rho : float
            Thermal resistance, K/W
        tau : float
            Thermal time constant, seconds
        R : float
            Heater resistance, ohms
        maxCurrent : float
            The maximum current we can apply, mA
        maxTempRate : float
            The maximum temperature change rate, K/min
        failsafeFraction : float
            If we trip the temp rate, what current to then drive at.
        loopCount : int
            Number of measurement loop samples to skip between corrections
        """

        self.logger.info('htr %d: configuring with %s', self._heater_num, locals())
        
        cfg = self.loopConfig
        
        if on is False:
            self.set_htr_mode(self.LOOP_MODE_IDLE)
            self.last_pv = 0.0

        # We might turn the loop off due to some sanity checks. Make
        # sure to remember to enable the loop if so.
        if self.heater_mode == self.LOOP_MODE_PID:
            on = True
            
        if sensor is not None:
            if sensor < 0 or sensor > 12:
                raise RuntimeError('sensor must be 0..12')
            
            # shutdown any loop with a different sensor
            if sensor != self.heater_ctrl_sensor:
                self.set_htr_mode(self.LOOP_MODE_IDLE)
                self.last_pv = 0.0
            self.heater_ctrl_sensor = sensor

        if trace is not None:
            self.traceMask = trace

        with self.configLock:
            self.impulse(0, 0)
               
            if setpoint is not None:
                self._heater_set_pt = setpoint
            if P is not None:
                cfg['P'] = P
            if I is not None:
                cfg['I'] = I
            if offset is not None:
                cfg['offset'] = offset
            if rho is not None:
                cfg['rho'] = rho
            if tau is not None:
                cfg['tau'] = tau
            if tint is not None:
                cfg['tint'] = tint
            if R is not None:
                cfg['R'] = R
            if maxCurrent is not None:
                self.currentLimit = maxCurrent
            if maxTempRate is not None:
                cfg['maxTempRate'] = maxTempRate
            if failsafeFraction is not None:
                if failsafeFraction > 100:
                    failsafeFraction = self.failsafeFraction
                cfg['failsafeFraction'] = failsafeFraction / 100
            if cfg['offset'] > self.currentLimit:
                cfg['offset'] = self.currentLimit
        if on:
            self.last_pv = 0.0
            self.set_htr_mode(self.LOOP_MODE_PID) # Will throw up on config error.
            
        return self.status(full=True)
