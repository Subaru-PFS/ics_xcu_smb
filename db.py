import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtSql import *
# import itertools


class smb_db(object):

    def __init__(self):
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName("smb.db")

        if not self.db.open():
            result = QMessageBox.warning(None, 'Phone Log', "Database Error: %s" % self.db.lastError().text())
            print(result)
            sys.exit(1)

    def db_fetch_table_fields(self, tblname):
        query = QSqlQuery(self.db)
        qrytxt = "pragma table_info({tn})".format(tn=tblname)
        query.exec_(qrytxt)
        print(qrytxt)
        tblheader = []
        while query.next():
            tblheader.append(query.value(1))
        return tblheader

    def db_fetch_table_data(self, tblname):
        query = QSqlQuery(self.db)
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

    def db_table_data_to_dictionary(self, tblname):
        query = QSqlQuery(self.db)
        query.exec_("SELECT * FROM " + tblname)
        data_list = []
        column_names = self.db_fetch_table_fields(tblname)

        data_dict = {}
        data = []
        i = 0
        while query.next():
            for i in range(len(column_names)):
                data_dict[column_names[i]] = query.value(i)
                data_list.append(data_dict)
            data_dict = {}

        return data_list

    def db_fetch_tablenames(self):
        query = QSqlQuery(self.db)
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

    # <editor-fold desc="******* Heater Queries ********">

    def db_update_htr_params(self, value, name, htr_num):
        query = QSqlQuery(self.db)
        qrytxt = "UPDATE tblHtrParams SET {n} = {v}  WHERE PK_HTR_ID = {hn}". \
            format(n=name, v=value, hn=htr_num)
        query.exec_(qrytxt)

    def db_fetch_heater_params(self, heater_num):
        htr_param_dict = {}
        query = QSqlQuery(self.db)
        qrytxt = "SELECT * FROM tblHtrParams WHERE PK_HTR_ID = " + str(heater_num)
        query.exec_(qrytxt)
        fields = self.db_fetch_table_fields('tblHtrParams')
        while query.next():
            i = 0
            for field in fields:
                htr_param_dict[field] = query.value(i)
                i = i + 1
        return htr_param_dict

    # </editor-fold>

    # <editor-fold desc="******** ADC Queries ********************">

    def db_adc_update_register_field(self, field_name, sns_num, value):
        query = QSqlQuery(self.db)
        qrytxt = "UPDATE tblAdcRegBits{sn} SET value = {v} " \
                 "WHERE NAME = '{rf}'".format(sn=sns_num, v=value, rf=field_name)
        query.exec_(qrytxt)

    def db_adc_fetch_sensor_constants(self, sns_type):
        adc_sns_const_dict = {}
        query = QSqlQuery(self.db)
        qrytxt = "SELECT * FROM tblPolynomialCostants WHERE Device = '{st}' LIMIT 1".format(st=sns_type)
        query.exec_(qrytxt)

        fields = self.db_fetch_table_fields('tblPolynomialCostants')
        while query.next():
            i = 0
            for field in fields:
                adc_sns_const_dict[field] = query.value(i)
                i = i + 1

        return adc_sns_const_dict

    def db_adc_fetch_params(self, sensor_num):
        adc_param_dict = {}
        query = QSqlQuery(self.db)
        qrytxt = "SELECT * FROM tblAdcParams WHERE PK_ADC_ID = " + str(sensor_num)
        query.exec_(qrytxt)
        fields = self.db_fetch_table_fields('tblAdcParams')
        while query.next():
            i = 0
            for field in fields:
                adc_param_dict[field] = query.value(i)
                i = i + 1

        return adc_param_dict

    def db_adc_register_data_to_dictionary(self, regname, adc_num):
        tablename = 'tblAdcRegBits' + str(adc_num)
        query = QSqlQuery(self.db)

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

    def db_adc_fetch_names_n_values(self, regname, adc_num):

        query = QSqlQuery(self.db)
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

    # </editor-fold>

    def db_dac_register_data_to_dictionary(self, regname, dac_num):
        tablename = 'tblDacRegBits' + str(dac_num)
        query = QSqlQuery(self.db)

        qrytxt = "select {name}, {mask}, {shift}, {value} ,{parent} from {tn} inner join tblDacRegisters on " \
                 "{parent} = tblDacRegisters.ADDRESS where tblDacRegisters.NAME = '{rn}'"\
            .format(name=tablename + ".NAME", mask=tablename + ".MASK", shift=tablename + ".SHIFT",
                    value = tablename + ".VALUE",parent = tablename + ".FK_PARENT_ID", tn=tablename, rn=regname)
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
            data_dict={}
        return data

    def db_fetch_cmd_specifications(self, cmdchar):
        query = QSqlQuery(self.db)
        qrytxt = "select * from tblSmbCmds WHERE CMD = '{cc}'".format(cc=cmdchar)
        cmd_dict = {}
        query.exec_(qrytxt)
        fields = self.db_fetch_table_fields('tblSmbCmds')

        while query.next():
            i = 0
            for field in fields:
                cmd_dict[field] = query.value(i)
                i = i + 1

        return cmd_dict


    def __del__(self):
        self.db.close()


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
