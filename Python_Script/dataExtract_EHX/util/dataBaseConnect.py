import psycopg2 as psy              #Requires Python >=3.6

def getCred():
    f = open(r'Python_Script\dataExtract_EHX\util\credentials.txt', 'r')
    credits = f.read().splitlines()
    #Get credentials from the user
    return credits

def printResult(data):
    rstSTR = ""
    for row in data:
        rstSTR = "["
        for item in row:
            rstSTR += " " 
            rstSTR += str(item)
        rstSTR += "]"  
        print(rstSTR)

class DB_Connect:
    
    connection = psy.connect

    def __init__ (self, credlist):
        self.user=credlist[0]
        self.password=credlist[1]
        self.host=credlist[2]
        self.port=credlist[3]
        self.database=credlist[4]        

    def open(self):
        #connect to the database
        try:
            self.connection = psy.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                database=self.database
            )
            #print(self.connection.status)
        except(Exception, psy.Error) as Error:
            print("Failed to Connect: {}".format(Error))
        finally:
             print("Connection Open")

    def close(self):
        #Close DB Connection
        print(self.connection.status)
        if self.connection:
            self.connection.close()
            #print(self.connection.status)
            print("SQL connection closed")

    def query(self, sqlStatement):
        cursor = self.connection.cursor()
        cursor.execute(sqlStatement) 
        result = cursor.fetchall()
        cursor.close()
        return result




if __name__ == "__main__":
    credentials = getCred()
    pgDB = DB_Connect(credentials)
    pgDB.open()
    sql_Var = "221415WALLS"
    thickness = 0.75

    sql_e1X_Max = 175.769
    sql_e1X_Min = sql_e1X_Max - thickness

    sql_select_query=f"""SELECT e1x
                        FROM elements
                        WHERE elementguid = '0c326f0c-19e7-41f2-9ac7-8d723ff671c1'
                    """

    results = pgDB.query(sqlStatement=sql_select_query)
    printResult(results)
    print(results[0][0])
    sql_e1X_Max = float(results[0][0])
    sql_e1X_Min = sql_e1X_Max - thickness

    sql_select_query=f"""SELECT elementguid, description, b1x, e1x , e4x 
                        FROM elements
                        WHERE panelguid = '4a4909bf-f877-4f2f-8692-84d7c6518a2d' and (e1x  >= {sql_e1X_Min} and e1x < {sql_e1X_Max}) or (e4x  <= {sql_e1X_Max} and e4x >= {sql_e1X_Min});
                    """

    results = pgDB.query(sqlStatement=sql_select_query)
    pgDB.close()
    printResult(results)

