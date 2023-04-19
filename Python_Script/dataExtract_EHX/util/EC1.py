import dataBaseConnect as dbc
import panelData

class MtrlData:

    mrtldata = []

    def __init__(self, panelData : panelData.Panel):
        #Assigns Panel Instance to Mtrl 
        self.panel = panelData
        
        self.mdMain()

    # Main Call for determining Material List
    def mdMain(self):
        #Open Connection to the database
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        sql_var = self.panel.guid
        sql_select_query=f"""SELECT elementguid, "type", description, "size", actual_thickness, actual_width
                    FROM elements
                    WHERE panelguid = '{sql_var}' AND description = 'Stud' AND type = 'Board'
                    ORDER BY b1x ASC;
                """       

        results = pgDB.query(sqlStatement=sql_select_query)
        pgDB.close()
        for element in results:            
            self.mrtldata.append(self.mdBuild(element))

    def mdBuild(self, element):
        
        uiItemLength = self.panel.studHeight
        uiItemHeight = float(element[4])
        uiItemThickness = float(element[5])
        sMtrlCode = self.getMatCode(element[3])
        uiOpCode = 0
        sPrinterWrite = 0	
        sType = 0
        uiItemID = element[0]	
        sCADPath = 0
        sProjectName = 0	
        sItemName = self.panel.guid

        line = [uiItemLength, uiItemHeight, uiItemThickness, sMtrlCode, uiOpCode, sPrinterWrite, sType, uiItemID, sCADPath, sProjectName, sItemName]
        return line
    
    def getMatCode(studType):
        #NEED TO DETERMINE HOW TO GET STUD MATERIAL CODE
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

    def __init__(self, panel : panelData.Panel):
        self.pdData = panel

        #self.plateInnerBottom = 1.5
        #self.plateInnerTop  = 1.5 + self.studHeight        

    def jdMain(panelguid): # Job Data Main
        
        pass

    def jdBuild(panelguid): # Job Data Build
        
        pass



if __name__ == "__main__":
    panel = panelData.Panel("4a4909bf-f877-4f2f-8692-84d7c6518a2d")
    matData = MtrlData(panel)
    jobdata = JobData(panel)

