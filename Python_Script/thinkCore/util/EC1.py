import math

import util.dataBaseConnect as dbc
from util.framingCheck import Clear
from util.globals import Build_EC1_Progress
from util.machineData import Line
from util.panelData import Panel


class Mtrl_Data:
    material_data = ()

    def __init__(self, panel_data: Panel):
        # Assigns Panel Instance to Mtrl
        self.build_progress = None
        self.panel = panel_data
        status = 'Started'
        self.build_progress = Build_EC1_Progress()

        # self.mdMain()

    # Main Call for determining Material List
    def md_main(self):
        # Open Connection to the database
        self.build_progress.sf3_status = "In-Progress"
        pgDB = dbc.DB_Connect()
        pgDB.open()
        sql_var = self.panel.guid
        sql_select_query = f"""SELECT DISTINCT ON ("size") "type", description, "size", actual_thickness, actual_width, species
                    FROM cad2fab.system_elements
                    WHERE panelguid = '{sql_var}' AND description = 'Stud' AND type = 'Board'
                    ORDER BY "size" ASC;
                """

        results = pgDB.query(sql_select_query)

        sql_select_query = f"""SELECT count(description) 
                    FROM cad2fab.system_elements
                    WHERE panelguid = '{sql_var}' AND description = 'Stud' AND type = 'Board';
        """
        result_count = pgDB.query(sql_select_query)
        pgDB.close()

        if len(results) == 1:
            self.material_data = self.md_build(results[0], result_count[0])
        else:
            pass
            # print("returned to many options")

        self.md_insert()
        self.build_progress.sf3_status = "Complete"

    def md_build(self, studs, count):  # This function will assemble the entry line of Material Data
        uiItemLength = round(self.panel.studHeight * 25.4, 0)
        uiItemHeight = round(float(studs[3]) * 25.4, 0)  # convert from inches to mm
        uiItemThickness = round(float(studs[4]) * 25.4, 0)  # convert from inches to mm
        sMtrlCode = studs[5]
        uiOpCode = 0
        sprinterWrite = ' '
        sType = ' '
        uiItemID = 0
        sCADPath = ' '
        sProjectName = ' '
        sItemName = self.panel.guid

        line = (count, uiItemLength, uiItemHeight, uiItemThickness, sMtrlCode, uiOpCode, sprinterWrite, sType, uiItemID,
                sCADPath, sProjectName, sItemName)
        return line

    def md_insert(self):  # Inserts "material_data" list into table "materialData"
        pgDB = dbc.DB_Connect()
        pgDB.open()
        # send OpData to JobData table
        sql_JobData_query = '''
        INSERT INTO cad2fab.sf3_jobdata 
        (numofstuds, uiitemlength, uiitemheight, uiitemthickness, smtrlcode, uiopcode, sprinterwrite, stype, uiitemid, scadpath, sprojectname, sitemname)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (sitemname)
        DO UPDATE SET numofstuds = EXCLUDED.numofstuds,
        uiitemlength = EXCLUDED.uiitemlength, uiitemheight = EXCLUDED.uiitemheight,
        uiitemthickness = EXCLUDED.uiitemthickness,smtrlcode = EXCLUDED.smtrlcode,
        uiopcode = EXCLUDED.uiopcode,sprinterwrite = EXCLUDED.sprinterwrite,
        stype = EXCLUDED.stype,uiitemid = EXCLUDED.uiitemid,
        scadpath = EXCLUDED.scadpath,sprojectname = EXCLUDED.sprojectname;
        '''
        # make a list of tuples for query many
        jd_query_data = [self.material_data]

        pgDB.query_many(sql_JobData_query, jd_query_data)
        pgDB.close()


