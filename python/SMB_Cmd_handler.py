"""
- Action Commands
CmdTyp | Cmd | P1      | P1 range | P2       | P2 Range  | Description
-------|-----|---------|----------|----------|-----------|-------------------------------------------
~      |  A  | uint    | 0 to 255 | n/a      | n/a       | Store Board ID
~      |  D  | LOOP#   | 1 to 2   | Value    | 0 to 100  | PID Derivative D factor
~      |  E  | n/A     | n/a      | n/A      | n/a       | Reset CPU
~      |  F  | ID      | 1 to  2  | state    | 0 t0 1    | Switched High Power output
~      |  I  | LOOP#   | 1 to 2   | Value    | 0 to 100  | PID Integral I factor
~      |  J  | LOOP#   | 1 to 2   | Value    | 1 to 12   | Loop control sensor#
~      |  L  | HtrEna  | 1 to 2   | /Dis Ena | 0,1,2     | 0=Disabled, 1=Fixed Percent, 2=PID Control
~      |  P  | LOOP#   | 1 to 2   | Value    | 0 to 100  | PID Proportional P factor
~      |  Q  | A/D #   | 1 to 12  | Fltr Val | 0 to 4    | ADC Filter Setting
~      |  S  | Sens#   | 1 to 12  | SnsType  | infinite  | Store Sensor Type (1=PT100 2=PT1000 3=NCT_THERMISTOR)
~      |  U  | Sens#'s | 12 bits  | Units    | 0,1,2     | Store Temperature Units (0=K;1=C;2=F)
~      |  V  | DAC#    | 1 to 2   | Value    | 0 to .1   | Set Heater Current (A)
~      |  W  | LOOP#   | 1 to 2   | Value    | -460->500 | Set LOOP SetPoint
~      |  X  | A/D #   | 1 to 12  | Current  | 0 to 7    | Store Excit uA(0=NONE,1=50,2=100,3=250,4=500,5=750, 6,7=1000)

- Query Commands
CmdType| Cmd | P1      | P1 range | Returns   | Range     | Description
-------|-----|---------|----------|-----------|-----------|-------------------------------------------
?      |  A  | uint    | 0 to 255 | Board ID  | n/a       | Read Board ID
?      |  D  | LOOP#   | 1 to 2   | D Value   | 0 to 100  | Read PID Derivative D factor
?      |  F  | ID      | 1 to  2  | Pwr Stat  | 0 to 1    | Read Switched High Power output Status
?      |  H  | n/A     | n/a      | Humidity  | 0 to 100% | Read Humidity Sensor (Humidity : Temp)
?      |  I  | LOOP#   | 1 to 2   | I Value   | 0 to 100  | Read PID Integral I factor
?      |  J  | LOOP#   | 1 to 2   | Loop Sns# | 1 to 12   | Read Loop control sensor#
?      |  K  | Sen#    | 1 to 12  | Temp      | +/-inf    | Read sensor temperature
?      |  L  | HtrEna  | 1 to 2   | Htr Stat  | 0,1,2     | Read Htr Amp status(0=Disabled,1=Fixed%, 2=PID ctrl)
?      |  N  | SW Ref  | n/a      | Rev       | n/a       | Read the software revision
?      |  P  | LOOP#   | 1 to 2   | P Value   | 0 to 100  | Read PID Proportional P factor
?      |  Q  | A/D #   | 1 to 12   | Fltr Val | 0 to 4    | Read Filter Setting
?      |  S  | Sens#   | 1 to 12  | SnsType   | 0,1,2,3   | Read SensorType (1=PT100 2=PT1000 3=NCT_THERMISTOR)
?      |  U  | Sens#   | 1 to 12  | Units     | 0,1,2     | Read Temperature Units(0=K;1=C;2=F)
?      |  V  | DAC#    | 1 to 2   | %         | 0 to .1   | Read Heater Current (A)
?      |  W  | LOOP#   | 1 to 2   | Value     | -460->500 | Read LOOP SetPoint
?      |  X  | A/D #   | 1 to 12  | Current   | 0 to 7    | Read Excit uA(0=NONE, 1=50,2=100,3=250,4=500,5=750 6,7=1000)
?      |  r  | n/a     | n/a	 | n/a       | n/a       | Read RTD Resistance at temperature
?      |  v  | n/a     | n/a      | n/a       | n/a       | Read RTD Voltage at temperature
?      |  t  | n/a     | n/a      | n/a       | n/a       | Read temperatures from all channels
"""
import re
import quieres


class SmbCmd(object):
    def __init__(self, smbdb):
        self.db = smbdb
        self.cmd_type = ''
        self.cmd = ''

    def parse_smb_cmd(self, cmdstr):
        cmdstr = cmdstr.strip()  # remove whitespace at end of cmdstring

        self.cmd_type = cmdstr[0:1]
        # search for the cmd char
        idx = 0
        for char in cmdstr:
            if char.isalpha():
                break
            idx += 1
        self.cmd = cmdstr[idx:idx+1]
        cmdparams = cmdstr[idx+1: len(cmdstr)]

        params = self.get_cmd_params(cmdparams)

        cmd_dict = quieres.db_fetch_cmd_specifications(self.db, self.cmd)
        cmd_dict['CMD'] = self.cmd
        cmd_dict['CMD_TYPE'] = self.cmd_type
        cmd_dict['P1_DEF'] = params[0]
        cmd_dict['P2_DEF'] = params[1]
        if 'P1_MIN' not in cmd_dict:
            cmd_dict['P1_MIN'] = None
        if 'P1_MAX' not in cmd_dict:
            cmd_dict['P1_MAX'] = None
        if self.cmd_type == '?' or self.cmd_type == '~':
            cmd_dict['ERROR'] = 0
        else:
            cmd_dict['ERROR'] = -1
        return cmd_dict

    def get_cmd_params(self, cmdstr):
        str_param1 = ""
        str_param2 = ""

        strlist = re.findall(r"[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", cmdstr)
        sublist1 = []
        itx = 0
        for item in strlist:
            if item != "," and item != ", " and item != '\s':
                sublist1.append(item)
                itx += 1
        param1 = 0
        param2 = 0.0
        if itx > 0:
            for c in sublist1[0]:
                if c.isdigit() or (c == '.') or (c == '+') or (c == '-'):  # make sure it is a number or decimal
                    str_param1 = str_param1 + c  # if it is a number add it to cmdstr
            param1 = int(str_param1)
        if itx > 1:
            for c in sublist1[1]:
                if c.isdigit() or (c == '.') or (c == '+') or (c == '-'):  # make sure it is a number or decimal
                    str_param2 = str_param2 + c  # if it is a number add it to cmdstr
            param2 = float(str_param2)

        return param1, param2
