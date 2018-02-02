#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 24 12:49:52 2018

@author: pi
"""
# sys.path.append('/home/pi/Documents/Spyder3 Projects/ICS_SMB/Python/ICS_SMB/Drivers/')
import Drivers.AD7124
from xml.dom import minidom
import Gbl

class ADC(object):
    """ ADC Class """
    def __init__(self, idx, sns_type="DT670", adc_filter=0):
        self._sens_num = idx + 1
        self._sns_type=sns_type
        self._adc_filter=adc_filter
        self.adc_reset()

    @property
    def sns_type(self):
        print("Getting value")
        return self._sns_type

    @sns_type.setter
    def sns_type(self, value):
        if value != "DT670" or value != "RTD" or value != "RAW":
            raise ValueError("Invalid Sensor Type")
        self._sns_type = value

    @property
    def adc_filter(self):
        print("Getting value")
        return self._adc_filter

    @adc_filter.setter
    def adc_filter(self, value):
        if value < 0 or value > 7:
            raise ValueError("Filter val out of range")
        self._adc_filter = value


    def adc_select(self):
        """ Select ADC for this object """
        print("selected ADC: %s" % (self._sens_num))

    def adc_reset(self):
        """ Reset the ADC """
        self.adc_select()
        Drivers.AD7124.reset()

    def GetAdcParams(self):
        xmldoc = minidom.parse('ADC_Chan_params.xml')
        paramlist = xmldoc.getElementsByTagName('channel')
        print(len(Gbl.paramlist))
        print(paramlist[self.sns_num-1].attributes['sns_type'].value)

