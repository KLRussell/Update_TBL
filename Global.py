from pandas.io import sql
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus

import pathlib as pl
import pandas as pd
import sqlalchemy as mysql
import shelve
import pyodbc
import os
import datetime
import logging


def grabobjs(scriptdir):
    if scriptdir and os.path.exists(scriptdir):
        myobjs = dict()

        if len(list(pl.Path(scriptdir).glob('General_Settings.*'))) > 0:
            myobjs['Settings'] = ShelfHandle(os.path.join(scriptdir, 'General_Settings'))
        elif len(list(pl.Path(scriptdir).glob('Script_Settings.*'))) > 0:
            myobjs['Local_Settings'] = ShelfHandle(os.path.join(scriptdir, 'Script_Settings'))
            myobjs['Settings'] = myobjs['Local_Settings'].grab_item('General_Settings_Path')
        else:
            myinput = None
            while not myinput:
                print("Please input a directory path where to setup general settings at:")
                myinput = input()

                if myinput and not os.path.exists(myinput):
                    myinput = None

            if myinput == scriptdir:
                myobjs['Settings'] = ShelfHandle(os.path.join(scriptdir, 'General_Settings'))
            else:
                myobjs['Local_Settings'] = ShelfHandle(os.path.join(scriptdir, 'Script_Settings'))
                myobjs['Local_Settings'].add_item('General_Settings_Path', myinput)
                myobjs['Settings'] = ShelfHandle(os.path.join(myinput, 'General_Settings'))

        myobjs['Event_Log'] = LogHandle(scriptdir)
        myobjs['SQL'] = SQLHandle(myobjs['Settings'])
        myobjs['Errors'] = ErrHandle(myobjs['Event_Log'])

        return myobjs
    else:
        raise Exception('Invalid script path provided')


class ShelfHandle:
    def __init__(self, filepath=None):
        self.filepath = filepath

    def change_config(self, filepath):
        self.filepath = filepath

    def get_shelf_path(self):
        return self.filepath

    def grab_item(self, key):
        if self.filepath and os.path.exists(self.filepath):
            sfile = shelve.open(self.filepath)
            type(sfile)

            if key in sfile.keys():
                myitem = sfile[key]
            else:
                myitem = None

            sfile.close()

            return myitem

    def add_item(self, key, val=None, inputmsg=None):
        if self.filepath and os.path.exists(self.filepath) and key:
            sfile = shelve.open(self.filepath)
            type(sfile)

            if key not in sfile.keys():
                if not val:
                    myinput = None

                    while not myinput:
                        if inputmsg:
                            print(inputmsg)
                        else:
                            print("Please input value for {}:".format(key))
                        myinput = input()

                    sfile[key] = myinput
                else:
                    sfile[key] = val

            sfile.close()

    def del_item(self, key):
        if self.filepath and os.path.exists(self.filepath) and key:
            sfile = shelve.open(self.filepath)
            type(sfile)

            if key in sfile.keys():
                del sfile[key]

            sfile.close()

    def grab_list(self):
        if self.filepath and os.path.exists(self.filepath):
            mydict = dict()
            sfile = shelve.open(self.filepath)
            type(sfile)

            for k, v in sfile.items():
                mydict[k] = v

            sfile.close()

            return mydict

    def empty_list(self):
        if self.filepath and os.path.exists(self.filepath):
            sfile = shelve.open(self.filepath)
            type(sfile)

            for k in sfile.keys():
                del sfile[k]

            sfile.close()

    def add_list(self, dict_list):
        if self.filepath and os.path.exists(self.filepath) and len(dict_list) > 0 and type(dict_list) == 'dict':
            sfile = shelve.open(self.filepath)
            type(sfile)

            for k, v in dict_list.items():
                sfile[k] = v

            sfile.close()


