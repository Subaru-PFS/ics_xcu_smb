#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""


Created on Thu Jan 25 08:38:35 2018

@author: pi
"""
""" SPI buses """
spi0 = None
spi1 = None
""" list that holds the 12 ADC objects """
adc = []
""" reference to the GUI application """
app = None
""" List of SMB Commands """
cmdlist=[]

"""Commands to be executed"""
cmd_queue=None