class JobData:
    job_data = []
    line_data = {
        "xPos": 0,
        "opText": " ",
        "opCode_FS": 0,
        "zPos_FS": 0,
        "yPos_FS": 0,
        "ssUpPosition_FS": 0,
        "opCode_MS": 0,
        "zPos_MS": 0,
        "yPos_MS": 0,
        "ssUpPosition_MS": 0,
        "imgName": " ",
        "objID": 0
    }

    def __init__(self, panel: Panel, machine: Line):
        self.machine = machine
        self.build_progress = Build_EC1_Progress()
        # Getting Panel Information for Nailing calculations in nailSubElements Function
        pgDB = dbc.DB_Connect()
        pgDB.open()

        sql_select_query = f"""
                        SELECT thickness, studheight, walllength, category
                        FROM cad2fab.system_panels
                        WHERE panelguid = '{panel.guid}';
                        """
        #
        results = pgDB.query(sql_select_query)
        # dbc.#printResult(results)
        # assign results of query to variables
        self.job = panel.job
        self.panelguid = panel.guid
        self.panelThickness = float(results[0][0])
        self.studHeight = (float(results[0][1])) * 25.4
        self.panelLength = float(results[0][2])
        self.category = results[0][3]
        # End of Panel Information

        # Getting Stud Stop and Hammer Unit dimensions that framingCheck.py uses
        # get parameters for stud stop and hammer that are universal
        sql_select_query = """
                            SELECT description, value
                            FROM public.parameters
                            WHERE description IN (  'Stud Stop thickness', 
                                                    'Stud Stop width', 
                                                    'Hammer Units Thickness', 
                                                    'Hammer Units Length', 
                                                    'Hammer Units Stroke',
                                                    'Positions:lrHammerUnitYCenterPosition'
                                                    );
                            """

        results = pgDB.query(sql_select_query)
        # assign results of query to variables
        # thickness is in the X direction of elevation, width/length in the Y direction
        self.ss_thickness = float(results[0][1])
        self.ss_width = float(results[1][1])
        self.hu_thickness = float(results[2][1])
        self.hu_length = float(results[3][1])
        self.hu_stroke = float(results[4][1])
        self.hu_Y = float(results[5][1])
        pgDB.close()
        # End of Framing Check

    def jd_main(self):  # Job Data Main
        self.build_progress.fm3_status = 'In-Progress'
        pgDB = dbc.DB_Connect()
        pgDB.open()
        panelguid = self.panelguid
        # query relevant data from elements table
        sql_elemData_query = f'''
        SELECT elementguid, type, description, size, b1x,b1y,b2x,b2y,b3x,b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,assembly_id
        FROM cad2fab.system_elements
        WHERE panelguid = '{panelguid}'
        ORDER BY b1x ASC;
        '''
        elemData = pgDB.query(sql_elemData_query)
        # counter for obj_id
        obj_count = 1
        # list of Op Datas
        OpData = []
        # list of placed sub assemblies
        placedSubAssembly = []
        # loop through all elements in the panel
        for i, elem in enumerate(elemData):
            # convert to mm and:
            # list of [panelguid,elementguid,type,description,size,b1x,b1y,b2x,b2y,b3x,
            #                       b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,assembly_id,count]
            if elem[4] is not None:
                element = [panelguid, elem[0], elem[1], elem[2], elem[3], float(elem[4]) * 25.4, float(elem[5]) * 25.4,
                           float(elem[6]) * 25.4, float(elem[7]) * 25.4, float(elem[8]) * 25.4, float(elem[9]) * 25.4,
                           float(elem[10]) * 25.4, float(elem[11]) * 25.4, float(elem[12]) * 25.4,
                           float(elem[13]) * 25.4,
                           float(elem[14]) * 25.4, float(elem[15]) * 25.4, float(elem[16]) * 25.4,
                           float(elem[17]) * 25.4,
                           float(elem[18]) * 25.4, float(elem[19]) * 25.4, elem[-1], obj_count]

            # if the element isn't a sheet, top plate, bottom plate, very top plate or Nog
            if elem[1] != 'Sheet' and elem[2] != 'BottomPlate' and elem[2] != 'TopPlate' and elem[2] != 'VeryTopPlate' and elem[2] != 'Nog':
                # if the element is a normal stud
                if elem[1] != 'Sub-Assembly Board' and elem[1] != 'Sub Assembly' and elem[1] != 'Sub-Assembly Cutout' and elem[1] != 'Hole':
                    # get opData for placing the element
                    tmp = self.place_element(element, pgDB)
                    # Add to OpDatas and increase the count
                    OpData.append(tmp[0])
                    # Add get OpDatas for nailing
                    tmp = self.nail_element(element, pgDB)
                    # loop through the Op Datas from the function and append to the list
                    # exclude the last list item because that is the counter
                    for var in tmp[:-1]:
                        OpData.append(var)
                    # update counter
                    obj_count = tmp[-1]
                    self.build_progress.auto_stud_count += 1
                # if the element isn't in a placed sub assembly and is a sub assembly board or cutout
                elif elem[-1] not in placedSubAssembly and (
                        elem[1] == 'Sub-Assembly Board' or elem[1] == 'Sub-Assembly Cutout'):
                    self.build_progress.sub_assembly_count += 1
                    # get relevant data of elements that aren't sub assembly cutouts, sort by b1x ascending
                    sql_sub_elem_query = f'''
                    SELECT elementguid, type, description, size, b1x,b1y,b2x,b2y,b3x,b3y,b4x,b4y,
                    e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,assembly_id
                    FROM cad2fab.system_elements
                    WHERE panelguid = '{panelguid}' and assembly_id = '{elem[-1]}' and type != 'Sub-Assembly Cutout'
                    ORDER BY b1x ASC;
                    '''
                    sub_elem_data = pgDB.query(sql_sub_elem_query)
                    # list of all sub elements and the sub assembly element, excluding rough cutouts(they don't need to be nailed)
                    subElemList = []
                    # loop through all the sub elements
                    for sub_elem in sub_elem_data:
                        # if the sub elem has coordinates (isn't the sub assembly element)
                        if sub_elem[4] is not None:
                            sub_element = [panelguid, sub_elem[0], sub_elem[1], sub_elem[2], sub_elem[3],
                                           round(float(sub_elem[4]) * 25.4, 1), round(float(sub_elem[5]) * 25.4, 1),
                                           round(float(sub_elem[6]) * 25.4, 1), round(float(sub_elem[7]) * 25.4, 1),
                                           round(float(sub_elem[8]) * 25.4, 1),
                                           round(float(sub_elem[9]) * 25.4, 1), round(float(sub_elem[10]) * 25.4, 1),
                                           round(float(sub_elem[11]) * 25.4, 1),
                                           round(float(sub_elem[12]) * 25.4, 1), round(float(sub_elem[13]) * 25.4, 1),
                                           round(float(sub_elem[14]) * 25.4, 1),
                                           round(float(sub_elem[15]) * 25.4, 1), round(float(sub_elem[16]) * 25.4, 1),
                                           round(float(sub_elem[17]) * 25.4, 1),
                                           round(float(sub_elem[18]) * 25.4, 1), round(float(sub_elem[19]) * 25.4, 1),
                                           sub_elem[-1], obj_count]
                        else:  # if the sub elem is the subassembly element (always the last in the list due to sort by b1x)
                            sub_element = [panelguid, sub_elem[0], sub_elem[1], sub_elem[2], sub_elem[3], sub_elem[4],
                                           sub_elem[5],
                                           sub_elem[6], sub_elem[7], sub_elem[8], sub_elem[9],
                                           sub_elem[10], sub_elem[11], sub_elem[12], sub_elem[13],
                                           sub_elem[14], sub_elem[15], sub_elem[16], sub_elem[17],
                                           sub_elem[18], sub_elem[19], sub_elem[-1], obj_count]
                        # add the item to the list
                        subElemList.append(sub_element)
                    # place the sub assembly send(sub assembly element, first board in the sub assembly for b1x position)
                    tmp = self.place_element(subElemList[-1], pgDB, element)
                    # add to op data and update counter
                    OpData.append(tmp[0])
                    obj_count = tmp[1]
                    # update the counter for all items in the sub elem list
                    for var in subElemList[:-1]:
                        var[-1] = obj_count
                    # get the nailing data, add it to the op data list and update the counter
                    tmp = self.nail_sub_element(subElemList, pgDB)
                    for var in tmp[:-1]:
                        OpData.append(var)
                    obj_count = tmp[-1]
                    # add the assembly id to the list of placed sub assemblies
                    placedSubAssembly.append(elem[-1])
                elif elem[1] == 'Hole':
                    # pass
                    tmp = self.hole_feature(element)
                    for op in reversed(OpData):
                        if op[0] > tmp[0][0]:
                            continue
                        else:
                            indexOp = OpData.index(op)
                            OpData.insert(indexOp + 1, tmp[0])
                            for i in range(op[-1] - 1, len(OpData)):
                                OpData[i][-1] = i + 1
                            break
                    obj_count = i + 2
        # send OpData to JobData table
        sql_JobData_query = '''
        INSERT INTO cad2fab.fm3_jobdata(panelguid, xpos, optext, opcode_fs, zpos_fs, ypos_fs, ssuppos_fs, 
        opcode_ms, zpos_ms, ypos_ms, ssuppos_ms, imgname, obj_id, loaddate)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
        ON CONFLICT (panelguid,obj_id)
        DO UPDATE SET xpos = EXCLUDED.xpos,
        optext = EXCLUDED.optext, opcode_fs = EXCLUDED.opcode_fs,
        zpos_fs = EXCLUDED.zpos_fs,ypos_fs = EXCLUDED.ypos_fs,
        ssuppos_fs = EXCLUDED.ssuppos_fs,opcode_ms = EXCLUDED.opcode_ms,
        zpos_ms = EXCLUDED.zpos_ms,ypos_ms = EXCLUDED.ypos_ms,
        ssuppos_ms = EXCLUDED.ssuppos_ms,imgname = EXCLUDED.imgname,
        obj_id = EXCLUDED.obj_id,loaddate = NOW();
        '''
        # make a list of tuples for query many
        jdQueryData = []
        for item in OpData:
            jdQueryData.append((panelguid, math.floor(item[0]), item[1], item[2], item[3], item[4],
                                item[5], item[6], item[7], item[8], item[9], item[10], item[11]))

        updated_jdQueryData = re_order_list(jdQueryData)

        pgDB.query_many(sql_JobData_query, updated_jdQueryData)
        # close the DB connection
        pgDB.close()
        self.build_progress.fm3_status = "Complete"

    def place_element(self, element, pg_db, sub_element=None):
        # call function with (self,element, subassembly board if applicable)
        path = ''
        # list of [panelguid,elementguid,type,description,size,b1x,b1y,b2x,b2y,b3x,
        #                       b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,assembly_id,count]
        clear = Clear(pg_db)
        # list of bools for FS & MS containing [StudStop,Hammer,Multi-Device,Option,Autostud,Operator Confirm, Nailing, Insulation, Drill]
        OpFS = [False, False, False, False, False, False, False, False, False]
        OpMS = [False, False, False, False, False, False, False, False, False]
        # empty list for [Xpos,OpText,OpCodeFS,ZposFS,YposFS,SSupPosFS,OpCodeMS,ZposMS,YposMS,SSupPosMS,IMG_NAME,OBJ_ID]
        OpJob = []
        ##
        # Flat Stud
        if element[2] == 'Board' and element[3] == 'FlatStud':
            # ----Operator needs to load Flatstud and stud stop needs to go up----
            OpFS[0] = True
            OpMS[0] = True
            OpFS[5] = True
            OpMS[5] = True
            # generate OpText and OpCodes from list of bools
            tmpFS = gen_op_code(OpFS)
            tmpMS = gen_op_code(OpMS)
            # list to append to OpJob & append it
            OpJobAppend = [element[5], tmpFS[0], tmpFS[1], 0, 0, 0, tmpMS[1], 0, 0, 0, '', element[-1]]
            OpJob.extend(OpJobAppend)
            # increase OBJ_ID Count for studs or subassemblies
            if sub_element is None:
                element[-1] += 1
            else:
                element[-1] = sub_element[-1] + 1
        # Normal vertical stud orientation
        else:
            # if placing a standard board
            if sub_element is None:
                # add X Pos from element
                OpJob.append(element[5])
            # if placing a subassembly
            else:
                # add X pos from sub assembly board
                OpJob.append(float(sub_element[5]))

            # check if the stud stops are clear for standard elements
            if sub_element is None:
                if clear.studStopFS(element):
                    OpFS[0] = True

                if clear.studStopMS(element[1]):
                    OpMS[0] = True
            # check if the stud stops are clear for sub assemblies
            else:
                if clear.studStopFS(sub_element):
                    OpFS[0] = True

                if clear.studStopMS(sub_element[1]):
                    OpMS[0] = True
            # if element is a stud enable hammer and autostud
            if element[2] == 'Board' and element[3] == 'Stud':
                OpFS[1] = True
                OpFS[4] = True
                OpMS[1] = True
                OpMS[4] = True
                # if element is the first stud enable operator confirm
                if element[5] <= 25.4:
                    OpFS[5] = True
                    OpMS[5] = True
            # if element is a sub assembly
            elif element[2] == 'Sub Assembly' or element[2] == 'Sub-Assembly Board':
                # set operator confirm
                OpFS[5] = True
                OpMS[5] = True
                job_id = self.job
                panel_id = element[0]
                image_name = str(element[3])
                dir_path = r"C:\Program Files\Inductive Automation\Ignition\webserver\webapps\main\Files"
                rel_path = r"%s" % image_name
                path = rel_path
            # other element types -> error
            else:
                if clear.hammerFS(element[1]):
                    OpFS[1] = True
                if clear.hammerMS(element[1]):
                    OpMS[1] = True
                # print(f'error with elementguid: {element[1]} \n Type unknown')

            # generate OpText and OpCodes from list of bools
            tmpFS = gen_op_code(OpFS)
            tmpMS = gen_op_code(OpMS)
            # list to append to OpJob & append it
            OpJobAppend = [tmpFS[0], tmpFS[1], 0, 0, 0, tmpMS[1], 0, 0, 0, path, element[-1]]
            OpJob.extend(OpJobAppend)
            # increase OBJ_ID Count for studs or subassemblies
            if sub_element is None:
                element[-1] += 1
            else:
                element[-1] = sub_element[-1] + 1
            # Return OpJob and updated count

        return OpJob, element[-1]

    def nail_element(self, element, pg_db):
        # element is a list consisting of [panelguid,elementguid,type,description,size,b1x,b1y,b2x,b2y,b3x,b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,count]
        # Used for calling StudStop or Hammer Unit Functions
        clear = Clear(pg_db)
        # Obj_ID
        count = element[-1]
        # List used as output of nailElement Function
        OpElement = []
        # Z positions for Nailing
        nailCount_2x4 = self.get_nail_count('2x4', 'FS')[0]
        nailCount_2x6 = self.get_nail_count('2x6', 'FS')[0]
        z_pos_2x4 = self.get_nail_count('2x4', 'FS')[1]
        z_pos_2x6 = self.get_nail_count('2x6', 'FS')[1]
        # list of bools for FS & MS containing [StudStop,Hammer,Multi-Device,Option,Autostud,Operator Confirm, Nailing, Insulation, Drill]
        OpFS = [False, False, False, False, False, False, False, False, False]
        OpMS = [False, False, False, False, False, False, False, False, False]
        if element[4] == "2X4":
            self.build_progress.auto_stud_type = '2X4'
            ct = 0
            while ct < nailCount_2x4:
                OpJob = [element[5]]
                # X_pos
                # check if the stud stops are clear
                if clear.studStopFS(element):
                    OpFS[0] = True

                if clear.studStopMS(element[1]):
                    OpMS[0] = True

                # if element is a stud enable hammer, autostud, and nailing
                if element[2] == 'Board' and (element[3] == 'Stud' or element[3] == 'CriticalStud'):
                    OpFS[1] = True
                    OpFS[4] = True
                    OpFS[6] = True
                    OpMS[1] = True
                    OpMS[4] = True
                    OpMS[6] = True
                #  Flat Stud Operations
                elif element[2] == 'Board' and element[3] == 'FlatStud':
                    x_pos_2x4 = z_pos_2x4
                    # Always Nail
                    OpFS[6] = True
                    OpMS[6] = True
                    z_pos_2x4 = [z_pos_2x4[0] for _ in z_pos_2x4]
                    if ct == 0:
                        OpJob = [element[5]]
                        # check if the stud stops are clear
                        if clear.studStopFS(element):
                            OpFS[0] = True

                        if clear.studStopMS(element[1]):
                            OpMS[0] = True

                        OpFS[1] = True
                        OpMS[1] = True
                        OpFS[5] = False
                        OpMS[5] = False

                        # No Stud Stop or Hammer required after first Nail
                    if ct > 1:
                        OpJob = [element[5] + x_pos_2x4[ct]]
                        OpFS[0] = False
                        OpFS[1] = False
                        OpMS[0] = False
                        OpMS[1] = False
                # other element types? -> error?
                else:
                    if clear.hammerFS(element[1]):
                        OpFS[1] = True
                    if clear.hammerMS(element[1]):
                        OpMS[1] = True
                    # print(f'error with elementguid: {element[1]} \n Type unknown')

                # generate OpText and OpCodes from list of bools
                tmpFS = gen_op_code(OpFS)
                tmpMS = gen_op_code(OpMS)
                # list to append to OpJob & append it
                OpJobAppend = [tmpFS[0], tmpFS[1], z_pos_2x4[ct], 0, 0, tmpMS[1], z_pos_2x4[ct], 0, 0, '', count]

                OpJob.extend(OpJobAppend)
                # increase Nail position counter and OBJ_ID Counter
                ct += 1
                count += 1
                OpElement.append(OpJob)

        elif element[4] == "2X6":
            self.build_progress.auto_stud_type = '2X6'
            ct = 0
            while ct < nailCount_2x6:
                OpJob = [element[5]]
                # Xpos
                # check if the stud stops are clear
                if clear.studStopFS(element):
                    OpFS[0] = True

                if clear.studStopMS(element[1]):
                    OpMS[0] = True

                # if element is a stud enable hammer, autostud and nailing
                if element[2] == 'Board' and (element[3] == 'Stud' or element[3] == 'CriticalStud'):
                    OpFS[1] = True
                    OpFS[4] = True
                    OpFS[6] = True
                    OpMS[1] = True
                    OpMS[4] = True
                    OpMS[6] = True
                #  Flat Stud Operations
                elif element[2] == 'Board' and element[3] == 'FlatStud':
                    x_pos_2x6 = z_pos_2x6
                    # Always Nail
                    OpFS[6] = True
                    OpMS[6] = True
                    z_pos_2x6 = [z_pos_2x6[0] for _ in z_pos_2x6]
                    if ct == 0:
                        OpJob = [element[5]]
                        # check if the stud stops are clear
                        if clear.studStopFS(element):
                            OpFS[0] = True

                        if clear.studStopMS(element[1]):
                            OpMS[0] = True

                        OpFS[1] = True
                        OpMS[1] = True
                        OpFS[5] = False
                        OpMS[5] = False

                    # No Stud Stop or Hammer required after first Nail
                    if ct > 1:
                        OpJob = [element[5] + x_pos_2x6[ct]]
                        OpFS[0] = False
                        OpFS[1] = False
                        OpMS[0] = False
                        OpMS[1] = False
                    # other element types? -> error?
                else:
                    if clear.hammerFS(element[1]):
                        OpFS[1] = True
                    if clear.hammerMS(element[1]):
                        OpMS[1] = True
                    # print(f'error with elementguid: {element[1]} \n Type unknown')

                # generate OpText and OpCodes from list of bools
                tmpFS = gen_op_code(OpFS)
                tmpMS = gen_op_code(OpMS)
                # list to append to OpJob & append it
                OpJobAppend = [tmpFS[0], tmpFS[1], z_pos_2x6[ct], 0, 0, tmpMS[1], z_pos_2x6[ct], 0, 0, '', count]
                OpJob.extend(OpJobAppend)
                # increase Nail position counter and OBJ_ID Counter
                ct += 1
                count += 1
                OpElement.append(OpJob)
        OpElement.append(count)
        # Return OpJob and updated count
        return OpElement

    def nail_sub_element(self, element_list, pg_db):
        # Used for calling StudStop or Hammer Unit Functions
        clear = Clear(pg_db)
        # Top and Bottom Plate variables used to check if Sub-Assembly element is touching
        TopPlate = round(38.1 + self.studHeight, 1)
        BottomPlate = 38.1
        # Z positions for Nailing
        nailCount_2x4 = self.get_nail_count('2x4', 'FS')[0]
        nailCount_2x6 = self.get_nail_count('2x6', 'FS')[0]
        Zpos_2x4 = self.get_nail_count('2x4', 'FS')[1]
        Zpos_2x6 = self.get_nail_count('2x6', 'FS')[1]
        # Value Used for Nail spacing along Header oriented elements (mm)
        HeaderNailSpacing = 304.8
        # List that Function will return containing all OpJobs for Sub Assembly being evaluated
        OpJobList = []
        # elementList [panelguid,elementguid,type,description,size,b1x,b1y,b2x,b2y,b3x,b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,count]
        #            [   0     ,      1    ,  2 ,    3      ,  4 , 5 , 6 , 7 , 8 , 9 , 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]
        for elem in element_list:
            # list of bools for FS & MS containing [StudStop,Hammer,Multi-Device,Option,Autostud,Operator Confirm, Nailing]
            OpFS = [False, False, False, False, False, False, False, False, False]
            OpMS = [False, False, False, False, False, False, False, False, False]
            # Sub Assembly Element is only touching Top plate
            if elem[16] == TopPlate and elem[14] != BottomPlate:
                # Check if StudStop and Hammer are being used for TopPlate side
                if clear.studStopMS(elem[1]):
                    OpMS[0] = True
                    if clear.hammerMS(elem[1]):
                        OpMS[1] = True

                # Set Nailing TopPlate Side in Opcode
                OpMS[6] = True

                # Is the element in the sub assembly normal stud orientation against Top Plate
                if (elem[17] - elem[13]) < 50.8:
                    if elem[4] == "2X4":
                        ct = 0
                        while ct < nailCount_2x4:
                            OpJob = [elem[5]]
                            # Xpos
                            # generate OpText and OpCodes from list of bools
                            tmpMS = gen_op_code(OpMS)
                            # list to append to OpJob
                            OpJobAppend = [tmpMS[0], 0, 0, 0, 0, tmpMS[1], Zpos_2x4[ct], 0, 0, '', 0]
                            OpJob.extend(OpJobAppend)
                            ct += 1
                            OpJobList.append(OpJob)

                    if elem[4] == "2X6":
                        ct = 0
                        while ct < nailCount_2x6:
                            OpJob = [elem[5]]
                            # Xpos
                            # generate OpText and OpCodes from list of bools
                            tmpMS = gen_op_code(OpMS)
                            # list to append to OpJob
                            OpJobAppend = [tmpMS[0], 0, 0, 0, 0, tmpMS[1], Zpos_2x6[ct], 0, 0, '', 0]
                            OpJob.extend(OpJobAppend)
                            ct += 1
                            OpJobList.append(OpJob)

                # Non Header Orientation along Top Plate (Flat against Top Plate)
                elif (elem[16] - elem[14]) < 50.8:
                    # b3x - b1x 
                    Length_of_Header = elem[17] - elem[13]
                    Number_of_NailSpacings = Length_of_Header / HeaderNailSpacing
                    if elem[4] == "2X4":
                        NailCounter = 0
                        while NailCounter < Number_of_NailSpacings:
                            ct = 0
                            while ct < nailCount_2x4:
                                OpJob = [elem[5] + (NailCounter * HeaderNailSpacing)]
                                # Xpos
                                # generate OpText and OpCodes from list of bools
                                tmpMS = gen_op_code(OpMS)
                                # list to append to OpJob & append it
                                OpJobAppend = [tmpMS[0], 0, 0, 0, 0, tmpMS[1], Zpos_2x4[ct], 0, 0, '', 0]
                                OpJob.extend(OpJobAppend)
                                ct += 1
                                OpJobList.append(OpJob)
                            NailCounter += 1

                    if elem[4] == "2X6":
                        NailCounter = 0
                        while NailCounter < Number_of_NailSpacings:
                            ct = 0
                            while ct < nailCount_2x6:
                                OpJob = [elem[5] + (NailCounter * HeaderNailSpacing)]
                                # Xpos
                                # generate OpText and OpCodes from list of bools
                                tmpMS = gen_op_code(OpMS)
                                # list to append to OpJob & append it
                                OpJobAppend = [tmpMS[0], 0, 0, 0, 0, tmpMS[1], Zpos_2x6[ct], 0, 0, '', 0]
                                OpJob.extend(OpJobAppend)
                                ct += 1
                                OpJobList.append(OpJob)

                            NailCounter += 1
                # Header Orientation along Top Plate(Perpendicular to Top Plate)
                elif (elem[16] - elem[14]) > 50.8:
                    # b3x - b1x 
                    Length_of_Header = elem[17] - elem[13]
                    Number_of_NailSpacings = Length_of_Header / HeaderNailSpacing
                    NailCounter = 0
                    Zpos = round((self.panelThickness * 25.4) - abs(elem[6]) + 19, 0)
                    while NailCounter < Number_of_NailSpacings:
                        OpJob = [elem[5] + (NailCounter * HeaderNailSpacing)]
                        # Xpos
                        # generate OpText and OpCodes from list of bools
                        tmpFS = gen_op_code(OpFS)
                        tmpMS = gen_op_code(OpMS)
                        # list to append to OpJob & append it
                        OpJobAppend = [tmpMS[0], 0, 0, 0, 0, tmpMS[1], Zpos, 0, 0, '', 0]
                        OpJob.extend(OpJobAppend)
                        OpJobList.append(OpJob)
                        NailCounter += 1

            # Sub Assembly Element is only Touching Bottom Plate
            if elem[14] == BottomPlate and elem[16] != TopPlate:
                # Check if StudStop and Hammer are being used for Bottom Plate side
                if clear.studStopFS(elem):
                    OpFS[0] = True
                    if clear.hammerFS(elem[1]):
                        OpFS[1] = True

                # Set Nailing Bottom Plate Side in Opcode
                OpFS[6] = True

                # Is the element in the sub assembly normal stud orientation against Bottom Plate
                if (elem[17] - elem[13]) < 50.8:
                    if elem[4] == "2X4":
                        ct = 0
                        while ct < nailCount_2x4:
                            OpJob = [elem[5]]
                            # Xpos
                            # generate OpText and OpCodes from list of bools
                            tmpFS = gen_op_code(OpFS)
                            # list to append to OpJob & append it
                            OpJobAppend = [tmpFS[0], tmpFS[1], Zpos_2x4[ct], 0, 0, 0, 0, 0, 0, '', 0]
                            OpJob.extend(OpJobAppend)
                            ct += 1
                            OpJobList.append(OpJob)

                    if elem[4] == "2X6":
                        ct = 0
                        while ct < nailCount_2x6:
                            OpJob = []
                            # Xpos
                            OpJob.append(elem[5])
                            # generate OpText and OpCodes from list of bools
                            tmpFS = gen_op_code(OpFS)
                            # list to append to OpJob & append it
                            OpJobAppend = [tmpFS[0], tmpFS[1], Zpos_2x6[ct], 0, 0, 0, 0, 0, 0, '', 0]
                            OpJob.extend(OpJobAppend)
                            ct += 1
                            OpJobList.append(OpJob)


                # Non Header Orientation along Bottom Plate (Flat against Top Plate)
                elif (elem[16] - elem[14]) < 50.8:
                    # b3x - b1x 
                    Length_of_Header = elem[17] - elem[13]
                    Number_of_NailSpacings = Length_of_Header / HeaderNailSpacing
                    if elem[4] == "2X4":
                        NailCounter = 0
                        while NailCounter < Number_of_NailSpacings:
                            ct = 0
                            while ct < nailCount_2x4:
                                OpJob = [elem[5] + (NailCounter * HeaderNailSpacing)]
                                # Xpos
                                # generate OpText and OpCodes from list of bools
                                tmpFS = gen_op_code(OpFS)
                                # list to append to OpJob & append it
                                OpJobAppend = [tmpFS[0], tmpFS[1], Zpos_2x4[ct], 0, 0, 0, 0, 0, 0, '', 0]

                                OpJob.extend(OpJobAppend)
                                ct += 1
                                OpJobList.append(OpJob)
                            NailCounter += 1

                    if elem[4] == "2X6":
                        NailCounter = 0
                        while NailCounter < Number_of_NailSpacings:
                            ct = 0
                            while ct < nailCount_2x6:
                                OpJob = [elem[5] + (NailCounter * HeaderNailSpacing)]
                                # Xpos
                                # generate OpText and OpCodes from list of bools
                                tmpFS = gen_op_code(OpFS)
                                # list to append to OpJob & append it
                                OpJobAppend = [tmpFS[0], tmpFS[1], Zpos_2x6[ct], 0, 0, 0, 0, 0, 0, '', 0]

                                OpJob.extend(OpJobAppend)
                                ct += 1
                                OpJobList.append(OpJob)
                            NailCounter += 1

                # Header Orientation along Bottom Plate (Perpendicular to Top Plate)
                elif (elem[16] - elem[14]) > 50.8:
                    # b3x - b1x 
                    Length_of_Header = elem[17] - elem[13]
                    Number_of_NailSpacings = Length_of_Header / HeaderNailSpacing
                    NailCounter = 0
                    Zpos = round((elem[8] - elem[6]) / 2, 0)
                    while NailCounter < Number_of_NailSpacings:
                        OpJob = [elem[5] + (NailCounter * HeaderNailSpacing)]
                        # Xpos
                        # generate OpText and OpCodes from list of bools
                        tmpFS = gen_op_code(OpFS)
                        # list to append to OpJob & append it
                        OpJobAppend = [tmpFS[0], tmpFS[1], Zpos, 0, 0, 0, 0, 0, 0, '', 0]

                        OpJob.extend(OpJobAppend)
                        OpJobList.append(OpJob)
                        NailCounter += 1

            # Sub Assembly Element is Touching Top and Bottom Plate
            if elem[14] == BottomPlate and elem[16] == TopPlate:
                if elem[5] > 5000.1:
                    pass
                # Check if StudStop and Hammer are being used for Bottom Plate side
                if clear.studStopFS(elem):
                    OpFS[0] = True

                if clear.hammerFS(elem[1]):
                    OpFS[1] = True

                # Set Nailing Bottom Plate Side in Opcode
                OpFS[6] = True

                # Check if StudStop and Hammer are being used for Top Plate side
                if clear.studStopMS(elem[1]):
                    OpMS[0] = True

                if clear.hammerMS(elem[1]):
                    OpMS[1] = True

                    # Set Nailing Top Plate Side in Opcode
                OpMS[6] = True

                # Is the element in the sub assembly normal stud orientation
                if (elem[17] - elem[13]) < 50.8:
                    if elem[4] == "2X4":
                        ct = 0
                        while ct < nailCount_2x4:
                            OpJob = [elem[5]]
                            # Xpos
                            # generate OpText and OpCodes from list of bools
                            tmpFS = gen_op_code(OpFS)
                            tmpMS = gen_op_code(OpMS)

                            # list to append to OpJob & append it
                            OpJobAppend = [tmpFS[0], tmpFS[1], Zpos_2x4[ct], 0, 0, tmpMS[1], Zpos_2x4[ct], 0, 0,
                                           '', 0]
                            OpJob.extend(OpJobAppend)
                            OpJobList.append(OpJob)
                            ct += 1

                    if elem[4] == "2X6":

                        ct = 0
                        while ct < nailCount_2x6:
                            OpJob = [elem[5]]
                            # Xpos
                            # generate OpText and OpCodes from list of bools
                            tmpFS = gen_op_code(OpFS)
                            tmpMS = gen_op_code(OpMS)
                            # list to append to OpJob & append it
                            OpJobAppend = [tmpFS[0], tmpFS[1], Zpos_2x6[ct], 0, 0, tmpMS[1], Zpos_2x6[ct], 0, 0,
                                           '', 0]
                            OpJob.extend(OpJobAppend)
                            OpJobList.append(OpJob)
                            ct += 1

                # Is the element in the sub assembly Flat stud orientation
                if (elem[17] - elem[13]) > 50.8:
                    top = (self.panelThickness * 25.4) + elem[8]
                    bottom = (self.panelThickness * 25.4) + elem[6]
                    if elem[4] == "2X4":
                        NailCounter = 0
                        XposOffset2X4 = [0, 70]
                        # Zpos = round((elem[8] - elem[6]) / 2, 0) This is old method
                        # new method
                        Zpos = round((bottom + top) / 2, 0)
                        while NailCounter < 2:
                            if NailCounter > 0:
                                OpFS[0] = False
                                OpMS[0] = False
                            OpJob = [elem[5] + XposOffset2X4[NailCounter]]
                            # Xpos
                            # generate OpText and OpCodes from list of bools
                            tmpFS = gen_op_code(OpFS)
                            tmpMS = gen_op_code(OpMS)
                            # list to append to OpJob & append it
                            OpJobAppend = [tmpFS[0], tmpFS[1], Zpos, 0, 0, tmpMS[1], Zpos, 0, 0, '', 0]
                            OpJob.extend(OpJobAppend)
                            OpJobList.append(OpJob)
                            NailCounter += 1

                    if elem[4] == "2X6":
                        NailCounter = 0
                        XposOffset2X6 = [0, 70, 125]
                        # Zpos = round((elem[8] - elem[6]) / 2, 0) This is old method
                        # new method
                        Zpos = round((bottom + top) / 2, 0)
                        while NailCounter < 2:
                            if NailCounter > 0:
                                OpFS[0] = False
                                OpMS[0] = False
                            OpJob = [elem[5] + XposOffset2X6[NailCounter]]
                            # Xpos
                            # generate OpText and OpCodes from list of bools
                            tmpFS = gen_op_code(OpFS)
                            tmpMS = gen_op_code(OpMS)
                            # list to append to OpJob & append it
                            OpJobAppend = [tmpFS[0], tmpFS[1], Zpos, 0, 0, tmpMS[1], Zpos, 0, 0, '', 0]
                            OpJob.extend(OpJobAppend)
                            OpJobList.append(OpJob)
                            NailCounter += 1

        op_list_sorted = sorted(OpJobList, key=lambda var: (var[0], var[3], var[7]))
        if len(element_list) > 0:
            count = element_list[0][-1]
        else:
            count = 0

        for OpJob in op_list_sorted:
            OpJob[-1] = count
            count += 1
        if len(element_list) > 0:
            op_list_sorted.append(count)
        # Return OpJob and updated count
        return op_list_sorted

    @staticmethod
    def hole_feature(element):
        # element is a list consisting of [panelguid,elementguid,type,description,size,b1x,b1y,b2x,b2y,b3x,b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,count]
        count = element[-1]
        # list of bools for FS & MS containing [StudStop,Hammer,Multi-Device,Option,Autostud,Operator Confirm, Nailing, Insulation, Drill]
        OpFS = [False, False, False, False, False, False, False, False, False]
        OpMS = [False, False, False, False, False, False, False, False, False]
        position = {
            'x': round(element[5], 2),
            'y': round(element[6], 2)}
        if element[2] == 'Hole':
            OpMS[8] = True

        # other element types? -> error?
        else:
            pass
            # print(f'error with elementguid: {element[1]} \n Type unknown')

        # generate OpText and OpCodes from list of bools
        tmpFS = gen_op_code(OpFS)
        tmpMS = gen_op_code(OpMS)
        # list to append to OpJob & append it
        OpElement = [position['x'], 'Drill', tmpFS[1], 0, 0, 0, tmpMS[1], 0, 0, 0, '', count]
        # Return OpJob and updated count
        return OpElement, count + 1

    def get_nail_count(self, size, side):
        # result -- [quantity, [pos1, pos2, pos3]]
        # Default [2 Nails, [19, 70]]
        result = [2, [19, 70]]  # Default
        if side == 'FS':
            if size == '2x4':
                positions = self.machine.ec1.nailSpaceFS['2x4']['positions']
                count = self.machine.ec1.nailSpaceFS['2x4']['nailCount']
                result = [count, positions]
            elif size == '2x6':
                positions = self.machine.ec1.nailSpaceFS['2x6']['positions']
                count = self.machine.ec1.nailSpaceFS['2x6']['nailCount']
                result = [count, positions]
        if side == 'MS':
            if size == '2x4':
                positions = self.machine.ec1.nailSpaceMS['2x4']['positions']
                count = self.machine.ec1.nailSpaceMS['2x4']['nailCount']
                result = [count, positions]
            elif size == '2x6':
                positions = self.machine.ec1.nailSpaceMS['2x6']['positions']
                count = self.machine.ec1.nailSpaceMS['2x6']['nailCount']
                result = [count, positions]
        return result


