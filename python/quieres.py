import logging

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSql import QSqlQuery

dbLogger = logging.getLogger('db')
dbLogger.setLevel(logging.INFO)

def db_table_data_to_dictionary(db, tblname):
    query = QSqlQuery(db)
    query.exec_("SELECT * FROM " + tblname)
    data_list = []
    column_names = db_fetch_table_fields(db,tblname)

    data_dict = {}
    data = []
    i = 0
    while query.next():
        for i in range(len(column_names)):
            data_dict[column_names[i]] = query.value(i)
            data_list.append(data_dict)
        data_dict = {}

    return data_list

def db_fetch_table_fields(db, tblname):
    # returns a list of coulumn (field) names
    query = QSqlQuery(db)
    qrytxt = "pragma table_info({tn})".format(tn=tblname)
    query.exec_(qrytxt)
    tblheader = []
    while query.next():
        tblheader.append(query.value(1))
    return tblheader

def db_dac_fetch_names_n_values(db, regname, dac_num):
    query = QSqlQuery(db)
    tablename = 'tbldacRegBits' + str(dac_num)

    qrytxt = "select {name}, {value} from {tn} inner join tbldacRegisters on {parent} = tbldacRegisters.ADDRESS " \
             "where tbldacRegisters.NAME = '{rn}'".format(name=tablename + ".NAME",
                                                          value=tablename + ".VALUE",
                                                          tn=tablename, parent=tablename + ".FK_PARENT_ID",
                                                          rn=regname)
    query.exec_(qrytxt)
    regdict = {}
    while query.next():
        regdict[query.value(0)] = query.value(1)
    return regdict

def db_dac_register_data_to_dictionary(db, regname, dac_num):
    tablename = 'tbldacRegBits' + str(dac_num)
    query = QSqlQuery(db)

    qrytxt = "select {name}, {mask}, {shift}, {value} ,{parent} from {tn} inner join tbldacRegisters on " \
             "{parent} = tbldacRegisters.ADDRESS where tbldacRegisters.NAME = '{rn}'" \
        .format(name=tablename + ".NAME", mask=tablename + ".MASK", shift=tablename + ".SHIFT",
                value=tablename + ".VALUE", parent=tablename + ".FK_PARENT_ID", tn=tablename, rn=regname)
    data_dict = {}
    data = []
    query.exec_(qrytxt)

    while query.next():
        data_dict["NAME"] = query.value(0)
        data_dict["MASK"] = query.value(1)
        data_dict["SHIFT"] = query.value(2)
        data_dict["VALUE"] = query.value(3)
        data_dict["PK_PAPRENT_ID"] = query.value(4)

        data.append(data_dict)
        data_dict = {}
    return data

def db_fetch_heater_params(db, heater_num):
    htr_param_dict = {}
    query = QSqlQuery(db)
    qrytxt = "SELECT * FROM tblHtrParams WHERE PK_HTR_ID = " + str(heater_num)
    query.exec_(qrytxt)
    fields = db_fetch_table_fields(db, 'tblHtrParams')
    while query.next():
        i = 0
        for field in fields:
            htr_param_dict[field] = query.value(i)
            i = i + 1
    return htr_param_dict

def db_adc_fetch_params(db, sensor_num):
    adc_param_dict = {}
    query = QSqlQuery(db)
    qrytxt = "SELECT * FROM tblAdcParams WHERE PK_ADC_ID = " + str(sensor_num)
    query.exec_(qrytxt)
    fields = db_fetch_table_fields(db, 'tblAdcParams')
    while query.next():
        i = 0
        for field in fields:
            adc_param_dict[field] = query.value(i)
            i = i + 1

    return adc_param_dict

def db_adc_fetch_names_n_values(db, regname, adc_num):
    # Retrive sub register names and values for a given register.
    query = QSqlQuery(db)
    tablename = 'tblAdcRegBits' + str(adc_num)

    qrytxt = "select {name}, {value} from {tn} inner join tblAdcRegisters on {parent} = tblAdcRegisters.ADDRESS " \
             "where tblAdcRegisters.NAME = '{rn}'".format(name=tablename + ".NAME",
                                                          value=tablename + ".VALUE",
                                                          tn=tablename, parent=tablename + ".FK_PARENT_ID",
                                                          rn=regname)
    query.exec_(qrytxt)
    regdict = {}

    while query.next():
        regdict[query.value(0)] = query.value(1)

    return regdict

def db_adc_register_data_to_dictionary(db, regname, adc_num):
    tablename = 'tblAdcRegBits' + str(adc_num)
    query = QSqlQuery(db)

    qrytxt = "select {name}, {mask}, {shift}, {value} ,{parent} from {tn} inner join tblAdcRegisters on " \
             "{parent} = tblAdcRegisters.ADDRESS where tblAdcRegisters.NAME = '{rn}'" \
        .format(name=tablename + ".NAME", mask=tablename + ".MASK", shift=tablename + ".SHIFT",
                value=tablename + ".VALUE", parent=tablename + ".FK_PARENT_ID", tn=tablename, rn=regname)
    data_dict = {}
    data = []
    query.exec_(qrytxt)

    while query.next():
        data_dict["NAME"] = query.value(0)
        data_dict["MASK"] = query.value(1)
        data_dict["SHIFT"] = query.value(2)
        data_dict["VALUE"] = query.value(3)
        data_dict["PK_PAPRENT_ID"] = query.value(4)

        data.append(data_dict)
        data_dict = {}
    return data

