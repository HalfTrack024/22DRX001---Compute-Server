import logging
import sys

import psycopg2 as psy  # Requires Python >=3.6
from psycopg2.extras import DictCursor

import util.General_Help as gHelp


def get_cred():
    f = open(r'C:\Users\Andrew Murray\PycharmProjects\pythonProject1\util\credentials.txt', 'r')
    credential = f.read().splitlines()
    # Get credentials from the user
    return credential


def print_result(data):
    for row in data:
        rstSTR = "["
        for item in row:
            rstSTR += " "
            rstSTR += str(item)
        rstSTR += "]"
        print(rstSTR)


class DB_Connect:
    connection = psy.connect

    def __init__(self):
        app_settings = gHelp.get_app_config()
        cred_list = app_settings.get('DB_credentials')
        self.user = cred_list.get('user')
        self.password = cred_list.get('password')
        self.host = cred_list.get('host')
        self.port = cred_list.get('port')
        self.database = cred_list.get('database')

    def open(self):
        # connect to the database
        try:
            self.connection = psy.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                database=self.database,
                connect_timeout=2
            )
            # print(self.connection.status)
        except (Exception, psy.Error) as Error:
            print("Failed to Connect: {}".format(Error))

            logging.error('Open Connection Failed')
            logging.error("Failed to Connect: {}".format(Error))
            sys.exit("Connection Not Found")
        finally:
            # print("Connection Open")
            pass

    def close(self):
        # Close DB Connection
        # print(self.connection.status)
        if self.connection:
            self.connection.close()
            # print(self.connection.status)
            # print("SQL connection closed")

    def query(self, sql_statement):
        try:
            cursor = self.connection.cursor()
            # print(sqlStatement)
            cursor.execute(sql_statement)
            result = cursor.fetchall()
            cursor.close()
            return result
        except:
            print('Query Did Not Complete')
            logging.info(sql_statement)
            self.connection.close()
        finally:
            pass

    def query_many(self, sql_statement, records):
        # records should be a list of tuples
        # sql statement should be a string of an sql statement with the values to be passed replaced by %s
        # records will be placed where the %s are
        cursor = self.connection.cursor()
        cursor.executemany(sql_statement, records)
        self.connection.commit()
        tmp = cursor.rowcount
        cursor.close()
        # returns the amount of rows modified
        return tmp

    def query_ret_json(self, sql_statement):
        cursor = self.connection.cursor(cursor_factory=DictCursor)
        cursor.execute(sql_statement)
        result = cursor.fetchall()
        cursor.close()
        return result
        # cursor = self.connection.cursor(cursor_factory=psy.extras.DictCursor)
        # cursor.executemany(sqlStatement)
        # self.connection.commit()
        # tmp = cursor.rowcount
        # cursor.close()

# if __name__ == "__main__":
#     credentials = getCred()
#     pgDB = DB_Connect(credentials)
#     pgDB.open()

#     sql_select_query=f"""
# select 
# 	json_object_agg(description, jsonOBJ.parms) 
# 	from (
# 		select	
# 		description,
# 		json_build_object('value', value, 'max', "max", 'min', "min", 'datatype', "DataType")	as parms
# 		from parameters) jsonOBJ;
#                         """

#     results = pgDB.query(sqlStatement=sql_select_query)
#     for  row in results:
#         print(type(row))

#     pgDB.close()
#     #printResult(results)
