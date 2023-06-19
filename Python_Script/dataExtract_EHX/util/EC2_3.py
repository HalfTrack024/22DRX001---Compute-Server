import dataBaseConnect as dbc
import runData_Helper as rdh
from Parameters import Parameters
import panelData, machineData
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
        #Prediction Keys ['oEC2_Place',	'oEC3_Place',	'oEC2_Fasten',	'oEC3_Fasten',	'oEC2_Routing',	'oEC3_Routing']
        loadbalance = self.machine.getPrediction()
        layers = rdh.Layers_RBC(11)
        


        #Determine how much material is being placed with EC2
        match loadbalance.get('oEC2_Place'):
            case 100:
                #Condition if only one layer is being applied by EC2           
                layers.addLayer(self.getSheets(self.panel.getLayerPosition(0), 2))
            case 200:
                layers.addLayer(self.getSheets(self.panel.getLayerPosition(0), 2))
                layers.addLayer(self.getSheets(self.panel.getLayerPosition(1)), 2)
            case 123:
                for i in range(self.panel.getLayerCount()):
                     layers.addLayer(self.getSheets(self.panel.getLayerPosition(i)))
            case default:
                print('no material is placed with EC2')


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



                        

            
    def getSheets(self, layer, station) -> rdh.Layer_RBC: #This fucntion will load the sheets of Material to the 
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
        pgDB.close()
        layerData = rdh.Layer_RBC(layer)

        for sheet in results:
            #change list to object
            sheet : dict = sheet[0]
            material = Material(sheet, self.machine.getSystemParms(station))

            # Board Pick
            pick = rdh.missionData_RBC(400)
            pick.info_01 = sheet.get('e1x') # e1x
            pick.info_02 = sheet.get('e1y') # e1y
            pick.info_03 = sheet.get('actual_width')
            pick.info_04 = sheet.get('e2y')
            pick.info_05 = sheet.get('actual_thickness')
            pick.info_06 = 1 #TBD got to get panel thickness
            pick.info_11 = 0 #TBD determine board type number
            pick.info_12 = material.getMaterial()
            

            # Board Place
            place = rdh.missionData_RBC(material.placeNum) #self.fastenTypes
            place.info_01 = sheet.get('e1x') # e1x
            place.info_02 = sheet.get('e1y') # e1y
            place.info_03 = 0
            place.info_04 = 0
            place.info_05 = 0 #sheet['actual_thickness']
            place.info_06 = 1 #TBD got to get panel thickness
            place.info_11 = 0
            place.info_12 = 0

            # Fastening
            self.getboardFastener(pick, material, station)
            # Pick and Place Locations are added to the list
            boardData = rdh.BoardData_RBC(boardpick = pick, boardplace = place)
            #Now we have to add the missions for temp fastening that board

            layerData.addBoard(boardData)

        return layerData     


    def getboardFastener(self, board : rdh.missionData_RBC, iMaterial : Material, station) -> list[rdh.missionData_RBC]:        
        # Open Database Connection
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        sql_var1= self.panel.guid #Panel ID        
        sql_wStart =  board.info_01 #Leading Edge of the Board (Width)        
        sql_wEnd = board.info_01 + board.info_03 #Trailing Edge of the Board (Width)
        #Get parameters to determine min and max window to temp fasten material
        if station == 2: 
            sql_vMin = machine.ec2.parmData.getParm([], 'ZL Core', 'Y Min Vertical') 
            sql_vMax = machine.ec2.parmData.getParm([], 'ZL Core', 'Y Max Vertical')
        elif station == 3: 
            sql_vMin = machine.ec2.parmData.getParm([], 'ZL Core', 'Y Min Vertical')
            sql_vMax = machine.ec2.parmData.getParm([], 'ZL Core', 'Y Max Vertical')    
        
        sql_select_query=f"""
                            select to_jsonb(se) 
                            from cad2fab.system_elements se
                            where 
                                panelguid = '{sql_var1}' 
                                and description not in ('Nog', 'Sheathing') 
                                and e1y < '{sql_vMax}'/25.4 and e2y > '{sql_vMin}'/25.4
                                and e1x >= '{sql_wStart}' and e1x < '{sql_wEnd}'
                            """    
        results = pgDB.query(sqlStatement=sql_select_query) 
        pgDB.close()
        # Process Results
        result : dict
        fastenlst = []
        for result  in results:

            #Vertical vs Horizantal
            if result.get('ey1') == result.get('ey2'):
                fasten = rdh.missionData_RBC
                fasten.missionID = iMaterial.getFastenType()
                if result.get('ey1') < sql_vMin:
                    fasten.info_02 = sql_vMin 
                else:
                    fasten.info_02 = result.get('ey1') + 0.75
                
                if result.get('ey2') > sql_vMax:
                    fasten.info_04 = sql_vMax
                else:
                    fasten.info_04 = result.get('ey2') - 0.75
            elif
            





    def getFastener(self):
        pass

    def getRoughOut(self):
        pass         







if __name__ == "__main__":
    panel = panelData.Panel("4a4909bf-f877-4f2f-8692-84d7c6518a2d")
    machine = machineData.Line()
    sheeting = RunData(panel, machine)


    
    sheeting.getSheets(0)

