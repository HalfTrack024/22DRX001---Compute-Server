import dataBaseConnect as dbc
import framingCheck as fc

def printResult(data):
    rstSTR = ""
    for row in results:
        rstSTR = "["
        for item in row:
            rstSTR += " " 
            rstSTR += str(item)
        rstSTR += "]"  
        print(rstSTR)




class JobData:

    def __init__(self):
            self



class Panel:

    plateInnerBottom = 0
    plateInnerTop = 0

    def __init__(self, paneldata):
        self.label = paneldata[0][0]
        self.height = float(paneldata[0][1])
        self.thickness = float(paneldata[0][2])
        self.studheight = float(paneldata[0][3])
        self.walllength = float(paneldata[0][4])

        self.plateInnerBottom = 1.5
        self.plateInnerTop  = 1.5 + self.studheight

    def getPanel(self, panelGUID):
        pass


if __name__ == "__main__":
    credentials = dbc.getCred()
    pgDB = dbc.DB_Connect(credentials)
    pgDB.open()

    #get panel details dimensions
    sql_var= "4a4909bf-f877-4f2f-8692-84d7c6518a2d"
    sql_select_query=f"""SELECT "label", height, thickness, studheight, walllength
                        FROM panel
                        WHERE panelguid='{sql_var}';
                    """
    
    results = pgDB.query(sqlStatement=sql_select_query)
    print(type(results[0][4]))

    #initialize Panel
    itterPanel = Panel(results)

    sql_select_query=f"""SELECT elementguid, "type", description, "size", b1x
                        FROM elements
                        WHERE panelguid = '{sql_var}' AND e1y = 1.5
                        ORDER BY b1x ASC;
                    """

    results = pgDB.query(sqlStatement=sql_select_query)
    
    clear = fc.Clear()

    if clear.studStopFS(): 
        #add for when stud stop is allowed
        pass
    if clear.hammerFS():
        #add for when hammer is allowed
        pass
    if clear.studStopMS():
        #add for when stud stop is allowed
        pass
    if clear.hammerMS():
        #add for when hammer is allowed
        pass


    results = pgDB.query(sqlStatement=sql_select_query)

    printResult(data=results)



    results = pgDB.query(sqlStatement=sql_select_query)
    pgDB.close()
