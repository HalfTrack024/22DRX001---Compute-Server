import logging
# Project Dependencies
from util.panelData import Panel
from util.machineData import Line
from util.machineData import Station
import util.dataBaseConnect as dbc
import util.runData_Helper as rdh
from util.material import Material
from util.globals import Build_RBC_Progress


class RunData:
    fastenTypes = {
        'OSB': 1,
        'PLYWOOD': 2,
        'GLASROC': 3,
        'ZIP R3': 4,
        'ZIP R6': 5,
        'ZIP R9': 6,
    }
    materialTypes: list[str]
    layers: list[float]

    def __init__(self, panel: Panel, machine: Line):
        self.storeCWSFound = 0
        self.track_sheets = []
        self.panel = panel
        self.machine = machine
        self.build_rbc_progress = Build_RBC_Progress()
        # This is used to evaluate if the layer count stored matches the panel. 
        # If Not re-run load balancing prediction 
        if self.machine.predict_layer_count != self.panel.get_layer_count():
            self.machine.change_prediction(self.panel.get_layer_count())

    def rd_main(self):  # Main Call for Run Data.

        # raise NotImplementedError("Not implemented")
        # Open Database Connection
        pgDB = dbc.DB_Connect()

        self.layers = [0, 0.437]
        # Insert EC2 Run Data to DataBase
        sql_var1 = self.panel.guid
        sql_var2 = 12
        if len(self.panel.layer_pos) > 0:
            self.build_rbc_progress.ec2_status = "In-Progress"
            sRunData_EC2 = self.rd_EC2_Main()
            sql_var3 = sRunData_EC2
            self.build_rbc_progress.ec2_status = "Complete"
        else:
            self.build_rbc_progress.ec2_status = "No Work To Do"
            layerEmpty = rdh.Layers_RBC(sql_var2)
            sLayerEmpty = layerEmpty.to_json()
            sql_var3 = sLayerEmpty
        pgDB.open()
        # send OpData to JobData table
        sql_JobData_query = '''
                            INSERT INTO cad2fab.rbc_jobdata
                            (sItemName, stationID, jobdata)
                            VALUES(%s,%s,%s)
                            ON CONFLICT (sitemname, stationID)
                            DO UPDATE SET jobdata = EXCLUDED.jobdata;
                            '''
        # make a list of tuples for query many
        jdQueryData = [[sql_var1, sql_var2, sql_var3]]
        tmp = pgDB.query_many(sql_JobData_query, jdQueryData)
        # Close Connection
        pgDB.close()
        # Insert EC3 Run Data to DataBase
        sql_var1 = self.panel.guid
        sql_var2 = 22
        if len(self.panel.layer_pos) > 0:
            self.build_rbc_progress.ec3_status = "In-Progress"
            sRunData_EC3 = self.rdEC3_Main()
            sql_var3 = sRunData_EC3
            self.build_rbc_progress.ec3_status = "Complete"
        else:
            self.build_rbc_progress.ec3_status = "No Work To Do"
            layerEmpty = rdh.Layers_RBC(sql_var2)
            sLayerEmpty = layerEmpty.to_json()
            sql_var3 = sLayerEmpty

        pgDB.open()
        # send OpData to JobData table
        sql_JobData_query = '''
                            INSERT INTO cad2fab.rbc_jobdata
                            (sItemName, stationID, jobdata)
                            VALUES(%s,%s,%s)
                            ON CONFLICT (sitemname, stationID)
                            DO UPDATE SET jobdata = EXCLUDED.jobdata;
                            '''
        # make a list of tuples for query many
        jdQueryData = [[sql_var1, sql_var2, sql_var3]]
        tmp = pgDB.query_many(sql_JobData_query, jdQueryData)
        # Close Connection
        pgDB.close()

    def rd_EC2_Main(self) -> str:  # Main Call to assign what work will be allowed to complete on EC2
        self.build_rbc_progress.ec2_status = 'In-Progress'
        self.track_sheets.clear()
        # Prediction Keys ['oEC2_Place',	'oEC3_Place',	'oEC2_Fasten',	'oEC3_Fasten',	'oEC2_Routing',	'oEC3_Routing']
        load_balance = self.machine.get_prediction()
        layers = rdh.Layers_RBC(11)
        # Determine how much material is being placed with EC2
        missionPlace = [None, None, None, None, None]
        match load_balance.get('oEC2_Place'):
            case 100:
                # Condition if only one layer is being applied by EC2
                missionPlace[0] = self.getSheets(self.panel.get_layer_position(0), 2)
                missionPlace[0] = True
                self.build_rbc_progress.ec2_operations.append('Place and Fasten Layer 1')
            case 200:
                # Layer 1
                missionPlace[0] = self.getSheets(self.panel.get_layer_position(0), 2)
                missionPlace[0] = True
                # Layer 2
                missionPlace[1] = self.getSheets(self.panel.get_layer_position(1), 2)
                missionPlace[1] = True
                self.build_rbc_progress.ec2_operations.append('Place and Fasten Layer 1/2')
            case 123:
                for i in range(self.panel.get_layer_count()):
                    # missionPlace[i] = self.getSheets(self.panel.getLayerPosition(i), 2)
                    missionPlace[i] = True
                    self.build_rbc_progress.ec2_operations.append('Place and Fasten All Layers')

            case default:
                self.build_rbc_progress.ec2_operations.append('No Place and Fasten on EC2')
                logging.info('no material is placed with EC2')

        # Determine if EC2 is fastening material that was loaded
        missionFasten = [None, None, None, None, None]
        match load_balance.get('oEC2_Fasten'):
            case 100:
                missionFasten[0] = self.get_fastener(self.panel.get_layer_position(0), 2)
                self.build_rbc_progress.ec2_operations.append('Fasten Layer 1')
            case 200:
                missionFasten[0] = self.get_fastener(self.panel.get_layer_position(0), 2)
                missionFasten[1] = self.get_fastener(self.panel.get_layer_position(1), 2)
                self.build_rbc_progress.ec2_operations.append('Fasten Layer 1/2')
            case 123:
                for i in range(self.panel.get_layer_count()):
                    missionFasten[i] = self.get_fastener(self.panel.get_layer_position(i), 2)
                    self.build_rbc_progress.ec2_operations.append('Fasten All Layers')

            case default:
                self.build_rbc_progress.ec2_operations.append('No Fastening on EC2')
                logging.info('no material is fastened with EC2')

        # Determine if EC2 is Routing any material
        missionRoute = [None, None, None, None, None]
        missionRouting = []
        match load_balance.get('oEC2_Routing'):
            case 100:
                missionRouting.extend(self.getRoughOutCut(self.panel.get_layer_position(0), 2))
                # missionRouting.extend(self.getEndCut(self.panel.getLayerPosition(0), 2))
                missionRoute[0] = missionRouting
                self.build_rbc_progress.ec2_operations.append('Route Layer 1')
            case 200:
                missionRouting.extend(self.getRoughOutCut(self.panel.get_layer_position(1), 2))
                # missionRouting.extend(self.getEndCut(self.panel.getLayerPosition(1), 2))
                missionRoute[1] = missionRouting
                self.build_rbc_progress.ec2_operations.append('Route Layer 1/2')
            case 123:
                for i in range(self.panel.get_layer_count()):
                    missionRoute[i] = self.getRoughOutCut(self.panel.get_layer_position(i), 2)
                # missionRouting.extend(self.getEndCut(self.panel.getLayerPosition(1), 2))
                missionRoute[1] = missionRouting
                self.build_rbc_progress.ec2_operations.append('Route All Layers')
            case default:
                self.build_rbc_progress.ec2_operations.append('No Routing on EC2')
                logging.info('no material is Routed with EC2')

        # Combine Place, Fasten, and Route Data to Layer

        for i in range(self.panel.get_layer_count()):
            used = False
            layer = rdh.Layer_RBC(self.panel.get_layer_position(i))
            if missionPlace[i] is not None:
                layer = self.getSheets(self.panel.get_layer_position(i), 2)  # Determine if any boards have been placed for that layer
                used = True
            if missionFasten[i] is not None:
                layer.add_mission(missionFasten[i])  # Determine if any fasteners have been used for that layer
                used = True
            if missionRoute[i] is not None:
                layer.add_mission(missionRoute[i])  # Determine if any routing have been used for that layer
                used = True
            if used:
                layer.set_properties(round(self.panel.get_layer_position(i) * 25.4, 1))
                layers.add_layer(layer)
                # layers._layers.append(layer)

        # Returns a converted layers object to a json string
        return layers.to_json()

    def rdEC3_Main(self):  # Main Call to assign what work will be allowed to complete on EC3
        # Prediction Keys ['oEC2_Place',	'oEC3_Place',	'oEC2_Fasten',	'oEC3_Fasten',	'oEC2_Routing',	'oEC3_Routing']
        loadbalance = self.machine.get_prediction()
        layers_ec3 = rdh.Layers_RBC(21)
        self.track_sheets.clear()
        station = Station(self.machine.ec2)
        # Determine how much material is being placed with EC2
        missionPlace = [None, None, None, None, None]
        match loadbalance.get('oEC3_Place'):
            case 100:
                # Condition if only one layer is being applied by EC2
                missionPlace[0] = self.getSheets(self.panel.get_layer_position(0), 3)
                missionPlace[0] = True
                self.build_rbc_progress.ec3_operations.append('Place and Fasten Layer 1')
            case 200:
                # Layer 1
                missionPlace[1] = self.getSheets(self.panel.get_layer_position(1), 3)
                missionPlace[1] = True
                # Layer 2
                # missionPlace[1] = self.getSheets(self.panel.getLayerPosition(1), 3)
                missionPlace[1] = True
                self.build_rbc_progress.ec3_operations.append('Place and Fasten Layer 2')
            case 123:
                for i in range(self.panel.get_layer_count()):
                    missionPlace[i] = self.getSheets(self.panel.get_layer_position(i), 3)
                    missionPlace[i] = True
                    self.build_rbc_progress.ec3_operations.append('Place and Fasten All Layers')

            case default:
                self.build_rbc_progress.ec3_operations.append('No Place and Fasten on EC3')
                logging.info('no material is placed with EC3')

        # Determine if EC3 is fastening material that was loaded
        missionFasten = [None, None, None, None, None]
        match loadbalance.get('oEC3_Fasten'):
            case 100:
                missionFasten[0] = self.get_fastener(self.panel.get_layer_position(0), 3)
                self.build_rbc_progress.ec3_operations.append('Fasten Layer 1')
            case 200:
                # missionFasten[0] = self.getFastener(self.panel.getLayerPosition(0), 3)
                missionFasten[1] = self.get_fastener(self.panel.get_layer_position(1), 3)
                self.build_rbc_progress.ec3_operations.append('Fasten Layer 2')
            case 123:
                for i in range(self.panel.get_layer_count()):
                    missionPlace[i] = self.get_fastener(self.panel.get_layer_position(i), 3)
                    self.build_rbc_progress.ec3_operations.append('Fasten All Layers')
            case default:
                self.build_rbc_progress.ec3_operations.append('No Fastening on EC3')
                logging.info('no material is fastened with EC3')

        # Determine if EC3 is Routing any material
        missionRoute = [None, None, None, None, None]
        missionRouting = []
        match loadbalance.get('oEC3_Routing'):
            case 100:
                missionRouting.extend(self.getRoughOutCut(self.panel.get_layer_position(0), 2))
                # missionRouting.extend(self.getEndCut(self.panel.getLayerPosition(0), 2))
                missionRoute[0] = missionRouting
                self.build_rbc_progress.ec3_operations.append('Route Layer 1')
            case 200:
                missionRouting.extend(self.getRoughOutCut(self.panel.get_layer_position(1), 2))
                # missionRouting.extend(self.getEndCut(self.panel.getLayerPosition(1), 2))
                missionRoute[1] = missionRouting
                self.build_rbc_progress.ec3_operations.append('Route Layer 2')
            case 123:
                missionRouting.extend(self.getRoughOutCut(self.panel.get_layer_position(1), 2))
                # missionRouting.extend(self.getEndCut(self.panel.getLayerPosition(1), 2))
                missionRoute[1] = missionRouting
                self.build_rbc_progress.ec3_operations.append('Route All Layers')
            case default:
                self.build_rbc_progress.ec3_operations.append('No Routing on EC3')
                logging.info('no material is Routed with EC3')

        # Combine Place, Fasten, and Route Data to Layer
        for i in range(self.panel.get_layer_count()):
            used = False
            layer = rdh.Layer_RBC(self.panel.get_layer_position(i))

            if missionPlace[i] is not None:
                layer = self.getSheets(self.panel.get_layer_position(i), 3)  # Determine if any boards have been placed for that layer
                used = True
            if missionFasten[i] is not None:
                layer.add_mission(missionFasten[i])  # Determine if any fasteners have been used for that layer
                used = True
            if missionRoute[i] is not None:
                layer.add_mission(missionRoute[i])  # Determine if any routing have been used for that layer
                used = True
            if used:
                layer.set_properties(round(self.panel.get_layer_position(i) * 25.4, 1))
                layers_ec3.add_layer(layer)

        # Returns a converted layers object to a json string
        sample = layers_ec3.to_json()
        return layers_ec3.to_json()

    # Get Sheet Information       
    def getSheets(self, layer, station) -> rdh.Layer_RBC:  # This fucntion will load the sheets of Material to the
        # Open Database Connection
        pgDB = dbc.DB_Connect()
        pgDB.open()
        sql_var1 = self.panel.guid
        sql_var2 = layer
        if station == 2:
            sql_var3 = round(self.machine.ec2.partial_board / 25.4, 0)
        else:
            sql_var3 = round(self.machine.ec3.partial_board / 25.4, 0)
        sql_select_query = f"""
                        SELECT to_jsonb(panel)
                        from cad2fab.system_elements panel
                        where panelguid = '{sql_var1}' 
                        and "type" = 'Sheet' 
                        and b2y = '{sql_var2}'
                        and "actual_width" > {sql_var3} 
                        and e1x >= 0
                        order by b1x 
                        """
        # sql_select_query=f"""
        #                SELECT to_jsonb(panel)
        #                from cad2fab.system_elements panel
        #                where panelguid = '{sql_var1}' AND "type" = 'Sheet' and b1y = {sql_var2}
        #                order by b1x;
        #                """    
        results = pgDB.query(sql_select_query)
        pgDB.close()
        layerData = rdh.Layer_RBC(layer)

        logging.info("results: " + str(results))
        self.storeCWSFound = 0
        for sheet in results:
            # change list to object
            sheet: dict = sheet[0]
            material = Material(sheet, self.machine.get_system_parms(station))
            # f.writelines('Sheets: '+str(sheet)+ '   Material: '+str(material))

            # Board Pick
            pick = rdh.missionData_RBC(400)
            pick.Info_01 = round(sheet.get('e1x') * 25.4, 2)  # e1x
            pick.Info_02 = round(sheet.get('e1y') * 25.4, 2)  # e1y
            pick.Info_03 = round(sheet.get('actual_width') * 25.4, 2)
            if 48 > sheet.get('actual_width') > 30:
                pick.Info_03 = round(48 * 25.4, 2)
            else:
                pick.Info_03 = round(sheet.get('actual_width') * 25.4, 2)
            if "96" in sheet.get('size'):
                pick.Info_04 = 2438.4

            elif "108" in sheet.get('size'):
                pick.Info_04 = 2743.2

            elif "120" in sheet.get('size'):
                pick.Info_04 = 3048

            else:
                pick.Info_04 = 2438.4

            pick.Info_05 = round(sheet.get('actual_thickness') * 25.4, 2)
            pick.Info_06 = round(self.panel.panelThickness * 25.4 + pick.Info_05, 2)
            pick.Info_11 = material.getMaterialCode()
            pick.Info_12 = material.getMaterial()
            if pick.Info_12 not in self.build_rbc_progress.materials_required: self.build_rbc_progress.materials_required.append(pick.Info_12)
            self.build_rbc_progress.material_count += 1
            # Board Place
            place = rdh.missionData_RBC(material.getPlaceType())  # self.fastenTypes
            # place = rdh.missionData_RBC(material.placeNum) #self.fastenTypes
            place.Info_01 = round(sheet.get('e1x') * 25.4, 2)  # e1x
            place.Info_02 = round(sheet.get('e1y') * 25.4, 2)  # e1y
            place.Info_03 = 0
            place.Info_04 = 0
            place.Info_05 = 29
            place.Info_06 = round((sheet.get('e1x') + 0.75) * 25.4, 2)
            if place.missionID == 401:
                place.Info_11 = 1
            else:
                place.Info_11 = 0
            place.Info_12 = 0

            # Fastening
            fasteners = self.getboardFastener(pick, layer, material, station)
            # Pick and Place Locations are added to the list
            boardData = rdh.BoardData_RBC(board_pick=pick, board_place=place, board_fasten=fasteners)
            # Now we have to add the missions for temp fastening that board

            layerData.add_board(boardData)
            self.track_sheets.append(sheet.get('elementguid'))
        # this information will be used when building fastener requirements for layer
        layIndex = self.panel.get_layer_index(layer)
        fast = material.fastenNum

        self.panel.update_layer_fastener(layIndex, fast)

        return layerData

    def getboardFastener(self, board: rdh.missionData_RBC, active_layer, iMaterial: Material, station) -> list[rdh.missionData_RBC]:
        studSpace = 406
        shiftspace = round(18 / 25.4, 2)
        # Open Database Connection

        pgDB = dbc.DB_Connect()
        pgDB.open()
        sql_var1 = self.panel.guid  # Panel ID
        sql_wStart = round(board.Info_01 / 25.4, 2)  # Leading Edge of the Board (Width)
        sql_wEnd = round((board.Info_01 + board.Info_03) / 25.4, 2)  # Trailing Edge of the Board (Width)
        # Get parameters to determine min and max window to temp fasten material
        if station == 2:
            sql_vMin = 0  # machine.ec3.parmData.getParm('ZL Core', 'Y Min Vertical') /25.4
            sql_vMax = self.machine.ec2.parmData.getParm('ZL Core', 'Y Middle Vertical') / 25.4
        elif station == 3:
            sql_vMin = 0  # machine.ec3.parmData.getParm([], 'ZL Core', 'Y Min Vertical') / 25.4
            sql_vMax = self.machine.ec3.parmData.getParm('ZL Core', 'Y Middle Vertical') / 25.4

        sql_select_query = f"""
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
        results = pgDB.query(sql_statement=sql_select_query)

        # Determine Start End Shift
        shiftSTART = [shiftspace, shiftspace + 0.25, shiftspace + 0.5]
        shiftEND = [shiftspace, shiftspace + 0.5, shiftspace + 0.5]
        offsetStart = shiftSTART[self.panel.get_layer_index(active_layer)]
        offsetEnd = shiftEND[self.panel.get_layer_index(active_layer)]

        # Process Results
        fastenlst: list[rdh.missionData_RBC] = []
        for result in results:
            result: dict = result[0]
            fasten = rdh.missionData_RBC(iMaterial.getFastenType())
            # fasten.missionID = iMaterial.getFastenType()
            # Vertical vs Horizantal Vertial dimension is less than 6inch
            # Vertical
            if result.get('e2y') - result.get('e1y') > 3:
                if sql_wEnd > result.get('e4x') and sql_wStart <= result.get('e1x'):
                    fasten.Info_01 = round((result.get('e1x') + 0.75) * 25.4, 2)  # X Start Position
                    fasten.Info_03 = round((result.get('e1x') + 0.75) * 25.4, 2)  # X End Position
                elif sql_wEnd < result.get('e4x'):  # Condition when stud is overhanging the board on the positive side
                    fasten.Info_01 = round((result.get('e1x') + 0.375) * 25.4, 2)  # X Start Position
                    fasten.Info_03 = round((result.get('e1x') + 0.375) * 25.4, 2)  # X End Position
                elif sql_wStart > result.get(
                        'e1x'):  # Condition when stud is overhanging the board on the positive side
                    fasten.Info_01 = round((result.get('e4x') - 0.375) * 25.4, 2)  # X Start Position
                    fasten.Info_03 = round((result.get('e4x') - 0.375) * 25.4, 2)  # X End Position
                else:
                    logging.warning(
                        'Did not add fastening for member' + self.panel.guid + '__' + result.get('elementguid'))
                    continue
                if result.get('e1y') < sql_vMin:
                    fasten.Info_02 = round(sql_vMin * 25.4, 2)  # Y Start Position
                else:
                    fasten.Info_02 = round((result.get('e1y') + offsetStart) * 25.4, 2)  # Y Start Position
                if result.get('e2y') > sql_vMax:
                    fasten.Info_04 = round((sql_vMax - offsetEnd) * 25.4, 2)  # Y End Position
                else:
                    fasten.Info_04 = round((result.get('e2y') - offsetEnd) * 25.4, 2)  # Y End Position
                # fasten.Info_10 = round(fasten.Info_04 - fasten.Info_02, 2)
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
                fasten.Info_02 = round((result.get('e1y') + 0.75) * 25.4, 2)  # Y Start Position
                fasten.Info_04 = round((result.get('e1y') + 0.75) * 25.4, 2)  # Y Start Position
                if result.get('e1x') < sql_wStart:
                    fasten.Info_01 = round((sql_wStart + offsetStart) * 25.4, 2)
                else:
                    fasten.Info_01 = round((result.get('e1x') + offsetStart) * 25.4, 2)
                if result.get('e4x') > sql_wEnd:
                    fasten.Info_03 = round((sql_wEnd - offsetEnd) * 25.4, 2)
                else:
                    fasten.Info_03 = round((result.get('e4x') - offsetEnd) * 25.4, 2)
                motionlength = abs(fasten.Info_03 - fasten.Info_01)
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
                logging.warning('Did not add fastening for member' + self.panel.guid + '__' + result.get('elementguid'))

            fasten.Info_09 = self.getCWS(result, pgDB, self.storeCWSFound)
            if fasten.Info_09 > 0:
                self.storeCWSFound = fasten.Info_09

            fastenlst.append(fasten)
        pgDB.close()

        if iMaterial.fastener not in self.build_rbc_progress.fasteners_required: self.build_rbc_progress.fasteners_required.append(iMaterial.fastener)
        return fastenlst

    def get_fastener(self, layer, station) -> list[rdh.missionData_RBC]:
        studSpace = 406
        # Open Database Connection
        pgDB = dbc.DB_Connect()
        pgDB.open()
        sql_var1 = self.panel.guid  # Panel ID
        sql_var2 = tuple(self.track_sheets)

        sql_wStart = 0  # Leading Edge of the Board (Width)
        sql_wEnd = self.panel.panelLength  # Trailing Edge of the Board (Width)
        # Get parameters to determine min and max window to temp fasten material
        if station == 2:
            sql_vMin = round(self.machine.ec2.parmData.getParm('ZL Core', 'Y Middle Vertical') / 25.4, 2)
            sql_vMax = round(self.machine.ec2.parmData.getParm('ZL Core', 'Y Build Max') / 25.4, 2)
            sql_var3 = round(self.machine.ec2.partial_board / 25.4, 0)
        elif station == 3:
            sql_vMin = round(self.machine.ec3.parmData.getParm('ZL Core', 'Y Middle Vertical') / 25.4, 2)
            sql_vMax = round(self.machine.ec3.parmData.getParm('ZL Core', 'Y Build Max') / 25.4, 2)
            sql_var3 = round(self.machine.ec3.partial_board / 25.4, 0)
        sql_select_query = f"""
                            select to_jsonb(se) 
                            from cad2fab.system_elements se 
                            where panelguid = '{sql_var1}' 
                            and description = 'Sheathing' 
                            and b2y = '{layer}' 
                            and e1y < '{sql_vMin}' 
                            and e2y < '{sql_vMax}' 
                            and e1x <= '{sql_wEnd}' 
                            and e4x > '{sql_wStart}' 
                            and "actual_width" > 36 
                            and e1x >= 0
                            """
        #   and elementguid in '{sql_var2}'
        # Determine Start End Shift
        shiftSTART = [2.75, 1, 1.25]
        shiftEND = [0.75, 1.25, 1.25]

        offsetStart = shiftSTART[self.panel.get_layer_index(layer)]
        offsetEnd = shiftEND[self.panel.get_layer_index(layer)]
        resultSheath = pgDB.query(sql_statement=sql_select_query)  # Look at Sheaths for Edge Conditions
        fastenlst: list[rdh.missionData_RBC] = []
        for sheet in resultSheath:
            sheet: dict = sheet[0]
            sql_wStart = sheet.get('e1x')
            sql_wEnd = sheet.get('e4x')
            sql_vMax = sheet.get('e2y')

            sql_select_query = f"""
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
            results = pgDB.query(sql_statement=sql_select_query)
            # Process Results
            for result in results:
                result: dict = result[0]
                fasten = rdh.missionData_RBC(self.panel.get_layer_fastener(self.panel.get_layer_index(layer)))
                # fasten.missionID = iMaterial.getFastenType()
                # Vertical vs Horizantal Vertial dimension is less than 6inch
                # Vertical
                if result.get('e2y') - result.get('e1y') > 3:
                    if sql_wEnd > result.get('e4x') and sql_wStart <= result.get('e1x'):
                        fasten.Info_01 = round((result.get('e1x') + 0.75) * 25.4, 2)  # X Start Position
                        fasten.Info_03 = round((result.get('e1x') + 0.75) * 25.4, 2)  # X End Position
                    elif sql_wEnd < result.get(
                            'e4x'):  # Condition when stud is overhanging the board on the positive side
                        fasten.Info_01 = round((result.get('e1x') + 0.375) * 25.4, 2)  # X Start Position
                        fasten.Info_03 = round((result.get('e1x') + 0.375) * 25.4, 2)  # X End Position
                    elif sql_wStart > result.get(
                            'e1x'):  # Condition when stud is overhanging the board on the positive side
                        fasten.Info_01 = round((result.get('e4x') - 0.375) * 25.4, 2)  # X Start Position
                        fasten.Info_03 = round((result.get('e4x') - 0.375) * 25.4, 2)  # X End Position
                    else:
                        logging.warning(
                            'Did not add fastening for member' + self.panel.guid + '__' + result.get('elementguid'))
                        continue
                    if result.get('e1y') < sql_vMin:
                        fasten.Info_02 = round((sql_vMin + offsetStart) * 25.4, 2)  # Y Start Position
                    else:
                        fasten.Info_02 = round((result.get('e1y') + offsetStart) * 25.4, 2)  # Y Start Position
                    if result.get('e2y') > sql_vMax:
                        fasten.Info_04 = round((sql_vMax - offsetEnd) * 25.4, 2)  # Y End Position
                    else:
                        fasten.Info_04 = round((result.get('e2y') - offsetEnd) * 25.4, 2)  # Y End Position
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
                    fasten.Info_02 = round((result.get('e1y') + 0.75) * 25.4, 2)  # Y Start Position
                    fasten.Info_04 = round((result.get('e1y') + 0.75) * 25.4, 2)  # Y Start Position
                    if result.get('e1x') < sql_wStart:
                        fasten.Info_01 = round((sql_wStart + offsetStart) * 25.4, 2)
                    else:
                        fasten.Info_01 = round((result.get('e1x') + offsetStart) * 25.4, 2)
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
                    vert = 'Horz'
                    fasten = self.crossRefCutOut(self.panel.guid, fasten, pgDB)
                else:
                    logging.warning(
                        'Did not add fastening for member' + self.panel.guid + '__' + result.get('elementguid'))
                #  Apply
                fastenlst.append(fasten)

        pgDB.close()
        return fastenlst

    def crossRefCutOut(self, panelID, mission: rdh.missionData_RBC, dbConnection: dbc.DB_Connect):
        sql_var1 = panelID
        sql_wStart = round(mission.Info_01 / 25.4, 2)
        sql_wEnd = round(mission.Info_03 / 25.4, 2)
        sql_vStart = round(mission.Info_02 / 25.4, 2)
        sql_vEnd = round(mission.Info_04 / 25.4, 2)

        sql_select_Prequery = f"""
            select to_jsonb(se) 
            from cad2fab.system_elements se
            where 
                panelguid = '{sql_var1}' 
                and description in ('Rough cutout') 
                and (e1x < {sql_wEnd} and e1x > {sql_wStart} and e4y  <= {sql_vStart} and e1y >= {sql_vStart})
            """
        sql_select_Postquery = f"""
            select to_jsonb(se) 
            from cad2fab.system_elements se
            where 
                panelguid = '{sql_var1}' 
                and description in ('Rough cutout') 
                and (e3x > {sql_wStart} and e3x < {sql_wEnd} and e4y  <= {sql_vStart} and e1y >= {sql_vStart})
            """
        preResult = dbConnection.query(sql_statement=sql_select_Prequery)
        postResult = dbConnection.query(sql_statement=sql_select_Postquery)
        if len(preResult) > 0:
            result: dict = preResult[0][0]
            if round(result.get('e4x') * 25.4, 2) <= mission.Info_03:
                mission.Info_03 = round((result.get('e4x') - 0.75) * 25.4, 2)
            if round(result.get('e4x') * 25.4, 2) <= mission.Info_01:
                mission.Info_01 = round((result.get('e4x') - 0.75) * 25.4, 2)
        elif len(postResult) > 0:
            result: dict = postResult[0][0]
            if round(result.get('e3x') * 25.4, 2) >= mission.Info_01:
                mission.Info_01 = round((result.get('e4x') + 0.75) * 25.4, 2)
            if round(result.get('e3x') * 25.4, 2) >= mission.Info_03:
                mission.Info_03 = round((result.get('e4x') + 0.75) * 25.4, 2)

            mission.Info_01 = round(result.get('e3x') * 25.4, 2)

        return mission

    def getRoughOutCut(self, layer, station):
        # Open Database Connection
        pgDB = dbc.DB_Connect()
        pgDB.open()
        sql_var1 = self.panel.guid
        sql_var2 = layer
        sql_select_query = f"""
                        SELECT to_jsonb(panel)
                        from cad2fab.system_elements panel
                        where panelguid = '{sql_var1}' AND description = 'Rough cutout' 
                        order by b1x;
                        """

        results = pgDB.query(sql_statement=sql_select_query)
        pgDB.close()
        routelst: list[rdh.missionData_RBC] = []
        routerDIA = 0.5
        scrapToolHalfLen = 822
        scrapToolShift = 200
        for result in results:
            result: dict = result[0]
            cutBottomTop = False
            count = 0
            # R1 Cut
            if not cutBottomTop:
                # Bottom Left Corner [x,y]
                p1 = {'x': 0, 'y': 0}
                # Top Right Corner [x,y]
                p2 = {'x': 0, 'y': 0}

                # Find Bottom Left
                p1['x'] = result.get('e4x')
                p1['y'] = result.get('e4y')
                if result.get('e3x') < p1['x']: p1['x'] = result.get('e3x')
                if result.get('e2x') < p1['x']: p1['x'] = result.get('e2x')
                if result.get('e1x') < p1['x']: p1['x'] = result.get('e1x')
                if result.get('e3y') < p1['y']: p1['y'] = result.get('e3y')
                if result.get('e2y') < p1['y']: p1['y'] = result.get('e2y')
                if result.get('e1y') < p1['y']: p1['y'] = result.get('e1y')
                p1['x'] = round((p1['x']) * 25.4, 2)
                p1['y'] = round((p1['y']) * 25.4, 2)

                # Find Top Right
                p2['x'] = result.get('e4x')
                p2['y'] = result.get('e4y')
                if result.get('e3x') > p2['x']: p2['x'] = result.get('e3x')
                if result.get('e2x') > p2['x']: p2['x'] = result.get('e2x')
                if result.get('e1x') > p2['x']: p2['x'] = result.get('e1x')
                if result.get('e3y') > p2['y']: p2['y'] = result.get('e3y')
                if result.get('e2y') > p2['y']: p2['y'] = result.get('e2y')
                if result.get('e1y') > p2['y']: p2['y'] = result.get('e1y')
                p2['x'] = round((p2['x']) * 25.4, 2)
                p2['y'] = round((p2['y']) * 25.4, 2)
                #                                     
                #
                route = rdh.missionData_RBC(200)
                route.Info_01 = p1['x']
                route.Info_02 = p1['y']
                route.Info_03 = round(p2['x'] - p1['x'], 2)
                route.Info_04 = round(p2['y'] - p1['y'], 2)
                route.Info_05 = 1
                if self.panel.get_layer_index(layer) == 0:
                    route.Info_07 = round(layer * 25.4, 1)
                else:
                    route.Info_07 = round((layer - self.panel.get_layer_position(0)) * 25.4, 1)
                routelst.append(route)
            else:
                logging.warning('Did not add Route for member' + self.panel.guid + '__' + result.get('elementguid'))
                break

        return routelst

    def getEndCut(self, layer):
        # Open Database Connection
        pgDB = dbc.DB_Connect()
        pgDB.open()
        sql_var1 = self.panel.guid
        sql_var2 = tuple(self.track_sheets)
        sql_var3 = self.machine
        sql_select_query = f"""
                        SELECT to_jsonb(panel)
                        from cad2fab.system_elements panel
                        where panelguid = '{sql_var1}' 
                        AND elementguid in {sql_var2}
                        AND "type" = 'Sheet' and actual_width < 48
                        order by b1x;
                        """

        results = pgDB.query(sql_statement=sql_select_query)
        pgDB.close()
        routelst: list[rdh.missionData_RBC] = []
        routerDIA = 12

        for result in results:
            result: dict = result[0]

            cutBottomTop = False
            while cutBottomTop == False:
                route = rdh.missionData_RBC(160)
                # R1 Cut
                if not cutBottomTop:
                    if result.get('e1x') > 0 and result.get('e3x') > 0:
                        route.Info_01 = round((result.get('e3x') + routerDIA / 2) * 25.4, 2)
                        route.Info_02 = 0
                        route.Info_03 = round((result.get('e3x') + routerDIA / 2) * 25.4, 2)
                        route.Info_04 = 1500
                    else:
                        logging.warning(
                            'Did not add Route for member' + self.panel.guid + '__' + result.get('elementguid'))
                        break
                if not cutBottomTop:
                    if result.get('e1x') > 0 and result.get('e3x') > 0:
                        route.Info_01 = round((result.get('e3x') + routerDIA / 2) * 25.4, 2)
                        route.Info_02 = 1500
                        route.Info_03 = round((result.get('e3x') + routerDIA / 2) * 25.4, 2)
                        route.Info_04 = round((result.get('e2y') + routerDIA) * 25.4, 2)
                    else:
                        logging.warning(
                            'Did not add Route for member' + self.panel.guid + '__' + result.get('elementguid'))
                        break

                routelst.append(route)

        return routelst

    def getCWS(self, element: dict, ipgDB: dbc, maxPrevious):
        cwsPos = 0
        if element.get('description') == 'Stud':
            sql_var1 = self.panel.guid  # Panel ID
            sql_var2 = element.get('elementguid')
            sql_wStart = element.get('e1x') - 6  # Leading Edge of Window Next to Element In Question
            sql_wEnd = element.get('e1x') + 0.25  # Trailing Edge of Window Next to Element In Question
            sql_select_query1 = f"""
                                select *
                                from cad2fab.system_elements se 
                                where ((e1x between '{sql_wStart}' and '{sql_wEnd}') or (e2x between '{sql_wStart}' and '{sql_wEnd}') or (e3x between '{sql_wStart}' and '{sql_wEnd}') or (e4x between '{sql_wStart}' and '{sql_wEnd}'))
                                and panelguid = '{sql_var1}'
                                and elementguid != '{sql_var2}';
                                """

            sql_wStart = element.get('e3x') - 0.25  # Leading Edge of Window Next to Element In Question
            sql_wEnd = element.get('e3x') + 6  # Trailing Edge of Window Next to Element In Question

            sql_select_query2 = f"""
                                select *
                                from cad2fab.system_elements se 
                                where ((e1x between '{sql_wStart}' and '{sql_wEnd}') or (e2x between '{sql_wStart}' and '{sql_wEnd}') or (e3x between '{sql_wStart}' and '{sql_wEnd}') or (e4x between '{sql_wStart}' and '{sql_wEnd}'))
                                and panelguid = '{sql_var1}'
                                and elementguid != '{sql_var2}';
                                """

            results_Pre = ipgDB.query(sql_statement=sql_select_query1)
            results_Post = ipgDB.query(sql_statement=sql_select_query2)
            if len(results_Pre) == 0 and len(results_Post) == 0 and element.get('e1x') > (
                    round(maxPrevious / 25.4, 2) + 1):
                leadEdge = element.get('e1x')
                trailEdge = element.get('e3x')
                cwsPos = round((leadEdge + (trailEdge - leadEdge) / 2) * 25.4, 2)

        return cwsPos

    def getStudSpacing(self, element, station):
        default_paremeter = station.ec.get


def check_fasten_mission(fasten: rdh.missionData_RBC) -> rdh.missionData_RBC:
    # Check if mission values are ordered correctly and make sense
    if fasten.Info_01 > fasten.Info_03:
        temp_01 = fasten.Info_01
        temp_03 = fasten.Info_03
        fasten.Info_01 = temp_03
        fasten.Info_03 = temp_01
    if fasten.Info_02 > fasten.Info_04:
        temp_02 = fasten.Info_02
        temp_04 = fasten.Info_04
        fasten.Info_02 = temp_04
        fasten.Info_04 = temp_02

    if all(getattr(fasten, attr) < 0 for attr in vars(fasten)):
        fasten = None

    return fasten
