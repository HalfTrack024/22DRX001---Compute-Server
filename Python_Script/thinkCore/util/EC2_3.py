import logging
import math

import util.dataBaseConnect as dBC
import util.runData_Helper as rDH
from util.globals import Build_RBC_Progress
from util.machineData import Line
from util.machineData import Station
from util.material import Material
# Project Dependencies
from util.panelData import Panel


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
        pgDB = dBC.DB_Connect()

        self.layers = [0, 0.437]
        # Insert EC2 Run Data to DataBase
        sql_var1 = self.panel.guid
        sql_var2 = 12
        if len(self.panel.layer_pos) > 0:
            self.build_rbc_progress.ec2_status = "In-Progress"
            sRunData_EC2 = self.rd_ec2_main(self.machine.ec2)
            sql_var3 = sRunData_EC2
            self.build_rbc_progress.ec2_status = "Complete"
        else:
            self.build_rbc_progress.ec2_status = "No Work To Do"
            layerEmpty = rDH.Layers_RBC(sql_var2)
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
            sRunData_EC3 = self.rd_ec3_main(self.machine.ec3)
            sql_var3 = sRunData_EC3
            self.build_rbc_progress.ec3_status = "Complete"
        else:
            self.build_rbc_progress.ec3_status = "No Work To Do"
            layerEmpty = rDH.Layers_RBC(sql_var2)
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

    def rd_ec2_main(self, station: Station) -> str:  # Main Call to assign what work will be allowed to complete on EC2
        self.build_rbc_progress.ec2_status = 'In-Progress'
        # Prediction Keys ['oEC2_Place',	'oEC3_Place',	'oEC2_Fasten',	'oEC3_Fasten',	'oEC2_Routing',	'oEC3_Routing']
        load_balance = self.machine.get_prediction()
        layers = rDH.Layers_RBC(11)
        # Determine how much material is being placed with EC2
        missionPlace = [None, None, None, None, None]
        match load_balance.get('oEC2_Place'):
            case 100:
                # Condition if only one layer is being applied by EC2
                missionPlace[0] = self.get_sheets(self.panel.get_layer_position(0), station)
                missionPlace[0] = True
                self.build_rbc_progress.ec2_operations.append('Place and Fasten Layer 1')
            case 200:
                # Layer 1
                missionPlace[0] = self.get_sheets(self.panel.get_layer_position(0), station)
                missionPlace[0] = True
                # Layer 2
                missionPlace[1] = self.get_sheets(self.panel.get_layer_position(1), station)
                missionPlace[1] = True
                self.build_rbc_progress.ec2_operations.append('Place and Fasten Layer 1/2')
            case 123:
                for i in range(self.panel.get_layer_count()):
                    missionPlace[i] = self.get_sheets(self.panel.get_layer_position(i), station)
                    missionPlace[i] = True
                self.build_rbc_progress.ec2_operations.append('Place and Fasten All Layers')
            case default:
                self.build_rbc_progress.ec2_operations.append('No Place and Fasten on EC2')
                logging.info('no material is placed with EC2')

        # Determine if EC2 is fastening material that was loaded
        missionFasten = [None, None, None, None, None]
        match load_balance.get('oEC2_Fasten'):
            case 100:
                missionFasten[0] = self.get_fastener(self.panel.get_layer_position(0), station)
                self.build_rbc_progress.ec2_operations.append('Fasten Layer 1')
            case 200:
                missionFasten[0] = self.get_fastener(self.panel.get_layer_position(0), station)
                missionFasten[1] = self.get_fastener(self.panel.get_layer_position(1), station)
                self.build_rbc_progress.ec2_operations.append('Fasten Layer 1/2')
            case 123:
                for i in range(self.panel.get_layer_count()):
                    missionFasten[i] = self.get_fastener(self.panel.get_layer_position(i), station)
                self.build_rbc_progress.ec2_operations.append('Fasten All Layers')
            case default:
                self.build_rbc_progress.ec2_operations.append('No Fastening on EC2')
                logging.info('no material is fastened with EC2')

        # Determine if EC2 is Small Routing any material
        missionSmallRoute = [None, None, None, None, None]
        match load_balance.get('oEC2_SmallRouting'):
            case 100:
                missionSmallRoute[0] = self.get_end_cut(self.panel.get_layer_position(0), station)
                self.build_rbc_progress.ec2_operations.append('Route Layer 1')
            case 200:
                missionSmallRoute[1] = self.get_end_cut(self.panel.get_layer_position(1), station)
                self.build_rbc_progress.ec2_operations.append('Route Layer 1/2')
            case 123:
                for i in range(self.panel.get_layer_count()):
                    missionSmallRoute[i] = self.get_end_cut(self.panel.get_layer_position(i), station)
                self.build_rbc_progress.ec2_operations.append('Route All Layers')
            case default:
                self.build_rbc_progress.ec2_operations.append('No Routing on EC2')
                logging.info('no material is Routed with EC2')
        # Determine if EC2 is Door/Window Routing any material
        missionRoute = [None, None, None, None, None]
        missionRouting = []
        match load_balance.get('oEC2_Routing'):
            case 100:
                missionRouting.extend(self.get_rough_out_cut(self.panel.get_layer_position(0), station))
                missionRoute[0] = missionRouting
                self.build_rbc_progress.ec2_operations.append('Route Door/Window Layer 1')
            case 200:
                missionRouting.extend(self.get_rough_out_cut(self.panel.get_layer_position(1), station))
                missionRoute[1] = missionRouting
                self.build_rbc_progress.ec2_operations.append('Route Door/Window Layer 1/2')
            case 123:
                for i in range(self.panel.get_layer_count()):
                    missionRoute[i] = self.get_rough_out_cut(self.panel.get_layer_position(i), station)
                missionRoute[1] = missionRouting
                self.build_rbc_progress.ec2_operations.append('Door/Window Route All Layers')
            case default:
                self.build_rbc_progress.ec2_operations.append('No Door/Window Routing on EC2')
                logging.info('no material is Routed with EC2')

        # Combine Place, Fasten, and Route Data to Layer

        for i in range(self.panel.get_layer_count()):
            used = False
            layer = rDH.Layer_RBC(self.panel.get_layer_position(i))
            if missionPlace[i] is not None:
                layer = self.get_sheets(self.panel.get_layer_position(i), station)  # Determine if any boards have been placed for that layer
                used = True
            if missionFasten[i] is not None:
                layer.add_mission(missionFasten[i])  # Determine if any fasteners have been used for that layer
                used = True
            if missionSmallRoute[i] is not None:
                layer.add_mission(missionSmallRoute[i])  # Determine if any routing have been used for that layer
                used = True
            if missionRoute[i] is not None:
                layer.add_mission(missionRoute[i])  # Determine if any routing have been used for that layer
                used = True
            if used:
                layer.set_properties(round(self.panel.get_layer_position(i) * 25.4, 1))
                layers.add_layer(layer)

        # Returns a converted layers object to a json string
        return layers.to_json()

    def rd_ec3_main(self, station: Station):  # Main Call to assign what work will be allowed to complete on EC3
        # Prediction Keys ['oEC2_Place',	'oEC3_Place',	'oEC2_Fasten',	'oEC3_Fasten',	'oEC2_Routing',	'oEC3_Routing']
        load_balance = self.machine.get_prediction()
        layers_ec3 = rDH.Layers_RBC(station.station_id)
        # Determine how much material is being placed with EC2
        missionPlace = [None, None, None, None, None]
        match load_balance.get('oEC3_Place'):
            case 100:
                # Condition if only one layer is being applied by EC2
                missionPlace[0] = self.get_sheets(self.panel.get_layer_position(0), station)
                missionPlace[0] = True
                self.build_rbc_progress.ec3_operations.append('Place and Fasten Layer 1')
            case 200:
                # Layer 1
                missionPlace[1] = self.get_sheets(self.panel.get_layer_position(1), station)
                missionPlace[1] = True
                # Layer 2
                # missionPlace[1] = self.getSheets(self.panel.getLayerPosition(1), station)
                missionPlace[1] = True
                self.build_rbc_progress.ec3_operations.append('Place and Fasten Layer 2')
            case 123:
                for i in range(self.panel.get_layer_count()):
                    missionPlace[i] = self.get_sheets(self.panel.get_layer_position(i), station)
                    missionPlace[i] = True
                self.build_rbc_progress.ec3_operations.append('Place and Fasten All Layers')

            case default:
                self.build_rbc_progress.ec3_operations.append('No Place and Fasten on EC3')
                logging.info('no material is placed with EC3')

        # Determine if EC3 is fastening material that was loaded
        missionFasten = [None, None, None, None, None]
        match load_balance.get('oEC3_Fasten'):
            case 100:
                missionFasten[0] = self.get_fastener(self.panel.get_layer_position(0), station)
                self.build_rbc_progress.ec3_operations.append('Fasten Layer 1')
            case 200:
                # missionFasten[0] = self.getFastener(self.panel.getLayerPosition(0), 3)
                missionFasten[1] = self.get_fastener(self.panel.get_layer_position(1), station)
                self.build_rbc_progress.ec3_operations.append('Fasten Layer 2')
            case 123:
                for i in range(self.panel.get_layer_count()):
                    missionPlace[i] = self.get_fastener(self.panel.get_layer_position(i), station)
                self.build_rbc_progress.ec3_operations.append('Fasten All Layers')
            case default:
                self.build_rbc_progress.ec3_operations.append('No Fastening on EC3')
                logging.info('no material is fastened with EC3')

        # Determine if EC3 is Small Routing any material
        missionSmallRoute = [None, None, None, None, None]
        match load_balance.get('oEC3_SmallRouting'):
            case 100:
                missionSmallRoute[0] = self.get_end_cut(self.panel.get_layer_position(0), station)
                self.build_rbc_progress.ec3_operations.append('Route Layer 1')
            case 200:
                missionSmallRoute[1] = self.get_end_cut(self.panel.get_layer_position(1), station)
                self.build_rbc_progress.ec3_operations.append('Route Layer 1/2')
            case 123:
                for i in range(self.panel.get_layer_count()):
                    missionSmallRoute[i] = self.get_end_cut(self.panel.get_layer_position(i), station)
                self.build_rbc_progress.ec3_operations.append('Route All Layers')
            case default:
                self.build_rbc_progress.ec3_operations.append('No Routing on EC3')
                logging.info('no material is Routed with EC3')

        # Determine if EC3 is Routing any material
        missionRoute = [None, None, None, None, None]
        missionRouting = []
        match load_balance.get('oEC3_Routing'):
            case 100:
                missionRouting.extend(self.get_rough_out_cut(self.panel.get_layer_position(0), station))
                missionRoute[0] = missionRouting
                self.build_rbc_progress.ec3_operations.append('Route Layer 1')
            case 200:
                missionRouting.extend(self.get_rough_out_cut(self.panel.get_layer_position(1), station))
                missionRoute[1] = missionRouting
                self.build_rbc_progress.ec3_operations.append('Route Layer 2')
            case 123:
                missionRouting.extend(self.get_rough_out_cut(self.panel.get_layer_position(1), station))
                missionRoute[1] = missionRouting
                self.build_rbc_progress.ec3_operations.append('Route All Layers')
            case default:
                self.build_rbc_progress.ec3_operations.append('No Routing on EC3')
                logging.info('no material is Routed with EC3')

        # Combine Place, Fasten, and Route Data to Layer
        for i in range(self.panel.get_layer_count()):
            used = False
            layer = rDH.Layer_RBC(self.panel.get_layer_position(i))

            if missionPlace[i] is not None:
                layer = self.get_sheets(self.panel.get_layer_position(i), station)  # Determine if any boards have been placed for that layer
                used = True
            if missionFasten[i] is not None:
                layer.add_mission(missionFasten[i])  # Determine if any fasteners have been used for that layer
                used = True
            if missionSmallRoute[i] is not None:
                layer.add_mission(missionSmallRoute[i])  # Determine if any routing have been used for that layer
                used = True
            if missionRoute[i] is not None:
                layer.add_mission(missionRoute[i])  # Determine if any routing have been used for that layer
                used = True
            if used:
                layer.set_properties(round(self.panel.get_layer_position(i) * 25.4, 1))
                layers_ec3.add_layer(layer)

        # Returns a converted layers object to a json string
        return layers_ec3.to_json()

    # Get Sheet Information       
    def get_sheets(self, layer, working_station: Station) -> rDH.Layer_RBC:  # This function will load the sheets of Material to the
        # Open Database Connection
        pgDB = dBC.DB_Connect()
        pgDB.open()
        sql_var1 = self.panel.guid
        sql_var2 = layer
        sql_var3 = round(working_station.partial_board / 25.4, 0)

        # Adjusted the e1x position from having to be greater e1x >= 0 changed to using parameter of partial board
        sql_select_query = f"""
                        SELECT to_jsonb(panel)
                        from cad2fab.system_elements panel
                        where panelguid = '{sql_var1}' 
                        and "type" = 'Sheet' 
                        and b2y = '{sql_var2}'
                        and "actual_width" > {sql_var3} 
                        and e1x >= {sql_var3 - 48}
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
        layerData = rDH.Layer_RBC(layer)

        logging.info("results: " + str(results))
        self.storeCWSFound = 0
        for sheet in results:
            # change list to object
            sheet: dict = sheet[0]
            material = Material(sheet, self.machine.get_system_parms(working_station.station_id))
            # f.writelines('Sheets: '+str(sheet)+ '   Material: '+str(material))

            # Board Pick
            pick = rDH.missionData_RBC(400)
            if (sheet.get('e1x') == 0 or sheet.get('e1x') < 0) and sheet.get('actual_width') < 48:
                pick.Info_01 = round((sheet.get('e4x') - 48) * 25.4, 2)
            else:
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
            layer_index = self.panel.get_layer_index(layer)
            if len(self.build_rbc_progress.materials_required) == 0 or pick.Info_12 not in self.build_rbc_progress.materials_required[
                working_station.station_id - 2]:
                self.build_rbc_progress.materials_required[working_station.station_id - 2].append(pick.Info_12)
            self.build_rbc_progress.material_count[working_station.station_id - 2] += 1
            # Board Place
            place = rDH.missionData_RBC(material.getPlaceType())  # self.fastenTypes
            # place = rdh.missionData_RBC(material.placeNum) #self.fastenTypes

            if sheet.get('e1x') == 0 and sheet.get('actual_width') < 48:
                place.Info_01 = round((sheet.get('e4x') - 48) * 25.4, 2)  # Condition if
            elif sheet.get('e1x') < 0 and sheet.get('actual_width') < 48:
                place.Info_01 = round((sheet.get('e4x') - 48) * 25.4, 2)  # Condition if
            else:
                place.Info_01 = round(sheet.get('e1x') * 25.4, 2)  # e1x
            place.Info_02 = round(sheet.get('e1y') * 25.4, 2)  # e1y
            place.Info_03 = 0
            place.Info_04 = 0
            place.Info_05 = 29
            if (sheet.get('e1x') == 0 or sheet.get('e1x') < 0) and sheet.get('actual_width') < 48:
                place.Info_06 = round(0.75 * 25.4, 2)
            else:
                place.Info_06 = round((sheet.get('e1x') + 0.75) * 25.4, 2)
            if place.missionID == 401:
                place.Info_11 = 1
            else:
                place.Info_11 = 0
            place.Info_12 = 0

            # Fastening
            fasteners = self.get_board_fasten(pick, layer, material, sheet, working_station)
            # Pick and Place Locations are added to the list
            boardData = rDH.BoardData_RBC(board_pick=pick, board_place=place, board_fasten=fasteners)
            # Now we have to add the missions for temp fastening that board

            layerData.add_board(boardData)
            if sheet.get('elementguid') not in self.track_sheets:
                self.track_sheets.append(sheet.get('elementguid'))
        # this information will be used when building fastener requirements for layer
        layIndex = self.panel.get_layer_index(layer)
        fast = material.fastenNum

        self.panel.update_layer_fastener(layIndex, fast)

        return layerData

    def get_board_fasten(self, board: rDH.missionData_RBC, active_layer, i_material: Material, sheet, working_station: Station) -> list[
        rDH.missionData_RBC]:
        studSpace = 406
        shiftspace = round(28 / 25.4, 2)
        # Open Database Connection

        pgDB = dBC.DB_Connect()
        pgDB.open()
        sql_var1 = self.panel.guid  # Panel ID
        sql_wStart = round(board.Info_01 / 25.4, 2)  # Leading Edge of the Board (Width)
        sql_wEnd = round((board.Info_01 + board.Info_03) / 25.4, 2)  # Trailing Edge of the Board (Width)
        # Get parameters to determine min and max window to temp fasten material
        sql_vMin = 0  # machine.ec3.parmData.getParm('ZL Core', 'Y Min Vertical') /25.4
        sql_vMax = working_station.parmData.getParm('ZL Core', 'Y Middle Vertical') / 25.4
        sql_panelMax = self.panel.panelLength
        sql_panelMin = 1.5
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
                            and ((e1x > '{sql_panelMin}' and e4x < '{sql_panelMax}') or description like '%Plate%')
                            order by b3x  
                            """
        results = pgDB.query(sql_statement=sql_select_query)

        # Determine Start End Shift
        shiftSTART = [shiftspace, shiftspace + 0.25, shiftspace + 0.5]
        shiftEND = [shiftspace, shiftspace + 0.5, shiftspace + 0.5]
        offsetStart = shiftSTART[self.panel.get_layer_index(active_layer)]
        offsetEnd = shiftEND[self.panel.get_layer_index(active_layer)]
        # Remove any boards that are not atleast 3/4 inch under sheet
        result2 = check_edge_case(sheet, results)

        if len(results) != len(result2):
            print('Adjusted')
        results = result2
        # Process Boards Results
        fastenlst: list[rDH.missionData_RBC] = []
        for result in results:
            result: dict = result[0]
            fasten = rDH.missionData_RBC(i_material.getFastenType())
            # Vertical vs Horizontal Vertical dimension is less than 6inch
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
                studSpace = get_shot_designed_spacing(sheet, fasten.Info_01, 'Vertical', working_station, pgDB, result)
                fasten.Info_10 = get_shot_spacing(fasten.Info_02, fasten.Info_04, studSpace)
                if fasten.missionID == 110:  # Screw Tool Selection
                    fasten.Info_11, fasten.Info_10 = get_screw_index(studSpace)
                    if studSpace == 110 or studSpace == 220:
                        fasten.Info_10 = studSpace * 2
            # Horizontal
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
                studSpace = get_shot_designed_spacing(sheet, fasten.Info_02, 'Horizontal', working_station, pgDB, result)
                fasten.Info_10 = get_shot_spacing(fasten.Info_01, fasten.Info_03, studSpace)
                if fasten.missionID == 110:  # Screw Tool Selection
                    fasten.Info_11, fasten.Info_10 = get_screw_index(studSpace)
                    if studSpace == 110 or studSpace == 220:
                        fasten.Info_10 = studSpace * 2

                fasten = self.cross_ref_cut_out(self.panel.guid, fasten, pgDB)

            else:
                logging.warning('Did not add fastening for member' + self.panel.guid + '__' + result.get('elementguid'))

            if self.panel.get_layer_index(active_layer) == 0:
                fasten.Info_09 = self.get_cws(result, pgDB, self.storeCWSFound)
                if fasten.Info_09 > 0:
                    self.storeCWSFound = fasten.Info_09

            fastenlst.append(fasten)
        pgDB.close()
        layer_index = self.panel.get_layer_index(active_layer)
        if len(self.build_rbc_progress.fasteners_required) == 0 or i_material.fastener not in self.build_rbc_progress.fasteners_required[
            working_station.station_id - 2]:
            self.build_rbc_progress.fasteners_required[working_station.station_id - 2].append(i_material.fastener)
        return fastenlst

    def get_fastener(self, layer, working_station: Station) -> list[rDH.missionData_RBC]:
        studSpace = 406
        # Open Database Connection
        pgDB = dBC.DB_Connect()
        pgDB.open()
        sql_var1 = self.panel.guid  # Panel ID
        sql_var2 = tuple(self.track_sheets)

        sql_wStart = 0  # Leading Edge of the Board (Width)
        sql_wEnd = self.panel.panelLength  # Trailing Edge of the Board (Width)
        # Get parameters to determine min and max window to temp fasten material
        sql_vMin = round(working_station.parmData.getParm('ZL Core', 'Y Middle Vertical') / 25.4, 2)
        sql_vMax = round(working_station.parmData.getParm('ZL Core', 'Y Build Max') / 25.4, 2)
        sql_var3 = round(working_station.partial_board / 25.4, 0)

        sql_select_query = f"""
                            select to_jsonb(se) 
                            from cad2fab.system_elements se 
                            where panelguid = '{sql_var1}' 
                            and description = 'Sheathing' 
                            and b2y = '{layer}' 
                            and e1y < '{sql_vMin}' 
                            and e2y < '{sql_vMax}' 
                            and e1x <= '{sql_wEnd}' 
                            and e1x >= {sql_var3 - 48}
                            and e4x > '{sql_wStart}' 
                            and "actual_width" > '{sql_var3}'
                            and e1x >= 0
                            """
        #   and elementguid in '{sql_var2}'
        # Determine Start End Shift
        shiftSTART = [4, 3.5, 1.25]
        shiftEND = [0.75, 1.25, 1.25]

        offsetStart = shiftSTART[self.panel.get_layer_index(layer)]
        offsetEnd = shiftEND[self.panel.get_layer_index(layer)]
        resultSheath = pgDB.query(sql_statement=sql_select_query)  # Look at Sheaths for Edge Conditions
        fastenlst: list[rDH.missionData_RBC] = []
        last_sheet = ''
        for sheet in resultSheath:
            sheet: dict = sheet[0]
            last_sheet = sheet
            sql_wStart = sheet.get('e1x')
            sql_wEnd = sheet.get('e4x')
            sql_vMax = sheet.get('e2y')
            sql_panelMax = self.panel.panelLength
            sql_panelMin = 1.5
            sql_select_query = f"""
                                select to_jsonb(se) 
                                from cad2fab.system_elements se
                                where 
                                    panelguid = '{sql_var1}' 
                                    and description not in ('Nog', 'Sheathing','VeryTopPlate','Rough cutout','FillerBtmNailer','HeaderSill','Header', 'TopPlate') 
                                    and e2y <= '{sql_vMax}' and e2y >= '{sql_vMin}' 
                                    and e1x < '{sql_wEnd}' and e4x > '{sql_wStart}' 
                                    and b2y = 0 
                                    and ((e1x > '{sql_panelMin}' and e4x < '{sql_panelMax}') or description like '%Plate%')
                                    order by b3x 
                                """
            results = pgDB.query(sql_statement=sql_select_query)

            # Remove any boards that are not atleast 3/4 inch under sheet
            result2 = check_edge_case(sheet, results)

            if len(results) != len(result2):
                print('Adjusted')
            results = result2

            # Process Results
            for result in results:
                result: dict = result[0]
                fasten = rDH.missionData_RBC(self.panel.get_layer_fastener(self.panel.get_layer_index(layer)))
                # Vertical vs Horizontal Vertical dimension is less than 6inch
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
                    studSpace = get_shot_designed_spacing(sheet, fasten.Info_01, 'Vertical', working_station, pgDB, result)
                    fasten.Info_10 = get_shot_spacing(fasten.Info_02, fasten.Info_04, studSpace)
                    if fasten.missionID == 110:  # Screw Tool Selection
                        fasten.Info_11, fasten.Info_10 = get_screw_index(studSpace)
                        if studSpace == 110 or studSpace == 220:
                            fasten.Info_10 = studSpace * 2
                # Horizontal
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
                    studSpace = get_shot_designed_spacing(sheet, fasten.Info_02, 'Horizontal', working_station, pgDB, result)
                    fasten.Info_10 = get_shot_spacing(fasten.Info_01, fasten.Info_03, studSpace)
                    if fasten.missionID == 110:  # Screw Tool Selection
                        fasten.Info_11, fasten.Info_10 = get_screw_index(studSpace)
                        if studSpace == 110 or studSpace == 220:
                            fasten.Info_10 = studSpace * 2

                    fasten = self.cross_ref_cut_out(self.panel.guid, fasten, pgDB)
                else:
                    logging.warning(
                        'Did not add fastening for member' + self.panel.guid + '__' + result.get('elementguid'))
                #  Apply
                fastenlst.append(fasten)

        sql_select_query = f"""
                            select to_jsonb(se) 
                            from cad2fab.system_elements se
                            where 
                                panelguid = '{sql_var1}' 
                                and description = 'TopPlate'
                                order by b1x
                            """

        results = pgDB.query(sql_statement=sql_select_query)
        fasten = rDH.missionData_RBC(self.panel.get_layer_fastener(self.panel.get_layer_index(layer)))
        fasten.Info_02 = round((results[0][0].get('e1y') + 0.75) * 25.4, 2)  # Y Start Position
        fasten.Info_04 = round((results[0][0].get('e1y') + 0.75) * 25.4, 2)  # Y Start Position

        fasten.Info_01 = round((results[0][0].get('e1x') + offsetStart) * 25.4, 2)
        fasten.Info_03 = round((results[0][-1].get('e4x') - offsetEnd) * 25.4, 2)

        studSpace = get_shot_designed_spacing(last_sheet, fasten.Info_02, 'Horizontal', working_station, pgDB, results[0][0])
        fasten.Info_10 = get_shot_spacing(fasten.Info_01, fasten.Info_03, studSpace)
        if fasten.missionID == 110:  # Screw Tool Selection
            fasten.Info_11, fasten.Info_10 = get_screw_index(studSpace)
            if studSpace == 110 or studSpace == 220:
                fasten.Info_10 = studSpace * 2
        fastenlst.append(fasten)
        pgDB.close()
        return fastenlst

    def add_fasten_list(self, working_station, result, sheet, layer, pgDB):
        # Determine Start End Shift
        shiftSTART = [4, 3.5, 1.25]
        shiftEND = [0.75, 1.25, 1.25]

        offsetStart = shiftSTART[self.panel.get_layer_index(layer)]
        offsetEnd = shiftEND[self.panel.get_layer_index(layer)]
        sql_vMin = round(working_station.parmData.getParm('ZL Core', 'Y Middle Vertical') / 25.4, 2)
        sql_vMax = round(working_station.parmData.getParm('ZL Core', 'Y Build Max') / 25.4, 2)
        sql_var3 = round(working_station.partial_board / 25.4, 0)
        sql_wStart = sheet.get('e1x')
        sql_wEnd = sheet.get('e4x')
        sql_vMax = sheet.get('e2y')
        fasten = rDH.missionData_RBC(self.panel.get_layer_fastener(self.panel.get_layer_index(layer)))
        # Vertical vs Horizontal Vertical dimension is less than 6inch
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
                return None
            if result.get('e1y') < sql_vMin:
                fasten.Info_02 = round((sql_vMin + offsetStart) * 25.4, 2)  # Y Start Position
            else:
                fasten.Info_02 = round((result.get('e1y') + offsetStart) * 25.4, 2)  # Y Start Position
            if result.get('e2y') > sql_vMax:
                fasten.Info_04 = round((sql_vMax - offsetEnd) * 25.4, 2)  # Y End Position
            else:
                fasten.Info_04 = round((result.get('e2y') - offsetEnd) * 25.4, 2)  # Y End Position
            studSpace = get_shot_designed_spacing(sheet, fasten.Info_01, 'Vertical', working_station, pgDB, result)
            fasten.Info_10 = get_shot_spacing(fasten.Info_02, fasten.Info_04, studSpace)
            if fasten.missionID == 110:  # Screw Tool Selection
                fasten.Info_11, fasten.Info_10 = get_screw_index(studSpace)
                if studSpace == 110 or studSpace == 220:
                    fasten.Info_10 = studSpace * 2

        # Horizontal
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
            studSpace = get_shot_designed_spacing(sheet, fasten.Info_02, 'Horizontal', working_station, pgDB, result)
            fasten.Info_10 = get_shot_spacing(fasten.Info_01, fasten.Info_03, studSpace)
            if fasten.missionID == 110:  # Screw Tool Selection
                fasten.Info_11, fasten.Info_10 = get_screw_index(studSpace)
                if studSpace == 110 or studSpace == 220:
                    fasten.Info_10 = studSpace * 2

            fasten = self.cross_ref_cut_out(self.panel.guid, fasten, pgDB)
        else:
            logging.warning(
                'Did not add fastening for member' + self.panel.guid + '__' + result.get('elementguid'))

        return fasten

    def cross_ref_cut_out(self, panelID, mission: rDH.missionData_RBC, dbConnection: dBC.DB_Connect):
        sql_var1 = panelID
        sql_wStart = round(mission.Info_01 / 25.4, 2)
        sql_wEnd = round(mission.Info_03 / 25.4, 2)
        sql_vStart = round(mission.Info_02 / 25.4, 2)
        sql_vEnd = round(mission.Info_04 / 25.4, 2)

        sql_pre_query = f"""
            select to_jsonb(se) 
            from cad2fab.system_elements se
            where 
                panelguid = '{sql_var1}' 
                and description in ('Rough cutout') 
                and (e1x < {sql_wEnd} and e1x > {sql_wStart} and e4y  <= {sql_vStart} and e1y >= {sql_vStart})
            """
        sql_post_query = f"""
            select to_jsonb(se) 
            from cad2fab.system_elements se
            where 
                panelguid = '{sql_var1}' 
                and description in ('Rough cutout') 
                and (e3x > {sql_wStart} and e3x < {sql_wEnd} and e4y  <= {sql_vStart} and e1y >= {sql_vStart})
            """
        preResult = dbConnection.query(sql_statement=sql_pre_query)
        postResult = dbConnection.query(sql_statement=sql_post_query)
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

    def get_rough_out_cut(self, layer, working_station: Station):
        # Open Database Connection
        pgDB = dBC.DB_Connect()
        pgDB.open()
        sql_var1 = self.panel.guid
        sql_select_query = f"""
                        SELECT to_jsonb(panel)
                        from cad2fab.system_elements panel
                        where panelguid = '{sql_var1}' AND description = 'Rough cutout' 
                        order by b1x;
                        """

        results = pgDB.query(sql_statement=sql_select_query)
        pgDB.close()
        route_list: list[rDH.missionData_RBC] = []

        for result in results:
            result: dict = result[0]
            cutBottomTop = False
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
                route = rDH.missionData_RBC(200)
                route.Info_01 = p1['x']
                route.Info_02 = p1['y']
                if route.Info_02 <= 38:
                    route.Info_02 = 38
                route.Info_03 = round(p2['x'] - p1['x'], 2)
                route.Info_04 = round(p2['y'] - p1['y'], 2)
                route.Info_05 = 1
                if self.panel.get_layer_index(layer) == 0:
                    route.Info_07 = round(layer * 25.4, 1)
                else:
                    route.Info_07 = round((layer - self.panel.get_layer_position(0)) * 25.4, 1)
                route_list.append(route)
            else:
                logging.warning('Did not add Route for member' + self.panel.guid + '__' + result.get('elementguid'))
                break

        return route_list

    def get_end_cut(self, layer, working_station: Station) -> list:
        # Open Database Connection
        pgDB = dBC.DB_Connect()
        pgDB.open()
        sql_var1 = self.panel.guid
        sql_var2 = tuple(self.track_sheets)
        sql_var3 = round(working_station.off_cut / 25.4, 2)
        sql_var4 = layer
        sql_select_query = f"""
                        SELECT to_jsonb(panel)
                        from cad2fab.system_elements panel
                        where panelguid = '{sql_var1}' 
                        AND elementguid in {sql_var2}
                        AND b2y = {sql_var4}
                        AND "type" = 'Sheet' 
                        AND actual_width between {sql_var3} and 48
                        order by b1x;
                        """

        results = pgDB.query(sql_statement=sql_select_query)
        pgDB.close()
        route_list: list[rDH.missionData_RBC] = []
        if results is not None:
            if len(results) > 0:
                for result in results:
                    result: dict = result[0]

                    route = rDH.missionData_RBC(160)
                    # R1 Cut
                    if (result.get('e1x') == 0 or result.get('e1x') < 0) and result.get('actual_width') < 48:
                        # Cut Material off that is in negative panel space
                        route.Info_01 = round((result.get('e1x')) * 25.4, 2)
                        route.Info_02 = 0
                        route.Info_03 = round((result.get('actual_width') - 48) * 25.4, 2)
                        route.Info_04 = round((result.get('e3y')) * 25.4, 2)
                        route.Info_05 = 1
                        if self.panel.get_layer_index(layer) == 0:
                            route.Info_07 = round(layer * 25.4, 1)
                        else:
                            route.Info_07 = round((layer - self.panel.get_layer_position(0)) * 25.4, 1)

                    elif round(result.get('e4x'), 1) >= round(self.panel.panelLength, 1) and result.get('actual_width') < 48:
                        # Cut Material off that is in positive panel space
                        route.Info_01 = round((result.get('e4x')) * 25.4, 2)
                        route.Info_02 = 0
                        route.Info_03 = round((48 - result.get('actual_width')) * 25.4, 2)
                        route.Info_04 = round((result.get('e3y')) * 25.4, 2)
                        route.Info_05 = 1
                        if self.panel.get_layer_index(layer) == 0:
                            route.Info_07 = round(layer * 25.4, 1)
                        else:
                            route.Info_07 = round((layer - self.panel.get_layer_position(0)) * 25.4, 1)
                    else:
                        logging.warning(
                            'Did not add Route for member' + self.panel.guid + '__' + result.get('elementguid'))
                    if hasattr(route, 'Info_01'):
                        route_list.append(route)

        return route_list

    def get_cws(self, element: dict, ipg_db: dBC, max_previous):
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

            results_Pre = ipg_db.query(sql_statement=sql_select_query1)
            results_Post = ipg_db.query(sql_statement=sql_select_query2)
            if len(results_Pre) == 0 and len(results_Post) == 0 and element.get('e1x') > (
                    round(max_previous / 25.4, 2) + 1):
                leadEdge = element.get('e1x')
                trailEdge = element.get('e3x')
                cwsPos = round((leadEdge + (trailEdge - leadEdge) / 2) * 25.4, 2)

        return cwsPos


