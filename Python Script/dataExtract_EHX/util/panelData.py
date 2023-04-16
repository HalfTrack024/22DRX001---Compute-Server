import dataBaseConnect as dbc

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
        self.height = paneldata[0][1]
        self.thickness = paneldata[0][2]
        self.studheight = paneldata[0][3]
        self.walllength = paneldata[0][4]

        self.plateInnerBottom = 1.5
        #self.plateInnerTop  = 1.5 + self.studheight

    def getPanel(self, panelGUID):
        pass

if __name__ == "__main__":
    credentials = dbc.getCred()
    pgDB = dbc.DB_Connect(credentials)
    pgDB.open()

    #get panel overall dimensions
    sql_select_query="""SELECT "label", height, thickness, studheight, walllength
                        FROM panel
                        WHERE panelguid='933d1e73-cb35-4f08-986c-ed7a43377715';
                    """
    results = pgDB.query(sqlStatement=sql_select_query)
    itterPanel = Panel(results)

    sql_select_query="""SELECT elementguid, "type", description, "size", b1x
                    FROM elements
                    WHERE panelguid = '4a4909bf-f877-4f2f-8692-84d7c6518a2d' AND e1y = 1.5
                    ORDER BY b1x ASC;
                """

    results = pgDB.query(sqlStatement=sql_select_query)
    
    printResult(data=results)


    results = pgDB.query(sqlStatement=sql_select_query)
    pgDB.close()
