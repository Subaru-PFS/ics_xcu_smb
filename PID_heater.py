from DAC8775 import DAC
import sqlite3

class PidHeater(object):
    """ pid_heater class """
    def __init__(self, idx, tlm_dict):
        dac=DAC(idx)
        self._heater_num = idx + 1
        self._heater_p_term = 1
        self._heater_i_term = 1
        self._heater_d_term = 1
        self._heater_percent = 0
        self._heater_mode = 0
        self._heater_ctrl_sensor = 0
        self._heater_set_pt = 0.0
        self.tlm_dict = tlm_dict
        self.db_get_heater_params()

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
    def heater_percent(self):
        print("Getting value")
        return self._heater_percent

    @heater_percent.setter
    def heater_percent(self, value):
        if value < 0 or value >= 100:
            raise ValueError("Heater percent value out of range")
        self._heater_percent = value

    def db_get_heater_params(self):
        con = sqlite3.connect("smb.db")
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM tblHtrParams WHERE PK_HTR_ID = " + str(self._heater_num))

        params = cur.fetchall()

        for param in params:
            if param is None:
                print("no records found")
            else:
                self._heater_p_term = param[1]
                self._heater_i_term = param[2]
                self._heater_d_term = param[3]
                self._heater_set_pt = param[4]
                self._heater_ctrl_sensor = param[5]
                self._heater_mode = param[6]
                self._heater_percent = param[7]
