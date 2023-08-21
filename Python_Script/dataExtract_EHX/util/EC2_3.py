import logging
#Project Dependencies
from util.panelData import Panel
from util.machineData import Line
import util.dataBaseConnect as dbc
import util.runData_Helper as rdh
from util.material import Material


class RunData:
    
    fastenTypes = {
        'OSB' : 1,
        'PLYWOOD' : 2,
        'GLASROC' : 3,
        'ZIP R3' : 4,
        'ZIP R6' : 5,
        'ZIP R9' : 6,
    }
    materialTypes : list[str]
    layers : list[float]

    def __init__(self, panel : Panel, machine : Line):
        self.panel = panel
        self.machine = machine
        # This is used to evaluate if the layer count stored matches the panel. 
        # If Not re-run load balancing prediction 
        if self.machine.predictlayercount != self.panel.getLayerCount():
            self.machine.changePrediction(self.panel.getLayerCount())        
        
        
    def rdMain(self): #Main Call for Run Data. 

        #raise NotImplementedError("Not implemented")
        # Open Database Connection
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)

        self.layers = [0,0.437]

        sRunData_EC2 = self.rdEC2_Main()
        
        #Insert EC2 Run Data to DataBase
        sql_var1= self.panel.guid
        sql_var2= 12
        sql_var3= sRunData_EC2

        pgDB.open()
        #send OpData to JobData table
        sql_JobData_query = '''
                            INSERT INTO cad2fab.rbc_jobdata
                            (sItemName, stationID, jobdata)
                            VALUES(%s,%s,%s)
                            ON CONFLICT (sitemname, stationID)
                            DO UPDATE SET jobdata = EXCLUDED.jobdata;
                            '''
        #make a list of tuples for querymany
        jdQueryData = []
        jdQueryData.append([sql_var1, sql_var2, sql_var3])        
        tmp = pgDB.querymany(sql_JobData_query,jdQueryData)
        #Close Connection
        pgDB.close()

        sRunData_EC3 = self.rdEC3_Main()

        #Insert EC3 Run Data to DataBase
        sql_var1= self.panel.guid
        sql_var2= 22
        sql_var3= sRunData_EC3
        
        pgDB.open()
        #send OpData to JobData table
        sql_JobData_query = '''
                            INSERT INTO cad2fab.rbc_jobdata
                            (sItemName, stationID, jobdata)
                            VALUES(%s,%s,%s)
                            ON CONFLICT (sitemname, stationID)
                            DO UPDATE SET jobdata = EXCLUDED.jobdata;
                            '''
        #make a list of tuples for querymany
        jdQueryData = []
        jdQueryData.append([sql_var1, sql_var2, sql_var3])        
        tmp = pgDB.querymany(sql_JobData_query,jdQueryData)
        #Close Connection
        pgDB.close()


    def rdEC2_Main(self) -> str: #Main Call to assign what work will be allowed to complete on EC2
        #Prediction Keys ['oEC2_Place',	'oEC3_Place',	'oEC2_Fasten',	'oEC3_Fasten',	'oEC2_Routing',	'oEC3_Routing']
        loadbalance = self.machine.getPrediction()
        layers = rdh.Layers_RBC(11)     
        #Determine how much material is being placed with EC2
        missionPlace = [None, None, None, None, None]  
        match loadbalance.get('oEC2_Place'):
            case 100:
                #Condition if only one layer is being applied by EC2  
                missionPlace[0] = self.getSheets(self.panel.getLayerPosition(0), 2)
                missionPlace[0] = True
            case 200:
                #Layer 1 
                missionPlace[0] = self.getSheets(self.panel.getLayerPosition(0), 2)
                missionPlace[0] = True
                #Layer 2
                missionPlace[1] = self.getSheets(self.panel.getLayerPosition(1), 2)
                missionPlace[1] = True
            case 123:
                for i in range(self.panel.getLayerCount()):
                    #missionPlace[i] = self.getSheets(self.panel.getLayerPosition(i), 2)
                    missionPlace[i] = True
                   
                   
            case default:
                logging.info('no material is placed with EC2')


        print('missionplace: '+str(missionPlace))
        print('panel, get layer pos: '+ str(self.panel.getLayerPosition(0)))


        #Determine if EC2 is fastening material that was loaded 
        missionFasten = [None, None, None, None, None] 
        match loadbalance.get('oEC2_Fasten'):
            case 100:
                missionFasten[0] = self.getFastener(self.panel.getLayerPosition(0), 2)
            case 200:
                missionFasten[0] = self.getFastener(self.panel.getLayerPosition(0), 2)
                missionFasten[1] = self.getFastener(self.panel.getLayerPosition(1), 2)              
            case 123:
                for i in range(self.panel.getLayerCount()):
                    missionFasten[i] = self.getFastener(self.panel.getLayerPosition(i), 2)
                   
            case default:
                logging.info('no material is fastened with EC2')

        #Determine if EC2 is Routing any material
        missionRoute = [None, None, None, None, None] 
        missionRouting = []
        match loadbalance.get('oEC2_Routing'):
           case 100:
               missionRouting.extend(self.getRoughOutCut(self.panel.getLayerPosition(0), 2))
               #missionRouting.extend(self.getEndCut(self.panel.getLayerPosition(0), 2))
               missionRoute[0] = missionRouting
           case 200:
               missionRouting.extend(self.getRoughOutCut(self.panel.getLayerPosition(1), 2))
               #missionRouting.extend(self.getEndCut(self.panel.getLayerPosition(1), 2))
               missionRoute[1] = missionRouting
           case 123:
               for i in range(self.panel.getLayerCount()):
                   missionRoute[i] = self.getRoughOutCut(self.panel.getLayerPosition(i), 2)
               #missionRouting.extend(self.getEndCut(self.panel.getLayerPosition(1), 2))
               missionRoute[1] = missionRouting
           case default:
               logging.info('no material is Routed with EC2')

        #Combine Place, Fasten, and Route Data to Layer 
        
        for i in range(self.panel.getLayerCount()):
            used = False
            layer = rdh.Layer_RBC(self.panel.getLayerPosition(i))
            if missionPlace[i] != None: 
                layer = self.getSheets(self.panel.getLayerPosition(i), 2) #Determine if any boards have been placed for that layer
                used = True
            if missionFasten[i] != None: 
                layer.addMission(missionFasten[i])  #Determine if any fasteners have been used for that layer
                used = True
            if missionRoute[i] != None: 
                layer.addMission(missionRoute[i])   #Determine if any routing have been used for that layer    
                used = True
            if used:
                layers.addLayer(layer)
                #layers._layers.append(layer)
        
        # Returns a converted layers object to a json string
        #sample = layers.toJSON()
        return layers.toJSON()
 

    def rdEC3_Main(self): #Main Call to assign what work will be allowed to complete on EC3
        #Prediction Keys ['oEC2_Place',	'oEC3_Place',	'oEC2_Fasten',	'oEC3_Fasten',	'oEC2_Routing',	'oEC3_Routing']
        loadbalance = self.machine.getPrediction()
        layers_ec3 = rdh.Layers_RBC(21)        

        #Determine how much material is being placed with EC2
        missionPlace = [None, None, None, None, None]  
        match loadbalance.get('oEC3_Place'):
            case 100:
                #Condition if only one layer is being applied by EC2  
                missionPlace[0] = self.getSheets(self.panel.getLayerPosition(0), 3)
                missionPlace[0] = True
            case 200:
                #Layer 1 
                missionPlace[1] = self.getSheets(self.panel.getLayerPosition(1), 3)
                missionPlace[1] = True
                #Layer 2
                #missionPlace[1] = self.getSheets(self.panel.getLayerPosition(1), 3)
                missionPlace[1] = True
            case 123:
                for i in range(self.panel.getLayerCount()):
                    missionPlace[i] = self.getSheets(self.panel.getLayerPosition(i), 3)
                    missionPlace[i] = True
                   
            case default:
                logging.info('no material is placed with EC3')


        #Determine if EC3 is fastening material that was loaded 
        missionFasten = [None, None, None, None, None] 
        match loadbalance.get('oEC3_Fasten'):
            case 100:
                missionFasten[0] = self.getFastener(self.panel.getLayerPosition(0), 3)
            case 200:
                #missionFasten[0] = self.getFastener(self.panel.getLayerPosition(0), 3)
                missionFasten[1] = self.getFastener(self.panel.getLayerPosition(1), 3)              
            case 123:
                for i in range(self.panel.getLayerCount()):
                    missionPlace[i] = self.getFastener(self.panel.getLayerPosition(i), 3)
            case default:
                logging.info('no material is fastened with EC3')

        
        #Determine if EC3 is Routing any material
        missionRoute = [None, None, None, None, None] 
        missionRouting = []
        match loadbalance.get('oEC3_Routing'):
            case 100:
               missionRouting.extend(self.getRoughOutCut(self.panel.getLayerPosition(0), 2))
               #missionRouting.extend(self.getEndCut(self.panel.getLayerPosition(0), 2))
               missionRoute[0] = missionRouting
            case 200:
               missionRouting.extend(self.getRoughOutCut(self.panel.getLayerPosition(1), 2))
               #missionRouting.extend(self.getEndCut(self.panel.getLayerPosition(1), 2))
               missionRoute[1] = missionRouting
            case 123:
               missionRouting.extend(self.getRoughOutCut(self.panel.getLayerPosition(1), 2))
               #missionRouting.extend(self.getEndCut(self.panel.getLayerPosition(1), 2))
               missionRoute[1] = missionRouting
            case default:
               logging.info('no material is Routed with EC3')
     
        #Combine Place, Fasten, and Route Data to Layer         
        for i in range(self.panel.getLayerCount()):
            used = False
            layer = rdh.Layer_RBC(self.panel.getLayerPosition(i))
            if missionPlace[i] != None: 
                layer = self.getSheets(self.panel.getLayerPosition(i), 3) #Determine if any boards have been placed for that layer
                used = True
            if missionFasten[i] != None: 
                layer.addMission(missionFasten[i])  #Determine if any fasteners have been used for that layer
                used = True
            if missionRoute[i] != None: 
                layer.addMission(missionRoute[i])   #Determine if any routing have been used for that layer    
                used = True
            if used:
                layers_ec3.addLayer(layer)

        # Returns a converted layers object to a json string
        sample = layers_ec3.toJSON()
        return layers_ec3.toJSON()

    # Get Sheet Information       
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
                        where panelguid = '{sql_var1}' 
                        and "type" = 'Sheet' 
                        and b1y = '{sql_var2}'
                        and "actual_width" > 30
                        order by b1x 
                        """    
        #sql_select_query=f"""
        #                SELECT to_jsonb(panel)
        #                from cad2fab.system_elements panel
        #                where panelguid = '{sql_var1}' AND "type" = 'Sheet' and b1y = {sql_var2}
        #                order by b1x;
        #                """    
        results = pgDB.query(sqlStatement=sql_select_query) 
        pgDB.close()
        layerData = rdh.Layer_RBC(layer)
        
        logging.info("results: "+str(results))
        self.storeCWSFound = 0
        for sheet in results:
            #change list to object
            sheet : dict = sheet[0]
            material = Material(sheet, self.machine.getSystemParms(station))

            #f.writelines('Sheets: '+str(sheet)+ '   Material: '+str(material))

            # Board Pick
            pick = rdh.missionData_RBC(400)
            pick.Info_01 = round(sheet.get('e1x')*25.4, 2) # e1x
            pick.Info_02 = round(sheet.get('e1y')*25.4, 2) # e1y
            pick.Info_03 = round(sheet.get('actual_width')*25.4, 2)
            if sheet.get('actual_width') < 48 and sheet.get('actual_width') > 30: 
                pick.Info_03 = round(48 * 25.4, 2)
            else:
                pick.Info_03 = round(sheet.get('actual_width')*25.4, 2)
            if "96" in sheet.get('size'):
                pick.Info_04 = 2438.4
            
            elif "108" in sheet.get('size'):
                pick.Info_04 = 2743.2
            
            elif "120" in sheet.get('size'):
                pick.Info_04 = 3048

            else:
                 pick.Info_04 = 2438.4

            pick.Info_05 = round(sheet.get('actual_thickness')*25.4, 2)
            pick.Info_06 = round(self.panel.panelThickness*25.4 + pick.Info_05, 2) 
            pick.Info_11 = material.getMaterialCode()
            pick.Info_12 = material.getMaterial()
            

            # Board Place
            place = rdh.missionData_RBC(material.getPlaceType()) #self.fastenTypes
            # place = rdh.missionData_RBC(material.placeNum) #self.fastenTypes
            place.Info_01 = round(sheet.get('e1x')*25.4, 2) # e1x
            place.Info_02 = round(sheet.get('e1y')*25.4, 2) # e1y
            place.Info_03 = 0
            place.Info_04 = 0
            place.Info_05 = 29
            place.Info_06 = round((sheet.get('e1x') + 0.75)*25.4, 2) 
            if place.missionID == 401:
                place.Info_11 = 1
            else:
                place.Info_11 = 0
            place.Info_12 = 0

            # Fastening
            fasteners = self.getboardFastener(pick, layer, material, station)
            # Pick and Place Locations are added to the list
            boardData = rdh.BoardData_RBC(boardpick = pick, boardplace = place, boardfasten = fasteners )
            #Now we have to add the missions for temp fastening that board

            layerData.addBoard(boardData)

        #this information will be used when building fastener requirements for layer
        layIndex = self.panel.getLayerIndex(layer)
        fast = material.fastenNum
        self.panel.updateLayerFastener(layIndex, fast)

        return layerData     

    
    def getboardFastener(self, board : rdh.missionData_RBC, activeLayer, iMaterial : Material, station) -> list[rdh.missionData_RBC]:       
        studSpace = 406
        # Open Database Connection
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        sql_var1= self.panel.guid #Panel ID        
        sql_wStart =  round(board.Info_01 /25.4,2)  #Leading Edge of the Board (Width)        
        sql_wEnd = round((board.Info_01 + board.Info_03)/25.4, 2) #Trailing Edge of the Board (Width)
        #Get parameters to determine min and max window to temp fasten material
        if station == 2: 
            sql_vMin = 0 #machine.ec3.parmData.getParm('ZL Core', 'Y Min Vertical') /25.4
            sql_vMax = self.machine.ec2.parmData.getParm('ZL Core', 'Y Middle Vertical') / 25.4
        elif station == 3: 
            sql_vMin = 0 #machine.ec3.parmData.getParm([], 'ZL Core', 'Y Min Vertical') / 25.4
            sql_vMax = self.machine.ec3.parmData.getParm('ZL Core', 'Y Middle Vertical') / 25.4

        sql_select_query=f"""
                            select to_jsonb(se) 
                            from cad2fab.system_elements se 
                            where panelguid = '{sql_var1}' 
                            and description not in ('Nog', 'Sheathing','VeryTopPlate','Rough cutout') 
                            and e1y < '{sql_vMax}' 
                            and e2y > '{sql_vMin}' 
                            and e1x < '{sql_wEnd}' 
                            and e4x > '{sql_wStart}' 
                            and b2y = 0 
                            order by b3x  
                            """    
        results = pgDB.query(sqlStatement=sql_select_query) 

        #Determine Start End Shift
        shiftSTART = [0.75, 1, 1.25]
        shiftEND = [0.75, 1.25, 1.25]      
        offsetStart = shiftSTART[self.panel.getLayerIndex(activeLayer)]
        offsetEnd = shiftEND[self.panel.getLayerIndex(activeLayer)]

        # Process Results
        fastenlst : list [rdh.missionData_RBC]= []
        for result  in results:
            result : dict = result[0]
            fasten = rdh.missionData_RBC(iMaterial.getFastenType())
            #fasten.missionID = iMaterial.getFastenType()
            #Vertical vs Horizantal Vertial dimension is less than 6inch
            #Vertical
            if  result.get('e2y') - result.get('e1y') > 3:
                if sql_wEnd > result.get('e4x') and sql_wStart <= result.get('e1x'):
                    fasten.Info_01 = round((result.get('e1x') + 0.75) * 25.4,2) #X Start Position
                    fasten.Info_03 = round((result.get('e1x') + 0.75) * 25.4, 2) #X End Position    
                elif sql_wEnd < result.get('e4x'): #Condition when stud is overhanging the board on the positive side
                    fasten.Info_01 = round((result.get('e1x') + 0.375) * 25.4,2) #X Start Position
                    fasten.Info_03 = round((result.get('e1x') + 0.375) * 25.4, 2) #X End Position
                elif sql_wStart > result.get('e1x'): #Condition when stud is overhanging the board on the positive side
                    fasten.Info_01 = round((result.get('e4x') - 0.375) * 25.4,2) #X Start Position
                    fasten.Info_03 = round((result.get('e4x') - 0.375) * 25.4, 2) #X End Position    
                else:
                    logging.warning('Did not add fastening for member' + self.panel.guid + '__'  + result.get('elementguid'))
                    continue               
                if result.get('e1y') < sql_vMin:
                    fasten.Info_02 = round(sql_vMin * 25.4, 2) #Y Start Position
                else:
                    fasten.Info_02 = round((result.get('e1y') + offsetStart)*25.4, 2) #Y Start Position
                if result.get('e2y') > sql_vMax:
                    fasten.Info_04 = round((sql_vMax - offsetEnd)*25.4, 2) #Y End Position
                else:
                    fasten.Info_04 = round((result.get('e2y') - offsetEnd) * 25.4, 2) #Y End Position
                #fasten.Info_10 = round(fasten.Info_04 - fasten.Info_02, 2)  
                motionlength = fasten.Info_04 - fasten.Info_02
                fastenCount = round(motionlength / studSpace) + 1
                fasten.Info_10 = round(motionlength / fastenCount) 
                if fasten.missionID == 110:
                    fasten.Info_11 = self.machine.toolIndex
                    if self.machine.toolIndex >= 8:
                        self.machine.toolIndex = 1
                    else:
                        self.machine.toolIndex = self.machine.toolIndex << 1
            # Horizantal
            elif result.get('e4x') - result.get('e1x') > 3:
                fasten.Info_02 = round((result.get('e1y') + 0.75) * 25.4, 2) #Y Start Position
                fasten.Info_04 = round((result.get('e1y') + 0.75) * 25.4, 2) #Y Start Position
                if result.get('e1x') < sql_wStart:
                    fasten.Info_01 = round((sql_wStart + offsetStart) * 25.4, 2)
                else:
                    fasten.Info_01 = round((result.get('e1x') + offsetStart)*25.4, 2)
                if result.get('e4x') > sql_wEnd:
                    fasten.Info_03 = round((sql_wEnd - offsetEnd) * 25.4, 2)
                else:
                    fasten.Info_03 = round((result.get('e4x') - offsetEnd) * 25.4, 2)
                motionlength = fasten.Info_03 - fasten.Info_01
                fastenCount = round(motionlength / studSpace) + 1
                fasten.Info_10 = round(motionlength / fastenCount) 
                if fasten.Info_10 < 75:
                    fasten.Info_10 = studSpace
                if fasten.missionID == 110:
                    fasten.Info_11 = self.machine.toolIndex
                    if self.machine.toolIndex >= 8:
                        self.machine.toolIndex = 1
                    else:
                        self.machine.toolIndex = self.machine.toolIndex << 1    

                fasten = self.crossRefCutOut(self.panel.guid, fasten, pgDB)     

            else:
                logging.warning('Did not add fastening for member' + self.panel.guid + '__'  + result.get('elementguid'))
            
            fasten.Info_09 = self.getCWS(result, pgDB, self.storeCWSFound)
            if fasten.Info_09 > 0:
                self.storeCWSFound = fasten.Info_09

            fastenlst.append(fasten)
        pgDB.close()
        return fastenlst
            
    
    def getFastener(self, layer, station) -> list [rdh.missionData_RBC]:
        studSpace = 406
        # Open Database Connection
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        sql_var1= self.panel.guid #Panel ID        
        sql_wStart =  0 #Leading Edge of the Board (Width)        
        sql_wEnd = self.panel.panelLength #Trailing Edge of the Board (Width)
        #Get parameters to determine min and max window to temp fasten material
        if station == 2:        
            sql_vMin = round(self.machine.ec2.parmData.getParm('ZL Core', 'Y Middle Vertical') / 25.4, 2)
            sql_vMax = round(self.machine.ec2.parmData.getParm('ZL Core', 'Y Build Max') / 25.4, 2)
        elif station == 3: 
            sql_vMin = round(self.machine.ec3.parmData.getParm('ZL Core', 'Y Middle Vertical') / 25.4, 2)
            sql_vMax = round(self.machine.ec3.parmData.getParm('ZL Core', 'Y Build Max') / 25.4, 2)
        sql_select_query=f"""
                            select to_jsonb(se) 
                            from cad2fab.system_elements se 
                            where panelguid = '{sql_var1}' 
                            and description = 'Sheathing' 
                            and b1y = '{layer}' 
                            and e1y < '{sql_vMin}' 
                            and e2y < '{sql_vMax}' 
                            and e1x <= '{sql_wEnd}' 
                            and e4x > '{sql_wStart}' 
                            and "actual_width" > 30  
                            """   
        
        #Determine Start End Shift
        shiftSTART = [0.75, 1, 1.25]
        shiftEND = [0.75, 1.25, 1.25]      
        offsetStart = shiftSTART[self.panel.getLayerIndex(layer)]
        offsetEnd = shiftEND[self.panel.getLayerIndex(layer)]      
        resultSheath = pgDB.query(sqlStatement=sql_select_query) #Look at Sheaths for Edge Conditions
        fastenlst : list [rdh.missionData_RBC]= []
        for sheet in resultSheath:
            sheet : dict = sheet[0]
            sql_wStart = sheet.get('e1x')
            sql_wEnd = sheet.get('e4x')
            sql_vMax = sheet.get('e2y')

            sql_select_query=f"""
                                select to_jsonb(se) 
                                from cad2fab.system_elements se
                                where 
                                    panelguid = '{sql_var1}' 
                                    and description not in ('Nog', 'Sheathing','VeryTopPlate','Rough cutout','FillerBtmNailer','HeaderSill','Header') 
                                    and e2y <= '{sql_vMax}' and e2y >= '{sql_vMin}' 
                                    and e1x < '{sql_wEnd}' and e4x > '{sql_wStart}' 
                                    and b2y = 0 
                                    order by b3x 
                                """    
            results = pgDB.query(sqlStatement=sql_select_query) 
            # Process Results
            for result  in results:
                result : dict = result[0]
                fasten = rdh.missionData_RBC(self.panel.getLayerFastener(self.panel.getLayerIndex(layer)))
                #fasten.missionID = iMaterial.getFastenType()
                #Vertical vs Horizantal Vertial dimension is less than 6inch
                #Vertical
                if  result.get('e2y') - result.get('e1y') > 3:
                    if sql_wEnd > result.get('e4x') and sql_wStart <= result.get('e1x'):
                        fasten.Info_01 = round((result.get('e1x') + 0.75) * 25.4,2) #X Start Position
                        fasten.Info_03 = round((result.get('e1x') + 0.75) * 25.4, 2) #X End Position    
                    elif sql_wEnd < result.get('e4x'): #Condition when stud is overhanging the board on the positive side
                        fasten.Info_01 = round((result.get('e1x') + 0.375) * 25.4,2) #X Start Position
                        fasten.Info_03 = round((result.get('e1x') + 0.375) * 25.4, 2) #X End Position
                    elif sql_wStart > result.get('e1x'): #Condition when stud is overhanging the board on the positive side
                        fasten.Info_01 = round((result.get('e4x') - 0.375) * 25.4,2) #X Start Position
                        fasten.Info_03 = round((result.get('e4x') - 0.375) * 25.4, 2) #X End Position    
                    else:
                        logging.warning('Did not add fastening for member' + self.panel.guid + '__'  + result.get('elementguid'))
                        continue               
                    if result.get('e1y') < sql_vMin:
                        fasten.Info_02 = round((sql_vMin + offsetStart) * 25.4, 2) #Y Start Position
                    else:
                        fasten.Info_02 = round((result.get('e1y') + offsetStart)*25.4, 2) #Y Start Position
                    if result.get('e2y') > sql_vMax:
                        fasten.Info_04 = round((sql_vMax - offsetEnd)*25.4, 2) #Y End Position
                    else:
                        fasten.Info_04 = round((result.get('e2y') - offsetEnd) * 25.4, 2) #Y End Position
                    motionlength = fasten.Info_04 - fasten.Info_02
                    fastenCount = round(motionlength / studSpace) + 1
                    fasten.Info_10 = round(motionlength / fastenCount) 
                    if fasten.missionID == 110:
                        fasten.Info_11 = self.machine.toolIndex
                        if self.machine.toolIndex >= 8:
                            self.machine.toolIndex = 1
                        else:
                            self.machine.toolIndex = self.machine.toolIndex << 1
                    vert = 'Vert'
                # Horizantal
                elif result.get('e4x') - result.get('e1x') > 3:
                    fasten.Info_02 = round((result.get('e1y') + 0.75) * 25.4, 2) #Y Start Position
                    fasten.Info_04 = round((result.get('e1y') + 0.75) * 25.4, 2) #Y Start Position
                    if result.get('e1x') < sql_wStart:
                        fasten.Info_01 = round((sql_wStart + offsetStart) * 25.4, 2)
                    else:
                        fasten.Info_01 = round((result.get('e1x')+ offsetStart)*25.4, 2)
                    if result.get('e4x') > sql_wEnd:
                        fasten.Info_03 = round((sql_wEnd - offsetEnd) * 25.4, 2)
                    else:
                        fasten.Info_03 = round((result.get('e4x') - offsetEnd) * 25.4, 2)
                    print()
                    motionlength = fasten.Info_03 - fasten.Info_01
                    fastenCount = round(motionlength / studSpace) + 1
                    fasten.Info_10 = round(motionlength / fastenCount) 
                    if fasten.Info_10 < 75:
                        fasten.Info_10 = studSpace                    
                    if fasten.missionID == 110:
                        fasten.Info_11 = self.machine.toolIndex
                        if self.machine.toolIndex >= 8:
                            self.machine.toolIndex = 1
                        else:
                            self.machine.toolIndex = self.machine.toolIndex << 1
                    vert = 'Horz'
                    fasten = self.crossRefCutOut(self.panel.guid, fasten, pgDB)     
                else:
                    logging.warning('Did not add fastening for member' + self.panel.guid + '__'  + result.get('elementguid'))
                fastenlst.append(fasten)
                print(vert + '--' + str(len(fastenlst)) + '--' + str(fasten.Info_01) + '--' + str(fasten.Info_03) + '--' + result['description'])
        pgDB.close()
        return fastenlst

    def crossRefCutOut(self, panelID, mission : rdh.missionData_RBC, dbConnection : dbc.DB_Connect):
        sql_var1 = panelID
        sql_wStart = round(mission.Info_01 / 25.4, 2)
        sql_wEnd = round(mission.Info_03 / 25.4, 2)
        sql_vStart = round(mission.Info_02 / 25.4, 2)
        sql_vEnd = round(mission.Info_04  / 25.4, 2)
        
        sql_select_Prequery=f"""
            select to_jsonb(se) 
            from cad2fab.system_elements se
            where 
                panelguid = '{sql_var1}' 
                and description in ('Rough cutout') 
                and (e1x < {sql_wEnd} and e1x > {sql_wStart} and e4y  <= {sql_vStart} and e1y >= {sql_vStart})
            """    
        sql_select_Postquery=f"""
            select to_jsonb(se) 
            from cad2fab.system_elements se
            where 
                panelguid = '{sql_var1}' 
                and description in ('Rough cutout') 
                and (e3x > {sql_wStart} and e3x < {sql_wEnd} and e4y  <= {sql_vStart} and e1y >= {sql_vStart})
            """   
        preResult = dbConnection.query(sqlStatement=sql_select_Prequery) 
        postResult = dbConnection.query(sqlStatement=sql_select_Postquery) 
        if len(preResult) > 0:
            result : dict = preResult[0][0]
            if round(result.get('e4x') * 25.4, 2) <= mission.Info_03:
                mission.Info_03 = round((result.get('e4x') - 0.75) * 25.4, 2)
            if round(result.get('e4x') * 25.4, 2) <= mission.Info_01:
                mission.Info_01 = round((result.get('e4x') - 0.75) * 25.4, 2)
        elif len(postResult) > 0:
            result : dict = postResult[0][0]
            if round(result.get('e3x') * 25.4, 2) >= mission.Info_01:
                mission.Info_01 = round((result.get('e4x') + 0.75) * 25.4, 2)
            if round(result.get('e3x') * 25.4, 2) >= mission.Info_03:
                mission.Info_03 = round((result.get('e4x') + 0.75) * 25.4, 2)
            
            mission.Info_01 = round(result.get('e3x') * 25.4, 2)

        return mission

    def getRoughOutCut(self, layer, station):
        # Open Database Connection
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        sql_var1= self.panel.guid
        sql_var2 = layer
        sql_select_query=f"""
                        SELECT to_jsonb(panel)
                        from cad2fab.system_elements panel
                        where panelguid = '{sql_var1}' AND description = 'Rough cutout' 
                        order by b1x;
                        """    
    
        results = pgDB.query(sqlStatement=sql_select_query) 
        pgDB.close()         
        routelst : list [rdh.missionData_RBC]= []
        routerDIA = 0.5
        scrapToolHalfLen = 822
        scrapToolShift = 200
        for result  in results:
            result : dict = result[0] 
            cutBottomTop = False
            count = 0                
            #R1 Cut
            if not cutBottomTop:
                #Bottom Left Corner [x,y]
                p1 = {'x':0 , 'y':0}
                #Top Right Corner [x,y]
                p2 = {'x':0 , 'y':0}

                #Find Bottom Left
                p1['x'] = result.get('e4x') 
                p1['y'] = result.get('e4y') 
                if result.get('e3x') < p1['x']: p1['x'] = result.get('e3x') 
                if result.get('e2x') < p1['x']: p1['x'] = result.get('e2x')                     
                if result.get('e1x') < p1['x']: p1['x'] = result.get('e1x')   
                if result.get('e3y') < p1['y']: p1['y'] = result.get('e3y') 
                if result.get('e2y') < p1['y']: p1['y'] = result.get('e2y')                     
                if result.get('e1y') < p1['y']: p1['y'] = result.get('e1y')     
                p1['x'] =round((p1['x']) * 25.4, 2)
                p1['y'] =round((p1['y']) * 25.4, 2)  

                #Find Top Right
                p2['x'] = result.get('e4x')
                p2['y'] = result.get('e4y')
                if result.get('e3x') > p2['x']: p2['x'] = result.get('e3x')
                if result.get('e2x') > p2['x']: p2['x'] = result.get('e2x')                    
                if result.get('e1x') > p2['x']: p2['x'] = result.get('e1x')  
                if result.get('e3y') > p2['y']: p2['y'] = result.get('e3y')
                if result.get('e2y') > p2['y']: p2['y'] = result.get('e2y')                    
                if result.get('e1y') > p2['y']: p2['y'] = result.get('e1y')     
                p2['x'] =round((p2['x']) * 25.4, 2)
                p2['y'] =round((p2['y']) * 25.4, 2)                                     
                #                                     
                #
                route = rdh.missionData_RBC(200)
                route.Info_01 = p1['x']
                route.Info_02 = p1['y']
                route.Info_03 = round(p2['x'] - p1['x'], 2)
                route.Info_04 = round(p2['y'] - p1['y'], 2)
                route.Info_05 = 1 
                routelst.append(route) 
            else:
                logging.warning('Did not add Route for member' + self.panel.guid + '__'  + result.get('elementguid'))
                break 

        return routelst


    def getEndCut(self, layer):
        # Open Database Connection
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        sql_var1= self.panel.guid
        sql_var2 = layer
        sql_select_query=f"""
                        SELECT to_jsonb(panel)
                        from cad2fab.system_elements panel
                        where panelguid = '{sql_var1}' AND "type" = 'Sheet' and actual_width < 48
                        order by b1x;
                        """    
    
        results = pgDB.query(sqlStatement=sql_select_query) 
        pgDB.close()         
        routelst : list [rdh.missionData_RBC]= []
        routerDIA = 12
        
        for result  in results:
            result : dict = result[0]
            
            cutBottomTop = False
            while cutBottomTop == False:
                route = rdh.missionData_RBC(160)
                #R1 Cut
                if not cutBottomTop:
                    if  result.get('e1x') > 0 and result.get('e3x') > 0:
                        route.Info_01 = round((result.get('e3x') + routerDIA/2) * 25.4, 2)
                        route.Info_02 = 0
                        route.Info_03 = round((result.get('e3x') + routerDIA/2) * 25.4, 2)
                        route.Info_04 = 1500 
                    else:
                        logging.warning('Did not add Route for member' + self.panel.guid + '__'  + result.get('elementguid'))
                        break 
                if not cutBottomTop:
                    if  result.get('e1x') > 0 and result.get('e3x') > 0:
                        route.Info_01 = round((result.get('e3x') + routerDIA/2) * 25.4, 2)
                        route.Info_02 = 1500
                        route.Info_03 = round((result.get('e3x') + routerDIA/2) * 25.4, 2)
                        route.Info_04 = round((result.get('e2y') + routerDIA) * 25.4, 2) 
                    else:
                        logging.warning('Did not add Route for member' + self.panel.guid + '__'  + result.get('elementguid'))
                        break         


                routelst.append(route)

        return routelst

    def getCWS(self, element : dict, ipgDB : dbc, maxPrevious):
        cwsPos = 0
        if element.get('description') == 'Stud':
            sql_var1= self.panel.guid #Panel ID    
            sql_var2= element.get('elementguid')
            sql_wStart =  element.get('e1x') - 6  #Leading Edge of Window Next to Element In Question        
            sql_wEnd = element.get('e1x') + 0.25 #Trailing Edge of Window Next to Element In Question   
            sql_select_query1=f"""
                                select *
                                from cad2fab.system_elements se 
                                where ((e1x between '{sql_wStart}' and '{sql_wEnd}') or (e2x between '{sql_wStart}' and '{sql_wEnd}') or (e3x between '{sql_wStart}' and '{sql_wEnd}') or (e4x between '{sql_wStart}' and '{sql_wEnd}'))
                                and panelguid = '{sql_var1}'
                                and elementguid != '{sql_var2}';
                                """    
            
            sql_wStart =  element.get('e3x') - 0.25  #Leading Edge of Window Next to Element In Question        
            sql_wEnd = element.get('e3x') + 6 #Trailing Edge of Window Next to Element In Question   
            
            sql_select_query2=f"""
                                select *
                                from cad2fab.system_elements se 
                                where ((e1x between '{sql_wStart}' and '{sql_wEnd}') or (e2x between '{sql_wStart}' and '{sql_wEnd}') or (e3x between '{sql_wStart}' and '{sql_wEnd}') or (e4x between '{sql_wStart}' and '{sql_wEnd}'))
                                and panelguid = '{sql_var1}'
                                and elementguid != '{sql_var2}';
                                """    

            results_Pre = ipgDB.query(sqlStatement=sql_select_query1) 
            results_Post = ipgDB.query(sqlStatement=sql_select_query2) 
            if len(results_Pre) == 0 and len(results_Post) == 0 and element.get('e1x') > (round(maxPrevious/25.4, 2) + 1):
                leadEdge = element.get('e1x')
                trailEdge = element.get('e3x')
                cwsPos = round((leadEdge + (trailEdge - leadEdge)/2) * 25.4, 2)

        print(cwsPos)
        return cwsPos



