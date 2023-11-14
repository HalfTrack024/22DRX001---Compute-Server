import util.dataBaseConnect as dbc
import traceback
from Validator import rbcCheck as rBC, framerCheck


def pass_print(name, value):
    print("Function: " + name + " State: " + str(value))


def check_rbc(query_statement):
    connect = dbc.DB_Connect()
    connect.open()
    rbc_data = connect.query(query_statement)
    connect.close()
    rbc_data = rbc_data[0][0]
    pass_print(rBC.check_json_schema.__name__, rBC.check_json_schema(rbc_data))
    for layer in rbc_data:
        layer_data = rbc_data[layer]
        pass_print(rBC.check_boards.__name__, rBC.check_boards(layer_data.get("Board")))
        for board in layer_data["Board"]:
            pass_print(rBC.check_board_pick.__name__, rBC.check_board_pick(board["BoardPick"]))


def check_framer():
    pass


def check_stud_feeder():
    pass

#MAIN LOGIC
rc = True
framer = False
picker = False

if rc:
    sql_var = '73791728-8e7a-4001-9c06-f4eaf7da44aa'
    sqlstatement = f"""SELECT jobdata
                    FROM cad2fab.rbc_jobdata
                    WHERE sitemname='{sql_var}' AND stationid=22;"""
    check_rbc(sqlstatement)

if framer:
    sql_var = '73791728-8e7a-4001-9c06-f4eaf7da44aa'
    sqlstatement = f"""SELECT *
                    FROM cad2fab.rbc_jobdata
                    WHERE sitemname='{sql_var}' AND stationid=22;"""
    check_framer(sqlstatement)