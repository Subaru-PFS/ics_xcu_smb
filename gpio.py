#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 08:52:18 2018

@author: joe orndorff
"""
from time import sleep
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!  This is probably because you need \
          superuser privileges.  You can achieve this by using 'sudo' to\
          run your script")


class gpio(object):
    def __init__(self):
        print("gpio init")
        print(GPIO.RPI_INFO)
        print(GPIO.getmode())
        GPIO.setmode(GPIO.BCM)
        print(GPIO.getmode())
        
    def GpioToggleTest(self):
        channel=26
        sleep(3)
        GPIO.setup(channel, GPIO.OUT)
        for i in range(0,5):
            GPIO.output(channel, 0)
            if GPIO.input(channel):
                print('output was HIGH')
            else:
                print('Output was LOW')
            sleep(1)
            GPIO.output(channel, 1)
            if GPIO.input(channel):
                print('output was HIGH')
            else:
                print('putput was LOW')
            sleep(1)
        GPIO.output(channel, 0)
        