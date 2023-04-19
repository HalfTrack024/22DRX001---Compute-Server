from util import dataBaseConnect as dbc

if __name__ == "__main__":
    credentials = dbc.getCred()
    pgDB = dbc.DB_Connect(credentials)
    pgDB.open()
    sql_select_query="select * from bundle"
    results = pgDB.query(sqlStatement=sql_select_query)
    pgDB.close()
    rstSTR = ""
    for row in results:
        rstSTR = "["
        for item in row:
            rstSTR += " " 
            rstSTR += str(item)
        rstSTR += "]"  
        print(rstSTR)