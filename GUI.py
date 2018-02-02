#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 23 14:12:54 2018
"""
import sys
import Gbl
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
# from PyQt5.QtGui import QIcon


class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'Sensor Monitor Board'
        self.left = 20
        self.top = 40
        self.width = 640
        self.height = 480
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.GetIdbutton = QPushButton('Get ADC ID', self)
        self.GetIdbutton.setToolTip('This is an example button')
        self.GetIdbutton.move(100,70)
        self.GetIdbutton.clicked.connect(self.get_id_on_click)
        self.show()

    @pyqtSlot()
    def get_id_on_click(self):
        print('Getting 7124 ID')