def check_edge_case(sheet, board_list) -> list:
    for result in board_list[:]:
        dict_result: dict = result[0]
        sheet_start = round(sheet.get('e1x'), 2)
        sheet_end = round((sheet.get('e1x') + sheet.get('e4x')), 2)
        board_start = dict_result.get('e1x')
        board_end = dict_result.get('e4x')
        if (board_start + 0.74) < sheet_start and abs(board_end - sheet_start) < 0.75:
            board_list.remove(result)
            print('sheet lead removed' + str(dict_result.get('e1x')))
        if (board_start + 0.74) > sheet_end and abs(board_start - sheet_end) < 0.75:
            board_list.remove(result)
            print('sheet end removed' + str(dict_result.get('e1x')))
    return board_list


def get_shot_designed_spacing(element: dict, pos, direction, station: Station, connect: dBC.DB_Connect, stud_element) -> float:
    # Determine if sheet has defined stud spacing
    stud_space = 304
    sql_var1 = element.get('elementguid')
    sql_determine = f"""
    select edge_spacing, field_spacing
    from cad2fab.system_fasteners
    where elementguid = '{sql_var1}'
    and edge_spacing > 0
    and field_spacing > 0
    """
    results = connect.query(sql_determine)
    if len(results) > 0:
        edge = round(float(results[0][0]) * 25.4, 2)
        field = round(float(results[0][1]) * 25.4, 2)
    else:
        parms = station.parmData
        matParms = parms._parmList.get('Material')
        nested_matParms = {}
        for key, value in matParms.items():
            key_text = key.rsplit(' ', 2)
            nested_matParms.setdefault(key_text[0], {})[key_text[1]] = value
        sheetType = element.get('materialdesc')
        for matType in nested_matParms:
            if matType.upper() in sheetType.upper():
                edge = int(nested_matParms[matType]['Edge']['value'])
                field = int(nested_matParms[matType]['Field']['value'])
                break
    sql_var2 = 0.75
    sql_var3 = round(pos / 25.4, 2)
    if direction == 'Vertical':
        sql_find = f"""
                    select * 
                    from cad2fab.system_elements
                    where panelguid = '{element.get('panelguid')}'
                    and (description = 'Rough cutout' or description = 'Sheathing') 
                    and (ABS(e1x - {sql_var3}) <= {sql_var2}
                    or ABS(e2x - {sql_var3}) <= {sql_var2}
                    or ABS(e3x - {sql_var3}) <= {sql_var2}
                    or ABS(e4x - {sql_var3}) <= {sql_var2})
        """
    else:
        sql_find = f"""
                    select * 
                    from cad2fab.system_elements
                    where panelguid = '{element.get('panelguid')}' 
                    and (description = 'Rough cutout' or description = 'Sheathing') 
                    and (ABS(e1y - {sql_var3}) <= {sql_var2}
                    or ABS(e2y - {sql_var3}) <= {sql_var2}
                    or ABS(e3y - {sql_var3}) <= {sql_var2}
                    or ABS(e4y - {sql_var3}) <= {sql_var2})
        """

    results = connect.query(sql_find)
    if len(results) > 0 or stud_element.get("description") == 'TopPlate' or stud_element.get("description") == 'BottomPlate':
        stud_space = edge
    elif results is None:
        errr = True
    else:
        stud_space = field

    return stud_space


index_edge = 0
index_field = 0
index_single = 1


def get_screw_index(spacing):
    global index_edge
    global index_field
    global index_single
    index_select = 1
    choice = {
        '110': [3, 12, 6],
        '220': [5, 10]}
    if spacing == 110:
        index_select = choice['110'][index_edge]
        index_edge += 1
        if index_edge == 2:
            index_edge = 0
    elif spacing == 220:
        index_select = choice['220'][index_field]
        index_field += 1
        if index_field == 2:
            index_field = 0
    else:
        if index_single >= 8:
            index_single = 1
            index_select = index_single
        else:
            index_single = index_single << 1
            index_select = index_single

    return index_select, spacing


def get_shot_spacing(start, end, design_spacing):
    motion_length = end - start
    fastenCount = round(motion_length / design_spacing)
    if fastenCount == 0:
        fastenCount = 1
    result_spacing = math.floor(motion_length / fastenCount) - 1
    if result_spacing < 75:
        result_spacing = design_spacing
    return result_spacing


def check_fasten_mission(fasten: rDH.missionData_RBC) -> rDH.missionData_RBC:
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
