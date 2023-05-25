import dataBaseConnect as dbc
import runData_Helper as rdh
from Parameters import Parameters
import panelData
import json
from material import Material

class RunData:
    
    fastenTypes : list[str]
    materialTypes : list[str]
    layers : list[float]


    def __init__(self, panel : panelData.Panel):
        self.panel = panel

        ec2TabNames = ["Stud Inverter speeds","Nail Tool MS","Axis LBH","Axis HSP","Computer Settings",
            "Joint Rules","Studfeeder","Axis Width","Axis GUM","Axis GUF","Axis NPM","Positions",
            "Nail Tool FS","Stud stack positions","Axis NPF","Axis WAN","Axis SPR",
            "Program Settings And Parameters","Device Offsets","Program Settings and Parameters", "Application"]
        self.ec2Parm = Parameters(ec2TabNames)
        ec3TabNames = ["Stud Inverter speeds","Nail Tool MS","Axis LBH","Axis HSP","Computer Settings",
            "Joint Rules","Studfeeder","Axis Width","Axis GUM","Axis GUF","Axis NPM","Positions",
            "Nail Tool FS","Stud stack positions","Axis NPF","Axis WAN","Axis SPR",
            "Program Settings And Parameters","Device Offsets","Program Settings and Parameters", "Application"] 
        #self.ec3Parm = Parameters(ec3TabNames)        
        

        self.rdMain() # Main Call to Programs
        
    def rdMain(self): #Main Call for Run Data. 
        # Open Database Connection
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        sql_var1= self.panel.guid
        sql_select_query=f"""
                        SELECT distinct b1y "size", actual_thickness, materialdesc, b1x, b1y, b2y, e1y, e2y
                        FROM cad2fab.system_elements
                        where panelguid = '{sql_var1}' AND "type" = 'Sheet'
                        order by b1x, e1y;
                        """        
        #
        results = pgDB.query(sqlStatement=sql_select_query) 
        pgDB.close()

        # for sheet in results:
        #     self.getMaterials(sheet)
        self.layers = [0,0.437]
        sRunData_EC2 = self.rdEC2_Main()
        
        pgDB.open()
        sql_var1= self.panel.guid
        sql_var2= json.loads(sRunData_EC2)["_stationID"]
        sql_var3= sRunData_EC2

        pgDB.open()
        #send OpData to JobData table
        sql_JobData_query = '''
                            INSERT INTO cad2fab."ec2_3RunData"
                            ("sItemName", "stationID", "rundata")
                            VALUES(%s,%s,%s);
                            '''
        #make a list of tuples for querymany
        jdQueryData = []
        jdQueryData.append([sql_var1, sql_var2, sql_var3])        

        tmp = pgDB.querymany(sql_JobData_query,jdQueryData)
        pgDB.close()

        sRunData_EC3 = self.rdEC3_Main()




    def rdEC2_Main(self) -> str: #Main Call to assign what work will be allowed to complete on EC2
        lvl20 = self.ec2Parm.getParm("Application", "Run Level 20 missions (True/false)")
        lvl30 = self.ec2Parm.getParm("Application", "Run Level 30 missions (True/false)")
        lvl40 = self.ec2Parm.getParm("Application", "Run Level 40 missions (True/false)")
        layers = rdh.Layers_RBC(11)
        if lvl20: #Applying Sheathing
            for layer in self.layers:                
                layers.addLayer(self.getSheets(layer))

        if lvl30: #Fastening
            self.getFastener()
        
        if lvl40: #Milling CutOuts
            self.getRoughOut()
        
        # returns a converted layers object to a json string
        return layers.toJSON()


    def rdEC3_Main(self): #Main Call to assign what work will be allowed to complete on EC3
        lvl20 = self.ec3Parm.getParm("Application", "Run Level 20 missions (True/False)")
        lvl30 = self.ec3Parm.getParm("Application", "Run Level 30 missions (True/False)")
        lvl40 = self.ec3Parm.getParm("Application", "Run Level 40 missions (True/False)")

        if lvl20:
            self.getSheets(0)

        if lvl30:
            self.getFastener()
        
        if lvl40:
            self.getRoughOut()



                        

            
    def getSheets(self, layer) -> rdh.Layer_RBC: #This fucntion will load the sheets of Material to the 
        # Open Database Connection
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        sql_var1= self.panel.guid
        sql_var2 = layer
        sql_select_query=f"""
                        SELECT to_jsonb(panel)
                        from cad2fab.system_elements panel
                        where panelguid = '{sql_var1}' AND "type" = 'Sheet' and b1y = {sql_var2}
                        order by b1x;
                        """    
        results = pgDB.query(sqlStatement=sql_select_query) 
        
        layerData = rdh.Layer_RBC(self.layers.index(layer))

        for sheet in results:
            #change list to object
            sheet = sheet[0]
            print(type(sheet))
            material = Material(sheet)

            # Board Pick
            pick = rdh.missionData_RBC(400)
            pick.info_01 = sheet['e1x'] # e1x
            pick.info_02 = sheet['e1y'] # e1y
            pick.info_03 = sheet['actual_width']
            pick.info_04 = sheet['e2y']
            pick.info_05 = sheet['actual_thickness']
            pick.info_06 = 1 #TBD got to get panel thickness
            pick.info_11 = 0 #TBD determine board type number
            pick.info_12 = getStack(pick.info_11)

            # Board Place
            place = rdh.missionData_RBC(401) #self.fastenTypes
            place.info_01 = sheet['e1x'] # e1x
            place.info_02 = sheet['e1y'] # e1y
            place.info_03 = 0
            place.info_04 = 0
            place.info_05 = 0 #sheet['actual_thickness']
            place.info_06 = 1 #TBD got to get panel thickness
            place.info_11 = 0
            place.info_12 = 0

            # Fastening

            boardData = rdh.BoardData_RBC(boardpick = pick, boardplace = place)

            sql_var1= self.panel.guid
            sql_var2 = layer
            sql_select_query=f"""
                            SELECT to_jsonb(panel)
                            from cad2fab.system_elements panel
                            where panelguid = '{sql_var1}' AND "type" = 'Sheet' and b1y = {sql_var2}
                            order by b1x;
                            """    
            results = pgDB.query(sqlStatement=sql_select_query)           
            layerData.addBoard(boardData)

        return layerData     


    def setboardFastener(self) -> rdh.missionData_RBC:
        pass


    def getFastener(self):
        pass

    def getRoughOut(self):
        pass         

        
def getStack(matType):
    pass




if __name__ == "__main__":
    panel = panelData.Panel("4a4909bf-f877-4f2f-8692-84d7c6518a2d")
    sheeting = RunData(panel)
    sheeting.getSheets(0)

