import quieres

class sensor(object):
    def __init__(self, smbdb, sns_type_id):
        self.db = smbdb
        self.sns_id = sns_type_id
        const_dict = quieres.db_adc_fetch_sensor_constants(self.db, self.sns_id)
        self._c0 = const_dict['C0']
        self._c1 = const_dict['C1']
        self._c2 = const_dict['C2']
        self._c3 = const_dict['C3']
        self._c4 = const_dict['C4']
        self._c5 = const_dict['C5']
        self._c6 = const_dict['C6']
        self._c7 = const_dict['C7']
        self._device = const_dict['Device']

        self.c0 = self._c0
        self.c1 = self._c1
        self.c2 = self._c2
        self.c3 = self._c3
        self.c4 = self._c4
        self.c5 = self._c5
        self.c6 = self._c6
        self.c7 = self._c7

    @property
    def sensor_type(self):
        return self._device

    @sensor_type.setter
    def sensor_type(self, value):
        self._device = value

    @property
    def c0(self):
        return self._c0

    @c0.setter
    def c0(self, value):
        self._c0 = value

    @property
    def c1(self):
        return self._c1

    @c1.setter
    def c1(self, value):
        self._c1 = value

    @property
    def c2(self):
        return self._c2

    @c2.setter
    def c2(self, value):
        self._c2 = value

    @property
    def c3(self):
        return self._c3

    @c3.setter
    def c3(self, value):
        self._c3 = value

    @property
    def c4(self):
        return self._c4

    @c4.setter
    def c4(self, value):
        self._c4 = value

    @property
    def c5(self):
        return self._c5

    @c5.setter
    def c5(self, value):
        self._c5 = value

    @property
    def c6(self):
        return self._c6

    @c6.setter
    def c6(self, value):
        self._c6 = value

    @property
    def c7(self):
        return self._c7

    @c7.setter
    def c7(self, value):
        self._c7 = value
