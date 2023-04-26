import psycopg2 as psy              #Requires Python >=3.6
import psycopg2.extras as psyE

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
             #print("Connection Open")
             pass

    def close(self):
        #Close DB Connection
        #print(self.connection.status)
        if self.connection:
            self.connection.close()
            #print(self.connection.status)
            #print("SQL connection closed")

    def query(self, sqlStatement):
        cursor = self.connection.cursor()
        #print(sqlStatement)
        cursor.execute(sqlStatement) 
        result = cursor.fetchall()
        cursor.close()
        return result
    
    def querymany(self,sqlStatement,records):
        #records should be a list of tuples
        #sql statement should be a string of an sql statement with the values to be passed replaced by %s
        #records will be placed where the %s are
        cursor = self.connection.cursor()
        cursor.executemany(sqlStatement,records)
        self.connection.commit()
        tmp = cursor.rowcount
        cursor.close()
        #returns the amount of rows modified
        return(tmp)
    
    def queryRetJSON(self, sqlStatement):
        cursor = self.connection.cursor(cursor_factory=psyE.DictCursor)
        cursor.execute(sqlStatement) 
        result = cursor.fetchall()
        cursor.close()
        return result
        # cursor = self.connection.cursor(cursor_factory=psy.extras.DictCursor)
        # cursor.executemany(sqlStatement)
        # self.connection.commit()
        # tmp = cursor.rowcount
        # cursor.close()



if __name__ == "__main__":
    credentials = getCred()
    pgDB = DB_Connect(credentials)
    pgDB.open()

    sql_select_query=f"""
select 
	json_object_agg(description, jsonOBJ.parms) 
	from (
		select	
		description,
		json_build_object('value', value, 'max', "max", 'min', "min", 'datatype', "DataType")	as parms
		from ec1_parameters) jsonOBJ;
                        """

    results = pgDB.query(sqlStatement=sql_select_query)
    for  row in results:
        print(type(row))

    pgDB.close()
    #printResult(results)