def gen_op_code(op_in: list):
    # This function converts a list of BOOLS to a list containing OpText and an integer opcode

    # OpIn is a list of opcode parameters
    # [Stud Stop, Hammer, Multi-device, Option, AutoStud, Operator Confirm, Nailing]
    opcode = ['', 0]
    if op_in[0]:
        opcode[0] += 'StudStop | '
        opcode[1] += 1
    if op_in[1]:
        opcode[0] += 'HammerUnit | '
        opcode[1] += 2
    if op_in[2]:
        opcode[0] += 'Multi-Device | '
        opcode[1] += 4
    if op_in[3]:
        opcode[0] += 'Option | '
        opcode[1] += 8
    if op_in[4]:
        opcode[0] += 'AutoStud | '
        opcode[1] += 16
    if op_in[5]:
        opcode[0] += 'OperatorConfirmation | '
        opcode[1] += 32
    if op_in[6]:
        opcode[0] += 'Nailing'
        opcode[1] += 64
    if op_in[8]:
        opcode[0] += ' Drill '
        opcode[1] += 256

        # remove trailing ' | ' from OpText string
    if opcode[0] != '':
        if opcode[0][-3] == ' ':
            opcode[0] = opcode[0][:-3]

    return opcode


def re_order_list(op_list) -> list:
    # This function is used to reorder the operation list to ensure merged
    # sub assemblies can be executed correctly in accordance to the x position only increasing
    for i in range(len(op_list)):
        for j in range(len(op_list) - 1):
            if op_list[j][1] > op_list[j + 1][1]:
                op_list[j], op_list[j + 1] = op_list[j + 1], op_list[j]

    indexed_list = [(*item[:-1], index + 1) for index, item in enumerate(op_list)]

    return indexed_list

def check_sub_install_x(op_list):
    # This function is used to check and update first nailing position
    #  when sub assemblies get loaded that the grippers don't move to a second location
    #  without first attaching the assembly to the plates
    pass
    for i in range(len(op_list)):
        pass