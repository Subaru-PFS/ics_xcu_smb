#!/usr/bin/python
# -*- coding: utf-8 -*-
import sqlite3
import sys
import Gbl


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


def get_next_cmd_from_queue(conn):
    """
    Query tasks by priority
    :param conn: the Connection object
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT * from (SELECT * FROM tblCmdQueue Where cmd_complete is NULL\
                  order by datetime_recvd desc)\
                LIMIT 1")

    rows = cur.fetchall()

    for row in rows:
        if row is None:
            print("no records found")
        else:
            print(row)


def populate_cmd_list():
    conn = sqlite3.connect("smb.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM tblSmbCmds")

    Gbl.cmdlist = cur.fetchall()
    conn.close()
    for cmd in Gbl.cmdlist:
        if cmd is None:
            print("no records found")
        else:
            pass
            # print(cmd)