def db_adc_fetch_sensor_constants(db, sns_type):
    adc_sns_const_dict = {}
    query = QSqlQuery(db)
    qrytxt = "SELECT * FROM tblSensorData WHERE PK_DEV_ID = '{st}' LIMIT 1".format(st=sns_type)
    query.exec_(qrytxt)

    fields = db_fetch_table_fields(db, 'tblSensorData')
    while query.next():
        i = 0
        for field in fields:
            adc_sns_const_dict[field] = query.value(i)
            i = i + 1

    return adc_sns_const_dict

def db_ads1015_fetch_names_n_values(db, regname):

    query = QSqlQuery(db)
    tablename = 'tblADS1015RegBits'

    qrytxt = "select {name}, {value} from {tn} inner join tblADS1015Registers on {parent} = tblADS1015Registers.ADDRESS " \
             "where tblADS1015Registers.NAME = '{rn}'".format(name=tablename + ".NAME",
                                                          value=tablename + ".VALUE",
                                                          tn=tablename, parent=tablename + ".FK_PARENT_ID",
                                                          rn=regname)
    query.exec_(qrytxt)
    regdict = {}

    while query.next():
        regdict[query.value(0)] = query.value(1)

    return regdict

def db_ads1015_register_data_to_dictionary(db, regname):
    tablename = 'tblADS1015RegBits'
    query = QSqlQuery(db)

    qrytxt = "select {name}, {mask}, {shift}, {value} ,{parent} from {tn} inner join tblADS1015Registers on " \
             "{parent} = tblADS1015Registers.ADDRESS where tblADS1015Registers.NAME = '{rn}'" \
        .format(name=tablename + ".NAME", mask=tablename + ".MASK", shift=tablename + ".SHIFT",
                value=tablename + ".VALUE", parent=tablename + ".FK_PARENT_ID", tn=tablename, rn=regname)
    data_dict = {}
    data = []
    query.exec_(qrytxt)

    while query.next():
        data_dict["NAME"] = query.value(0)
        data_dict["MASK"] = query.value(1)
        data_dict["SHIFT"] = query.value(2)
        data_dict["VALUE"] = query.value(3)
        data_dict["PK_PAPRENT_ID"] = query.value(4)

        data.append(data_dict)
        data_dict = {}
    return data

def db_update_htr_params(db, value, name, htr_num):
    query = QSqlQuery(db)
    qrytxt = "UPDATE tblHtrParams SET {n} = {v}  WHERE PK_HTR_ID = {hn}". \
        format(n=name, v=value, hn=htr_num)
    dbLogger.info(qrytxt)
    query.exec_(qrytxt)

def db_fetch_board_id(db):
    query = QSqlQuery(db)
    qrytxt = "SELECT VALUE from tblSmbParams WHERE NAME= \'BOARD_ID\'"
    query.exec_(qrytxt)
    if query.first():
        id = query.value(0)
    query.clear()
    return id

def db_fetch_tablenames(db):
    # returns a list of all tablenames in the database
    query = QSqlQuery(db)
    qrytxt = ("SELECT name FROM sqlite_master "
              "WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' "
              "UNION ALL "
              "SELECT name FROM sqlite_temp_master "
              "WHERE type IN ('table','view') ORDER BY 1")
    query.exec_(qrytxt)
    print(qrytxt)
    list = []
    while query.next():
        list.append(query.value(0))
    return list

def db_fetch_table_data(db, tblname):
    query = QSqlQuery(db)
    query.exec_("SELECT * FROM " + tblname)
    data_list = []
    while query.next():
        i = 0
        data = {}
        while query.value(i) is not None:
            data[i] = query.value(i)
            i += 1
        data_list.append(data)
    return data_list

def db_update_adc_params(db, value, name, adc_num):
    query = QSqlQuery(db)
    qrytxt = "UPDATE tblAdcParams SET {n} = {v}  WHERE PK_ADC_ID = {an}". \
        format(n=name, v=value, an=adc_num)
    dbLogger.info(qrytxt)
    query.exec_(qrytxt)

def db_adc_update_register_field(db, field_name, sns_num, value):
    query = QSqlQuery(db)
    qrytxt = "UPDATE tblAdcRegBits{sn} SET value = {v} " \
             "WHERE NAME = '{rf}'".format(sn=sns_num, v=value, rf=field_name)
    dbLogger.info(qrytxt)
    query.exec_(qrytxt)

def db_fetch_cmd_specifications(db, cmdchar):
    query = QSqlQuery(db)
    qrytxt = "select * from tblSmbCmds WHERE CMD = '{cc}'".format(cc=cmdchar)
    cmd_dict = {}
    query.exec_(qrytxt)
    fields = db_fetch_table_fields(db, 'tblSmbCmds')

    while query.next():
        i = 0
        for field in fields:
            cmd_dict[field] = query.value(i)
            i = i + 1

    return cmd_dict

def db_update_board_id(db, value):
    query = QSqlQuery(db)
    qrytxt = "UPDATE tblSmbParams SET VALUE = {v}  WHERE NAME = \'BOARD_ID\'".format(v=value)
    dbLogger.info(qrytxt)
    query.exec_(qrytxt)
    query.clear()

def db_update_board_swrev(db, value):
    query = QSqlQuery(db)
    qrytxt = "UPDATE tblSmbParams SET VALUE = {v}  WHERE NAME = \'SOFTWARE_REV\'".format(v=value)
    dbLogger.info(qrytxt)
    query.exec_(qrytxt)
    query.clear()

def db_software_rev(db):
    query = QSqlQuery(db)
    qrytxt = "SELECT VALUE from tblSmbParams WHERE NAME= \'SOFTWARE_REV\'"
    query.exec_(qrytxt)
    if query.first():
        id = query.value(0)
    query.clear()
    return id



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