class LogHandle:
    def __init__(self, scriptpath):
        if scriptpath:
            if not os.path.exists(os.path.join(scriptpath, '01_Event_Logs')):
                os.makedirs(os.path.join(scriptpath, '01_Event_Logs'))

            self.EventLog_Dir = os.path.join(scriptpath, '01_Event_Logs')
        else:
            raise Exception('Settings object was not passed through')

    def write_log(self, message, action='info'):
        filepath = os.path.join(self.EventLog_Dir,
                                "{0}_{1}_Log.txt".format(datetime.datetime.now().__format__("%Y%m%d"), os.path
                                                         .basename(os.path.dirname(os.path.abspath(__file__)))))

        logging.basicConfig(filename=filepath,
                            level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')

        print('{0} - {1} - {2}'.format(datetime.datetime.now(), action.upper(), message))

        if action == 'debug':
            logging.debug(message)
        elif action == 'info':
            logging.info(message)
        elif action == 'warning':
            logging.warning(message)
        elif action == 'error':
            logging.error(message)
        elif action == 'critical':
            logging.critical(message)


class SQLHandle:
    conn_type = None
    conn_str = None
    session = False
    engine = None
    conn = None
    cursor = None

    def __init__(self, settingsobj):
        if settingsobj:
            self.settingsobj = settingsobj
        else:
            raise Exception('Settings object not included in parameter')

    def create_conn_str(self, server=None, database=None, dsn=None):
        if self.conn_type == 'alch':
            p = quote_plus(
                'DRIVER={};PORT={};SERVER={};DATABASE={};Trusted_Connection=yes;'
                    .format('{SQL Server Native Client 11.0}', '1433', server, database))

            self.conn_str = '{}+pyodbc:///?odbc_connect={}'.format('mssql', p)
        elif self.conn_type == 'sql':
            self.conn_str = 'driver={0};server={1};database={2};autocommit=True;Trusted_Connection=yes'\
                .format('{SQL Server}', server, database)
        elif self.conn_type == 'dsn':
            self.conn_str = 'DSN={};DATABASE=default;Trusted_Connection=Yes;'.format(dsn)
        else:
            raise Exception('Invalid conn_type specified')

    def val_settings(self):
        if self.conn_type in ['alch', 'sql']:
            if not self.settingsobj.grab_item('Server') and not self.settingsobj.grab_item('Database'):
                self.settingsobj.add_item('Server', inputmsg='Please input Server to store in settings:')
                self.settingsobj.add_item('Database', inputmsg='Please input Database name to store in settings:')

            self.create_conn_str(server=self.settingsobj.grab_item('Server')
                                 , database=self.settingsobj.grab_item('Database'))

        elif self.conn_type == 'dsn':
            if not self.settingsobj.grab_item('DSN'):
                self.settingsobj.add_item('DSN', inputmsg='Please input DSN name to store in settings:')

            self.create_conn_str(dsn=self.settingsobj.grab_item('DSN'))

    def conn_chk(self):
        exit_loop = False

        while exit_loop:
            self.val_settings()
            myquery = "SELECT 1 from sys.sysprocesses"
            self.connect()

            try:
                if self.conn_type == 'alch':
                    obj = self.engine.execute(mysql.text(myquery))

                    if obj._saved_cursor.arraysize > 0:
                        exit_loop = True
                    else:
                        self.settingsobj.del_item('Server')
                        self.settingsobj.del_item('Database')
                        print('Error! Server & Database combination are incorrect!')

                else:
                    df = sql.read_sql(myquery, self.conn)
                    if len(df) > 0:
                        exit_loop = True
                    else:
                        if self.conn_type == 'sql':
                            self.settingsobj.del_item('Server')
                            self.settingsobj.del_item('Database')
                            print('Error! Server & Database combination are incorrect!')
                        else:
                            self.settingsobj.del_item('DSN')
                            print('Error! DSN is incorrect!')

                self.close()

            except ValueError as a:
                if self.conn_type in ['alch', 'sql']:
                    self.settingsobj.del_item('Server')
                    self.settingsobj.del_item('Database')
                    print('Error! Server & Database combination are incorrect!')
                else:
                    self.settingsobj.del_item('DSN')
                    print('Error! DSN is incorrect!')

                self.close()

    def connect(self, conn_type):
        self.conn_type = conn_type
        self.conn_chk()

        if self.conn_type == 'alch':
            self.engine = mysql.create_engine(self.conn_str)
        else:
            self.conn = pyodbc.connect(self.conn_str)
            self.cursor = self.conn.cursor()
            self.conn.commit()

    def close(self):
        if self.conn_type == 'alch':
            self.engine.dispose()
        else:
            self.cursor.close()
            self.conn.close()

    def createsession(self):
        if self.conn_type == 'alch':
            self.engine = sessionmaker(bind=self.engine)
            self.engine = self.engine()
            self.engine._model_changes = {}
            self.session = True

    def createtable(self, dataframe, sqltable):
        if self.conn_type == 'alch' and not self.session:
            dataframe.to_sql(
                sqltable,
                self.engine,
                if_exists='replace',
            )

    def grabengine(self):
        if self.conn_type == 'alch':
            return self.engine
        else:
            return [self.cursor, self.conn]

    def upload(self, dataframe, sqltable):
        if self.conn_type == 'alch' and not self.session:
            mytbl = sqltable.split(".")

            if len(mytbl) > 1:
                dataframe.to_sql(
                    mytbl[1],
                    self.engine,
                    schema=mytbl[0],
                    if_exists='append',
                    index=True,
                    index_label='linenumber',
                    chunksize=1000
                )
            else:
                dataframe.to_sql(
                    mytbl[0],
                    self.engine,
                    if_exists='replace',
                    index=False,
                    chunksize=1000
                )

    def query(self, query):
        try:
            if self.conn_type == 'alch':
                obj = self.engine.execute(mysql.text(query))

                if obj._saved_cursor.arraysize > 0:
                    data = obj.fetchall()
                    columns = obj._metadata.keys

                    return pd.DataFrame(data, columns=columns)

            else:
                df = sql.read_sql(query, self.conn)
                return df

        except ValueError as a:
            print('\t[-] {} : SQL Query failed.'.format(a))
            pass

    def execute(self, query):
        try:
            if self.conn_type == 'alch':
                self.engine.execute(mysql.text(query))
            else:
                self.cursor.execute(query)

        except ValueError as a:
            print('\t[-] {} : SQL Execute failed.'.format(a))
            pass


class ErrHandle:
    errors = dict()

    def __init__(self, logobj):
        if not logobj:
            raise Exception('Event Log object not included in parameter')

        self.logobj = logobj

    @staticmethod
    def trim_df(df_to_trim, df_to_compare):
        if type(df_to_trim) == 'DataFrame' and type(df_to_compare) == 'DataFrame' and not df_to_trim.empty\
                and not df_to_compare.empty:
            df_to_trim.drop(df_to_compare.index, inplace=True)

    @staticmethod
    def concat_dfs(df_list):
        if type(df_list) == 'list' and len(df_list) > 0:
            dfs = []

            for df in df_list:
                if type(df) == 'DataFrame':
                    dfs.append(df)

            if len(dfs) > 0:
                return pd.concat(dfs, ignore_index=True, sort=False).drop_duplicates().reset_index(drop=True)

    def append_errors(self, err_items, key=None):
        if type(err_items) == 'list' and not err_items:
            self.logobj.write_log('Error(s) found. Appending to virtual list', 'warning')

            if key and key in self.errors.keys:
                self.errors[key] = self.errors[key].append(err_items)
            elif key:
                self.errors[key] = [].append(err_items)
            elif 'default' in self.errors.keys:
                self.errors['default'] = self.errors['default'].append(err_items)
            else:
                self.errors['default'] = [].append(err_items)

    def grab_errors(self, key=None):
        if key and key in self.errors.keys:
            mylist = self.errors[key]
            del self.errors[key]
            return mylist
        elif not key and 'default' in self.errors.keys:
            mylist = self.errors['default']
            del self.errors['default']
            return mylist
        else:
            return None