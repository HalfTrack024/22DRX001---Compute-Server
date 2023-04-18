import psycopg2 as psy              #Requires Python >=3.6

def getCred():
    print('Using saved credentials')
    save = open('Python Script\dataExtract_EHX\credentials.txt','r')
    credits = save.read().splitlines()
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
            print(self.connection.status)
        except(Exception, psy.Error) as Error:
            print("Failed to Connect: {}".format(Error))
        finally:
             print("Connection Open")

    def close(self):
        #Close DB Connection
        print(self.connection.status)
        if self.connection:
            self.connection.close()
            print(self.connection.status)
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
    sql_select_query=f"""SELECT jobid, panelguid
                        FROM bundle, panel
                        WHERE jobid = '{sql_Var}'
                    """

    results = pgDB.query(sqlStatement=sql_select_query)
    pgDB.close()
    printResult(results)

