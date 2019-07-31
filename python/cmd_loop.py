import logging
import threading
import os
import queue

import numpy as np

import quieres

import version

class CmdException(Exception):
    @property
    def msg(self):
        return self.args[0]

class CmdLoop(threading.Thread):
    def __init__(self, smbdb, tlm_dict, bang_bangs, adcs, heaters, ads1015,
                 qcommand, qtransmit):

        self.logger = logging.getLogger('smb')
        self.logger.setLevel(logging.INFO)
        self.db = smbdb
        self.tlm_dict = tlm_dict
        self.bb = bang_bangs
        self.adcs = adcs
        self.heaters = heaters
        self.qcmd = qcommand
        self.qxmit = qtransmit
        self.ads1015 = ads1015
        self.__exitEvent = threading.Event()
        
        threading.Thread.__init__(self, name='cmdLoop', daemon=True)

    def pleaseExit(self):
        self.__exitEvent.set()
        
    def run(self):
        while True:
            try:
                cmd = self.qcmd.get(timeout=1)
            except queue.Empty:
                if self.__exitEvent.is_set():
                    self.logger.info('exiting command thread because we were asked to.')
                    return
                else:
                    continue
                
            if isinstance(cmd, str):
                try:
                    self.logger.info('processing raw cmd: %s', cmd)
                    self.process_string_cmd(cmd)
                except CmdException as e:
                    self.logger.warn('command failure: %s', e)
                    self.qxmit.put('FATAL ERROR: %s' % e.msg)
                except Exception as e:
                    self.logger.warn('command failure: %s', e)
                    self.qxmit.put('FATAL ERROR')
            else:
                self.process_queued_cmd(cmd)

    def process_string_cmd(self, cmdstr):
        cmd, *args = cmdstr.split(',')
        cmd = cmd.lower()

        if cmd == 'readhtrreg':
            htrId, name = args
            htrId = int(htrId)
            ret = self.heaters[htrId].dac.dac_read_register(name)
            self.qxmit.put(ret)
        elif cmd == 'setperiod':
            period, = args
            period = float(period)
            
            self.qxmit.put('OK')
        else:
            self.qxmit.put('UNKNOWN COMMAND: %s' % (cmdstr))
            
            
    def process_queued_cmd(self, cmd_dict):
        logging.debug('processing cmd: %s' % (cmd_dict))
        
        if cmd_dict['CMD_TYPE'] == '?':
            try:
                self.process_read_cmd(cmd_dict)
            except Exception as e:
                self.logger.warn('command failure: %s', e)
                self.qxmit.put('FATAL ERROR')
                
        elif cmd_dict['CMD_TYPE'] == '~':
            try:
                self.process_write_cmd(cmd_dict)
            except Exception as e:
                self.logger.warn('command failure: %s', e)
                self.qxmit.put('FATAL ERROR')
        else:
            cmd_dict['ERROR'] = -1
            output = "bad command"
            self.qxmit.put(output)

    def process_read_cmd(self, cmd_dict):
        output = 'ERROR'
        cmd = cmd_dict['CMD']
        p1 = cmd_dict['P1_DEF']
        p1min = cmd_dict["P1_MIN"]
        p1max = cmd_dict["P1_MAX"]

        if (p1min is not None and p1 < p1min) or (p1max is not None and p1 > p1max):
            self.logger.warn('cmd %s p1 arg is out of range', cmd)
            output = "OUT OF RANGE"
            self.qxmit.put(output)
            return -1

        if self.qxmit.full():
            self.logger.warn('qxmit full!')
            return -1

        # fetch Heater Mode (0=Disabled, 1=Fixed Percent, 2=PID Control)
        if cmd == 'L':
            htr_dict = quieres.db_fetch_heater_params(self.db, p1)
            output = str(htr_dict['mode'])

        # Return temperatures for all channels
        elif cmd == 't':
            readings = [("%0.4f" % self.tlm_dict['rtd%d' % i]) for i in range(1,13)]
            output = ','.join(readings)

        # Return raw data values for all channels
        elif cmd == 'd':
            readings = [("%d" % self.tlm_dict['adc_counts%d' % i]) for i in range(1,13)]
            output = ','.join(readings)

        # Return RTD Resistances for all channels
        elif cmd == 'r':
            readings = [("%0.4f" % self.tlm_dict['adc_sns_ohms%d' % i]) for i in range(1,13)]
            output = ','.join(readings)

        # Return RTD voltages for all channels
        elif cmd == 'v':
            readings = [("%0.4f" % self.tlm_dict['adc_sns_volts%d' % i]) for i in range(1,13)]
            output = ','.join(readings)

        # Read Board ID
        elif cmd == 'A':
            value = quieres.db_fetch_board_id(self.db)
            output = str("board_id = %s" % value)

        # Read Hi Power output state
        elif cmd == 'F':
            value = self.bb[p1-1].bang_bang_status()
            output = str(int(value))

        # Read Software Rev
        elif cmd == 'N':
            output = version.getRevision()

        # Read Temp Unit Setting (0=K 1=C 2=F).
        elif cmd == 'U':
            value_dict = quieres.db_adc_fetch_params(self.db, p1)
            output = str("Temp_unit = %s" % value_dict["temperature_unit"])

        # Read Sensor Type(1=PT100 2=PT1000 3=NCT_THERMISTOR)
        elif cmd == 'S':
            value_dict = quieres.db_adc_fetch_params(self.db, p1)
            output = str("sensor_type = %s" % value_dict["sensor_type"])

        # Read PID Proportional P factor.
        elif cmd == 'P':
            value_dict = quieres.db_fetch_heater_params(self.db, p1)
            output = str("P_term = %s" % value_dict["P"])

        # Read PID Integral I factor.
        elif cmd == 'I':
            value_dict = quieres.db_fetch_heater_params(self.db, p1)
            output = str("I_term = %s" % value_dict["I"])

        # Read PID Derivative D factor
        elif cmd == 'D':
            value_dict = quieres.db_fetch_heater_params(self.db, p1)
            output = str("D_term = %s" % value_dict["D"])

        # Read Heater Looop Set Point.
        elif cmd == 'W':
            value_dict = quieres.db_fetch_heater_params(self.db, p1)
            output = str("Set_pt= %s" % value_dict["set_pt"])

        # Read Heater Loop Control Sensor Number.
        elif cmd == 'J':
            value_dict = quieres.db_fetch_heater_params(self.db, p1)
            output = str(value_dict["ctrl_sensor"])

        # Read Heater Percent (%).
        elif cmd == 'V':
            value_dict = quieres.db_fetch_heater_params(self.db, p1)
            current = value_dict["htr_current"]
            output = str(current / self.heaters[0].maxTotalCurrent)
            
        # Read One Temp Sensor.
        elif cmd == 'K':
            output = "temp={0:3.3f}K".format(self.tlm_dict["rtd" + str(p1)])

        # Read Exciation Current Setting.
        elif cmd == 'X':
            setting_dict = quieres.db_adc_fetch_names_n_values(self.db, 'IOCon1', p1)
            value = setting_dict['iout0']
            output = "excitation_current_setting = %s" % value

        # Read Filter Type Setting.
        elif cmd == 'Q':
            setting_dict = quieres.db_adc_fetch_names_n_values(self.db, 'Filter_0', p1)
            value = setting_dict['filter']
            output = "filter_setting = %s" % value

        # Read sensor type connected to ADC.
        elif cmd == 'S':
            value_dict = quieres.db_fetch_heater_params(self.db, p1)
            output = str("sns_type = %s" % value_dict["sensor_type"])

        # Read Bang Bang Current
        elif cmd == "H":
            output = self.ads1015.read_data()

        # Read humidity sensor
        elif cmd == "H":
            output = str("cmd not yet implemented")

        else:
            output = 'UNKNOWN COMMAND: %s' % (cmd)

        if output == '':
            output = 'NO VALUE'
            
        self.qxmit.put(output)
        return 1

    def process_write_cmd(self, cmd_dict):
        cmd = cmd_dict['CMD']
        p1 = cmd_dict['P1_DEF']
        p2 = cmd_dict['P2_DEF']
        p1min = cmd_dict["P1_MIN"]
        p1max = cmd_dict["P1_MAX"]
        p2min = cmd_dict["P2_MIN"]
        p2max = cmd_dict["P2_MAX"]
        output =  '~' + cmd + ', ' + str(p1) +  ', ' + str(p2)

        if p1 < p1min or p1 > p1max or p2 < p2min or p2 > p2max:
            output = "bad command"
            self.qxmit.put(output)
            return -1

        # set heater mode
        if cmd == 'L':
            self.heaters[p1 - 1].set_htr_mode(p2)

        # Store Board ID
        elif cmd == 'A':
            quieres.db_update_board_id(self.db, p1)

        # Store Temp Unit (0=K;1=C;2=F)
        elif cmd == 'U':
            self.adcs[p1-1].adc_set_temp_units(p2)

        # Set Heater Current (Percent)
        elif cmd == 'V':
            self.heaters[p1 - 1].htr_set_heater_fraction(p2/100.0)

        # Store Excit uA (0=NONE,1=50,2=100,3=250,4=500,5=750, 6,7=1000)
        elif cmd == 'X':
            self.adcs[p1-1].set_exciatation_current(p2)

        # ADC Filter Setting
        # (0=sinc^4 1=rsv'd 2=sinc^3 3=rsv'd 4=fast sinc^4 5=fast sinc^3 6=rsv'd 7=post filter enabled
        elif cmd == 'Q':
            self.adcs[p1 - 1].set_filter_type(p2)

        # Heater P Setting
        elif cmd == 'P':
            quieres.db_update_htr_params(self.db, p2, 'P', p1)
            self.heaters[p1-1].heater_p_term = p2

        # Heater I Setting
        elif cmd == 'I':
            quieres.db_update_htr_params(self.db, p2, 'I', p1)
            self.heaters[p1 - 1].heater_i_term = p2

        # Heater D Setting
        elif cmd == 'D':
            quieres.db_update_htr_params(self.db, p2, 'D', p1)
            if p1 < len(self.heaters) + 1:
                self.heaters[p1 - 1].heater_d_term = p2

        # Heater Loop Control Sensor
        elif cmd == 'J':
            quieres.db_update_htr_params(self.db, p2, 'ctrl_sensor', p1)
            self.heaters[p1 - 1].heater_ctrl_sensor = p2

        # Set Heater Loop Setpoint
        elif cmd == 'W':
            quieres.db_update_htr_params(self.db, p2, 'set_pt', p1)
            self.heaters[p1 - 1].heater_set_pt = p2

        # Enable/disable High Power Output
        elif cmd == 'F':
            if int(p2) == 1:
                self.bb[p1-1].power_on_output()
            else:
                self.bb[p1 - 1].power_off_output()

        # set sensor type that is connected to ADC
        elif cmd == 'S':
            self.adcs[p1 - 1].adc_set_sensor_type(p2)

        # reboot rasberry pi
        elif cmd == 'E':
            os.system('sudo shutdown -r now')
            output = '~' + cmd

        else:
            self.logger.warn('UNKNOWN command: %s', cmd)
            raise ValueError('unknown command %s' % cmd)
        
        self.qxmit.put(output)
        return 1

#TODO: wire in command for reading humidity sensor
