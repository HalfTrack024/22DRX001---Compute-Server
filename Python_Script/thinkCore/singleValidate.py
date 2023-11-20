import util.dataBaseConnect as dbc
import logging
import traceback
from Validator import rbcCheck as rBC, framerCheck as fCK


def pass_print(name, value):
    print("Function: " + name + " State: " + str(value))


def check_rbc(query_statement):
    rbc_data = connect.query(query_statement)
    rbc_data = rbc_data[0][0]
    pass_print(rBC.check_json_schema.__name__, rBC.check_json_schema(rbc_data))
    for layer in rbc_data:
        layer_data = rbc_data[layer]
        pass_print(rBC.check_boards.__name__, rBC.check_boards(layer_data.get("Board")))
        for board in layer_data["Board"]:
            pass_print(rBC.check_board_pick.__name__, rBC.check_board_pick(board["BoardPick"]))


def check_framer(query_statement):
    job_data = connect.query(query_statement)
    global count
    results, count = fCK.check_op_data((job_data))
    pass_print(fCK.check_op_data.__name__, results)


def check_stud_feeder(query_statement):
    mtrl_data = connect.query(query_statement)
    pass_print(fCK.check_stud_feeder.__name__, fCK.check_stud_feeder(mtrl_data[0], count))



# MAIN LOGIC
logging.basicConfig(encoding='utf-8', format='%(levelname)s : %(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
rc = False
framer = True
picker = True
connect = dbc.DB_Connect()
connect.open()
sql_var = '73791728-8e7a-4001-9c06-f4eaf7da44aa'
if rc:
    sqlstatement = f"""SELECT jobdata
                    FROM cad2fab.rbc_jobdata
                    WHERE sitemname='{sql_var}' AND stationid=22;"""
    check_rbc(sqlstatement)
count = 0
if framer:
    sqlstatement = f"""SELECT *
                    FROM cad2fab.fm3_jobdata
                    WHERE panelguid='{sql_var}';"""
    check_framer(sqlstatement)
if picker:
    sqlstatement = f"""SELECT *
                    FROM cad2fab.sf3_jobdata
                    WHERE sitemname='{sql_var}';"""
    check_stud_feeder(sqlstatement)
connect.close()
