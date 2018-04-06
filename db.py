#!/usr/bin/python
# -*- coding: utf-8 -*-
import sqlite3
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import itertools


def get_sqlite_ver():
    try:
        con = sqlite3.connect('smb.db')
        cur = con.cursor()
        cur.execute('SELECT SQLITE_VERSION()')
        data = cur.fetchone()
        print("SQLite version: %s" % data)
    except sqlite3.Error as e:
        print("Error %s:" % e.args[0])
        sys.exit(1)
    finally:
        if con:
            con.close()


class DbTableModel(QAbstractTableModel):
    def __init__(self, datain, headerdata, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        QAbstractTableModel.__init__(self, parent)
        self.arraydata = datain
        self.headerdata = headerdata

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        if len(self.arraydata) > 0:
            return len(self.arraydata[0])
        return 0

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != Qt.DisplayRole:
            return None
        return str(self.arraydata[index.row()][index.column()])

    def setData(self, index, value, role):
        pass         # not sure what to put here

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return str(self.headerdata[col])
        return None

    def sort(self, Ncol, order):
        """
        Sort table by given column number.
        """
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))
        if order == Qt.DescendingOrder:
            self.arraydata.reverse()
        self.emit(SIGNAL("layoutChanged()"))


def config_table(tv, tblheader, tabledata):
    # set the table model
    tablemodel = DbTableModel(tabledata, tblheader)
    tv.setModel(tablemodel)
    # set the minimum size
    tv.setMinimumSize(400, 300)
    # hide grid
    tv.setShowGrid(True)
    # hide vertical header
    vh = tv.verticalHeader()
    vh.setVisible(False)
    # set horizontal header properties
    hh = tv.horizontalHeader()
    hh.setStretchLastSection(True)
    # set column width to fit contents
    tv.resizeColumnsToContents()
    # set row height
    tv.resizeRowsToContents()
    # enable sorting
    tv.setSortingEnabled(False)


def db_fetch_table_data(tblname):
    conn = sqlite3.connect("smb.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM " + tblname)
    data = cur.fetchall()
    conn.close()
    return data


def db_fetch_tablenames():
    con = sqlite3.connect('smb.db')
    cursor = con.cursor()
    qrytxt = ("SELECT name FROM sqlite_master "
              "WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' "
              "UNION ALL "
              "SELECT name FROM sqlite_temp_master "
              "WHERE type IN ('table','view') ORDER BY 1")
    cursor.execute(qrytxt)
    tblnames = cursor.fetchall()
    return tblnames


def db_fetch_table_fields(tblname):
    connection = sqlite3.connect('smb.db')
    cursor = connection.execute('select * from ' + tblname)
    tblheader = list(map(lambda x: x[0], cursor.description))
    return tblheader


def db_fetch_cmd_specifications(cmdchar):
    # Builds a dict of dicts from garden sqlite db
    cmd_dict = {}
    conn = sqlite3.connect("smb.db")
    # Need to allow write permissions by others
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    qry = "select * from tblSmbCmds WHERE CMD = " + "'" +  cmdchar + "'"
    c.execute(qry)
    tuple_list = c.fetchall()
    conn.close()
    # Building dict from table rows
    fields = db_fetch_table_fields('tblSmbCmds')
    for item in tuple_list:
        i = 0
        for field in fields:
            cmd_dict[field] = item[i]
            i = i + 1

    return cmd_dict


# <editor-fold desc="******* Heater Queries ********">

def db_update_htr_params(value, name, tablename):
    con = sqlite3.connect("smb.db")
    cur = con.cursor()
    qrytxt = "UPDATE {tn} SET {n} = {v}  WHERE PK_HTR_ID = 1". \
        format(tn=tablename, n=name, v=value)
    cur.execute(qrytxt)
    con.commit()
    con.close()


def db_fetch_heater_params(heater_num):
    # Builds a dict of dicts from garden sqlite db
    htr_param_dict = {}
    conn = sqlite3.connect("smb.db")
    # Need to allow write permissions by others
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    qry = "SELECT * FROM tblHtrParams WHERE PK_HTR_ID = " + str(heater_num)
    c.execute(qry)
    tuple_list = c.fetchall()
    conn.close()
    fields = db_fetch_table_fields('tblHtrParams')
    for item in tuple_list:
        i = 0
        for field in fields:
            htr_param_dict[field] = item[i]
            i = i + 1
    return htr_param_dict

# </editor-fold>

# <editor-fold desc="*************** DAC Queries **************">

