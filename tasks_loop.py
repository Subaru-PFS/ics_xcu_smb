import threading
import time
import natsort
import db


class DoTasks(threading.Thread):
    def __init__(self, tlm_dict, adcs, heaters, qcommand, qtransmit):
        self.tlm_dict = tlm_dict
        self.adcs = adcs
        self.heaters = heaters
        self.qcmd = qcommand
        self.qxmit = qtransmit
        threading.Thread.__init__(self)

    def run(self):
        try:
            while True:
                # See if there is command to execute.
                if not self.qcmd.empty():
                    self.process_queued_cmd(self.qcmd.get())
                    self.qcmd.task_done()

                # Read out ADC conversion data
                for adc in self.adcs:
                    adc.read_conversion_data()

                time.sleep(.5)
                # for key, value in self.tlm_dict.items():
                #     if key.lower() == 'rtd1' or key == 'rtd2':
                #         print(key, value)

        except KeyboardInterrupt:  # Ctrl+C pressed
            del self

    def process_queued_cmd(self, cmd_dict):

        try:
            if cmd_dict['ERROR'] < 0:
                raise ValueError('Invalid Command', cmd_dict['CMD'], "error=" + cmd_dict['ERROR'])
            else:
                if cmd_dict['CMD_TYPE'] == '?' and cmd_dict["READ"] == 1:
                    result = self.process_read_cmd(cmd_dict)
                elif cmd_dict['CMD_TYPE'] == '~' and cmd_dict["WRITE"] == 1:
                    result = self.process_write_cmd(cmd_dict)
                else:
                    cmd_dict['ERROR'] = -1
                    raise ValueError

            if result < 0:
                raise ValueError

        except ValueError as err:
            print(err.args)

    def process_read_cmd(self, cmd_dict):
        output = ''
        if not self.qxmit.full():
            if cmd_dict['CMD'] == 'L':
                htr_dict = db.db_fetch_heater_params(cmd_dict['P1_DEF'])
                output = str(htr_dict['mode']) + '\r\n'

            elif cmd_dict['CMD'] == 't':
                for item in natsort.natsorted(self.tlm_dict):
                    if 'rtd' in item:
                        output += item + " = {0:3.3f}K\r\n".format(self.tlm_dict[item])

            elif cmd_dict['CMD'] == 'r':
                for item in natsort.natsorted(self.tlm_dict):
                    if 'rtd' in item:
                        output += item + " = {0:3.1f}ohms\r\n".format(self.tlm_dict[item])
            else:
                return -1

            self.qxmit.put(output.encode('utf-8'))
            return 1

    def process_write_cmd(self, cmd_dict):
        if cmd_dict['CMD'] == 'L':
            state = bool(int(cmd_dict['P2_DEF']))
            if state is True:
                self.heaters[cmd_dict['P1_DEF'] - 1].htr_enable_heater_current(True)
            else:
                self.heaters[cmd_dict['P1_DEF'] - 1].htr_enable_heater_current(False)

        elif cmd_dict['CMD'] == 'V':
            self.heaters[cmd_dict['P1_DEF'] - 1].htr_set_heater_current(cmd_dict['P2_DEF'])
        elif cmd_dict['CMD'] == 'X':
            adc_id = cmd_dict["P1_DEF"]
            self.adcs[adc_id-1].set_exciatation_current(cmd_dict['P2_DEF'])
        elif cmd_dict['CMD'] == 'Q':
            adc_id = cmd_dict["P1_DEF"]
            self.adcs[adc_id - 1].set_filter_type(cmd_dict['P2_DEF'])
        else:
            return -1
        return 1

