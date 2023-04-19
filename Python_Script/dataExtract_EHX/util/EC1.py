from util import dataBaseConnect as dbc
import panelData

class MtrlData:

    def mdMain():
        pass


class JobData():
    
    jobdata = []
    linedata = {
        "xPos" : 0,
        "opText" : " ",
        "opCode_FS": 0,
        "zPos_FS" : 0,
        "yPos_FS" : 0,
        "ssUpPosition_FS" : 0,
        "opCode_MS": 0,
        "zPos_MS" : 0,
        "yPos_MS" : 0,
        "ssUpPosition_MS" : 0,
        "imgName" : " ",
        "objID" : 0
    }

    def __init__(self, panelguid, panelData(panel)):
        self.pdData = panelData.Panel(panel)
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        #
        sql_var= " "
        sql_select_query=f"""
                        SELECT thickness, studheight, walllength, category
                        FROM panel
                        WHERE panelguid = '{panelguid}';
                        """
        
        results = pgDB.query(sqlStatement=sql_select_query)
        dbc.printResult(results)
        #assign results of query to variables
        self.panelGuid = panelguid
        self.panelThickness = float(results[0][1])
        self.studHeight = float(results[1][1])
        self.panelLength = float(results[2][1])
        self.catagory = float(results[3][1])

        #self.plateInnerBottom = 1.5
        #self.plateInnerTop  = 1.5 + self.studHeight        

        #Always close the connection after all queries are complete
        pgDB.close()

    def jdMain(panelguid): # Job Data Main
        
        pass

    def jdBuild(panelguid): # Job Data Build
        
        pass



if __name__ == "__main__":
    Panel = JobData("4a4909bf-f877-4f2f-8692-84d7c6518a2d")