def db_dac_register_data_to_dictionary(regname):
    # Builds a dict of dicts from garden sqlite db
    conn = sqlite3.connect("smb.db")
    # Need to allow write permissions by others
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    qry = "select tblDacRegBits.NAME, tblDacRegBits.MASK, tblDacRegBits.SHIFT, tblDacRegBits.VALUE," \
          " tblDacRegBits.FK_PARENT_ID from tblDacRegBits inner join tblDacRegisters" \
          " on tblDacRegBits.FK_PARENT_ID = tblDacRegisters.ADDRESS where tblDacRegisters.NAME = " + "'" + regname + "'"

    c.execute(qry)
    desc = c.description
    column_names = [col[0] for col in desc]
    data = [dict(itertools.zip_longest(column_names, row))
            for row in c]
    conn.close()
    return data


# </editor-fold>

# <editor-fold desc="******** ADC Queries ********************">

def db_adc_fetch_params(sensor_num):
    # Builds a dict of dicts from garden sqlite db
    adc_param_dict = {}
    conn = sqlite3.connect("smb.db")
    # Need to allow write permissions by others
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    qry = "SELECT * FROM tblAdcParams WHERE PK_ADC_ID = " + str(sensor_num)
    c.execute(qry)
    tuple_list = c.fetchall()
    conn.close()
    # Building dict from table rows
    fields = db_fetch_table_fields('tblAdcParams')
    for item in tuple_list:
        i = 0
        for field in fields:
            adc_param_dict[field] = item[i]
            i = i + 1

    return adc_param_dict


def db_adc_fetch_sensor_constants(sns_type):
    # Builds a dict of dicts from garden sqlite db
    adc_sns_const_dict = {}
    conn = sqlite3.connect("smb.db")
    # Need to allow write permissions by others
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    qry = "SELECT * FROM tblPolynomialCostants WHERE Device = " + "'" + sns_type + "'" + " LIMIT 1"
    c.execute(qry)
    tuple_list = c.fetchall()
    conn.close()
    # Building dict from table rows
    fields = db_fetch_table_fields('tblPolynomialCostants')

    for item in tuple_list:
        i = 0
        for field in fields:
            adc_sns_const_dict[field] = item[i]
            i = i + 1

    return adc_sns_const_dict


def db_table_data_to_dictionary(tblname):
    # Builds a dict of dicts from garden sqlite db
    conn = sqlite3.connect("smb.db")
    # Need to allow write permissions by others
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    qry = 'select * from ' + tblname
    c.execute(qry)
    desc = c.description
    column_names = [col[0] for col in desc]
    data = [dict(itertools.zip_longest(column_names, row))
            for row in c]
    conn.close()
    return data


def db_adc_register_data_to_dictionary(regname, adc_num):
    # Builds a dict of dicts from garden sqlite db
    conn = sqlite3.connect("smb.db")
    # Need to allow write permissions by others
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    tablename='tblAdcRegBits' + str(adc_num)
    name = tablename + ".NAME"
    shift = tablename + ".SHIFT"
    mask = tablename + ".MASK"
    value = tablename + ".VALUE"
    parent = tablename + ".FK_PARENT_ID"

    qry = "select " + name + ", " + mask  + ", " +  shift  + ", " + value + ", " +  parent + " from " + tablename \
          + " inner join tblAdcRegisters" \
          " on " + parent + " = tblAdcRegisters.ADDRESS where tblAdcRegisters.NAME = " + "'" + regname + "'"
    # print(qry)
    c.execute(qry)
    desc = c.description
    column_names = [col[0] for col in desc]
    data = [dict(itertools.zip_longest(column_names, row))
            for row in c]
    conn.close()
    return data


def db_fetch_names_n_values(tblname):
    # Builds a dict of dicts from garden sqlite
    conn = sqlite3.connect("smb.db")
    # Need to allow write permissions by others
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    qry = 'select NAME, VALUE from ' + tblname
    c.execute(qry)
    things = [dict(itertools.zip_longest(['NAME', 'VALUE'], row)) for row in c.fetchall()]
    regdict = {}
    for thing in things:
        regdict[thing['NAME']] = thing['VALUE']

    return regdict


def db_fetch_names_n_values(regname, adc_num):
    # Builds a dict of dicts from garden sqlite
    conn = sqlite3.connect("smb.db")
    # Need to allow write permissions by others
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    tablename = 'tblAdcRegBits' + str(adc_num)
    name = tablename + ".NAME"
    shift = tablename + ".SHIFT"
    mask = tablename + ".MASK"
    value = tablename + ".VALUE"
    parent = tablename + ".FK_PARENT_ID"

    qry = "select " + name +  ", " + value + " from " + tablename + " inner join tblAdcRegisters on " \
          + parent + "= tblAdcRegisters.ADDRESS where tblAdcRegisters.NAME = " + "'" + regname + "'"
    c.execute(qry)
    things = [dict(itertools.zip_longest(['NAME', 'VALUE'], row)) for row in c.fetchall()]
    regdict = {}
    for thing in things:
        regdict[thing['NAME']] = thing['VALUE']

    return regdict

# </editor-fold>
