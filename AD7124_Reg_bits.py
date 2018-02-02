#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 22 15:29:23 2018

@author: pi

Dictionary of AD7124 Register bits
"""

RegBits = [
    {'reg_name': 'Comm','func_name': "AD7124_COMM_REG_WEN",
     'bitpol':0,'shift': 7, 'mask': 0xff},
    {'reg_name': 'Comm','func_name': "AD7124_COMM_REG_WR",
     'bitpol':0,'shift': 6, 'mask': 0xff},
    {'reg_name': 'Comm','func_name': "AD7124_COMM_REG_RD",
     'bitpol':1,'shift': 6, 'mask': 0xff},
    {'reg_name': 'Comm','func_name': "AD7124_COMM_REG_RA",
     'bitpol':0,'shift': 0, 'mask': 0x3f},
    {'reg_name': 'Status','func_name': "AD7124_STATUS_REG_RDY",
     'bitpol':1,'shift': 7, 'mask': 0xff},
    {'reg_name': 'Status','func_name': "AD7124_STATUS_REG_ERROR_FLAG",
     'bitpol':1,'shift': 6,'mask': 0xff},
    {'reg_name': 'Status','func_name': "AD7124_STATUS_REG_POR_FLAG",
     'bitpol':1,'shift': 4,'mask': 0xff},
    {'reg_name': 'Status','func_name': "AD7124_STATUS_REG_CH_ACTIVE",
     'bitpol':1,'shift': 0,'mask': 0xf},
    ]