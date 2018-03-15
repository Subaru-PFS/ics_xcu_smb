class sensor(object):
    def __init__(self):
        self._const_0 = 0.0
        self._const_1 = 0.0
        self._const_2 = 0.0
        self._const_3 = 0.0
        self._const_4 = 0.0
        self._const_5 = 0.0
        self._const_6 = 0.0
        self._const_7 = 0.0
        self._sensor_type = 'PT1000'

    @property
    def sensor_type(self):
        return self._sensor_type

    @sensor_type.setter
    def sensor_type(self, value):
        self._sensor_type = value

    @property
    def const_0(self):
        return self._const_0

    @const_0.setter
    def const_0(self, value):
        self._const_0 = value

    @property
    def const_1(self):
        return self._const_1

    @const_1.setter
    def const_1(self, value):
        self._const_1 = value

    @property
    def const_2(self):
        return self._const_2

    @const_2.setter
    def const_2(self, value):
        self._const_2 = value

    @property
    def const_3(self):
        return self._const_3

    @const_3.setter
    def const_3(self, value):
        self._const_3 = value

    @property
    def const_4(self):
        return self._const_4

    @const_4.setter
    def const_4(self, value):
        self._const_4 = value

    @property
    def const_5(self):
        return self._const_5

    @const_5.setter
    def const_5(self, value):
        self._const_5 = value

    @property
    def const_6(self):
        return self._const_6

    @const_6.setter
    def const_6(self, value):
        self._const_6 = value

    @property
    def const_7(self):
        return self._const_7

    @const_7.setter
    def const_7(self, value):
        self._const_7 = value
