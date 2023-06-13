import dataBaseConnect as dbc
import runData_Helper as rdh
from Parameters import Parameters
import panelData
import machineData
import json
from material import Material

class RunData:
    
    fastenTypes : list[str]
    materialTypes : list[str]
    layers : list[float]

    def __init__(self, panel : panelData.Panel, machine : machineData.Line):
        self.panel = panel
        self.machine = machine
        # This is used to evaluate if the layer count stored matches the panel. 
        # If Not re-run load balancing prediction 
        if self.machine.predictlayercount != self.panel.getLayerCount():
            self.machine.changePrediction(self.panel.getLayerCount())
        
        

        self.rdMain() # Main Call to Programs
        
    def rdMain(self): #Main Call for Run Data. 
        # Open Database Connection
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)

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
        loadbalance = self.machine.getPrediction()
        layers = rdh.Layers_RBC(11)
        if self.runlvl.get('ec2_20'): #Applying Sheathing
            for layer in self.layers:                
                layers.addLayer(self.getSheets(layer))

        if self.runlvl.get('ec2_30'): #Fastening
            self.getFastener()
        
        if self.runlvl.get('ec2_40'): #Milling CutOuts
            self.getRoughOut()
        
        # returns a converted layers object to a json string
        return layers.toJSON()


    def rdEC3_Main(self): #Main Call to assign what work will be allowed to complete on EC3

        if self.runlvl['ec3_20']:
            self.getSheets(0)

        if self.runlvl['ec3_30']:
            self.getFastener()
        
        if self.runlvl['ec3_40']:
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
            sheet : dict = sheet[0]
            print(type(sheet))
            material = Material(sheet, self.ec2Parm)

            # Board Pick
            pick = rdh.missionData_RBC(400)
            pick.info_01 = sheet.get('e1x') # e1x
            pick.info_02 = sheet.get('e1y') # e1y
            pick.info_03 = sheet['actual_width']
            pick.info_04 = sheet['e2y']
            pick.info_05 = sheet['actual_thickness']
            pick.info_06 = 1 #TBD got to get panel thickness
            pick.info_11 = 0 #TBD determine board type number
            pick.info_12 = material.getMaterial()
            

            # Board Place
            place = rdh.missionData_RBC(material.placeNum) #self.fastenTypes
            place.info_01 = sheet['e1x'] # e1x
            place.info_02 = sheet['e1y'] # e1y
            place.info_03 = 0
            place.info_04 = 0
            place.info_05 = 0 #sheet['actual_thickness']
            place.info_06 = 1 #TBD got to get panel thickness
            place.info_11 = 0
            place.info_12 = 0

            # Fastening
            # Pick and Place Locations are added to the list
            boardData = rdh.BoardData_RBC(boardpick = pick, boardplace = place)
            #Now we have to add the missions for temp fastening that board

            layerData.addBoard(boardData)

        return layerData     


    def getboardFastener(self, element) -> list[rdh.missionData_RBC]:        
        pass


    def getFastener(self):
        pass

    def getRoughOut(self):
        pass         







if __name__ == "__main__":
    panel = panelData.Panel("4a4909bf-f877-4f2f-8692-84d7c6518a2d")
    sheeting = RunData(panel)


    
    sheeting.getSheets(0)

