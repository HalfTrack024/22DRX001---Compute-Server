import util.dataBaseConnect as dbc
import util.framingCheck as fc
from util.machineData import Line
from util.panelData import Panel


class MtrlData:

    mtrldata = ()

    def __init__(self, panelData : Panel):
        #Assigns Panel Instance to Mtrl 
        self.panel = panelData
        
        #self.mdMain()

    # Main Call for determining Material List
    def mdMain(self):
        #Open Connection to the database
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        sql_var = self.panel.guid
        sql_select_query=f"""SELECT DISTINCT ON ("size") "type", description, "size", actual_thickness, actual_width, species
                    FROM cad2fab.system_elements
                    WHERE panelguid = '{sql_var}' AND description = 'Stud' AND type = 'Board'
                    ORDER BY "size" ASC;
                """       

        results = pgDB.query(sqlStatement=sql_select_query)
        
        sql_select_query=f"""SELECT count(description) 
                    FROM cad2fab.system_elements
                    WHERE panelguid = '{sql_var}' AND description = 'Stud' AND type = 'Board';
        """     
        resultcount = pgDB.query(sqlStatement=sql_select_query)
        pgDB.close()

        
        if len(results) == 1:            
            self.mrtldata = self.mdBuild(results[0], resultcount[0])
        else:
            print("returned to many options")

        self.mdInsert()

    def mdBuild(self, studs, count): # This function will assemble the entry line of Material Data
        uiItemLength = round(self.panel.studHeight * 25.4, 0)
        uiItemHeight = round(float(studs[3]) * 25.4, 0) # convert from inches to mm
        uiItemThickness = round(float(studs[4]) * 25.4, 0)  # convert from inches to mm
        sMtrlCode = studs[5]
        uiOpCode = 0
        sPrinterWrite = ' '	
        sType = ' '
        uiItemID = 0
        sCADPath = ' '
        sProjectName = ' '	
        sItemName = self.panel.guid

        line = (count, uiItemLength, uiItemHeight, uiItemThickness, sMtrlCode, uiOpCode, sPrinterWrite, sType, uiItemID, sCADPath, sProjectName, sItemName)
        return line
    
    def getMatCode(self, studType): # returns material code for size of material (1: 2x4, 2:2x6)
        #NEED TO DETERMINE HOW TO GET STUD MATERIAL CODE
        pass

    def mdInsert(self): # Inserts "mtrldata" list into table "materialData"
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        #send OpData to JobData table
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
        #make a list of tuples for querymany
        jdQueryData = []
        jdQueryData.append(self.mrtldata)        

        tmp = pgDB.querymany(sql_JobData_query,jdQueryData)
        pgDB.close()


    




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

    def __init__(self, panelguid, machine : Line):
        self.machine = machine
        # Getting Panel Information for Nailing calculations in nailSubElements Function
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()

        sql_select_query=f"""
                        SELECT thickness, studheight, walllength, category
                        FROM cad2fab.system_panels
                        WHERE panelguid = '{panelguid}';
                        """
        #
        results = pgDB.query(sqlStatement=sql_select_query)
        #dbc.printResult(results)
        pgDB.close()
        #assign results of query to variables
        self.panelguid = panelguid
        self.panelThickness = float(results[0][0])
        self.studHeight = (float(results[0][1]))*25.4
        self.panelLength = float(results[0][2])
        self.catagory = results[0][3]
        # End of Panel Information

        #Getting Stud Stop and Hammer Unit dimensions that framingCheck.py uses 
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        #get parameters for stud stop and hammer that are universal
        sql_select_query="""
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
        #dbc.printResult(results)
        #assign results of query to variables
        #thickness is in the X direction of elevation, width/length in the Y direction
        self.ss_thickness = float(results[0][1])
        self.ss_width = float(results[1][1])
        self.hu_thickness = float(results[2][1])
        self.hu_length = float(results[3][1])
        self.hu_stroke = float(results[4][1])
        self.hu_Y = float(results[5][1])
        pgDB.close()     
        #End of Framing Check

    def jdMain(self): # Job Data Main
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        panelguid = self.panelguid
        #query relevant data from elements table
        sql_elemData_query = f'''
        SELECT elementguid, type, description, size, b1x,b1y,b2x,b2y,b3x,b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,assembly_id
        FROM cad2fab.system_elements
        WHERE panelguid = '{panelguid}'
        ORDER BY b1x ASC;
        '''
        elemData = pgDB.query(sql_elemData_query)
        #counter for obj_id
        obj_count = 1
        #list of OpDatas
        OpData = []
        #list of placed sub assemblies
        placedSubAssembly = []
        #loop through all elements in the panel
        for i,elem in enumerate(elemData):
            #convert to mm and:
            #list of [panelguid,elementguid,type,description,size,b1x,b1y,b2x,b2y,b3x,
            #                       b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,assembly_id,count]
            if elem[4] != None:
                element = [panelguid,elem[0],elem[1],elem[2],elem[3],float(elem[4]) * 25.4,float(elem[5]) * 25.4,
                       float(elem[6]) * 25.4,float(elem[7]) * 25.4,float(elem[8]) * 25.4,float(elem[9]) * 25.4,
                       float(elem[10]) * 25.4,float(elem[11]) * 25.4,float(elem[12]) * 25.4,float(elem[13]) * 25.4,
                       float(elem[14]) * 25.4,float(elem[15]) * 25.4,float(elem[16]) * 25.4,float(elem[17]) * 25.4,
                       float(elem[18]) * 25.4,float(elem[19]) * 25.4,elem[-1],obj_count]

            #if the element isn't a sheet, top plate, bottom plate, very top plate or Nog
            if elem[1] != 'Sheet' and elem[2] != 'BottomPlate' and elem[2] != 'TopPlate' and elem[2] != 'VeryTopPlate' and elem[2] != 'Nog':
                #if the element is a normal stud
                if elem[1] != 'Sub-Assembly Board' and elem[1] != 'Sub Assembly' and elem[1] != 'Sub-Assembly Cutout' and elem[1] != 'Hole':
                    #get opData for placeing the element
                    tmp = self.placeElement(element)
                    #Add to OpDatas and increase the count
                    OpData.append(tmp[0])
                    obj_count = tmp[1]
                    #Add get OpDatas for nailing
                    tmp = self.nailElement(element)
                    # loop through the OpDatas from the function and append to the list
                    # exclude the last list item because that is the counter
                    for i in tmp[:-1]:
                        OpData.append(i)
                    #update counter
                    obj_count = tmp[-1]
                #if the element isn't in a placed sub assembly and is a sub assembly board or cutout
                elif elem[-1] not in placedSubAssembly and (elem[1] == 'Sub-Assembly Board' or elem[1] == 'Sub-Assembly Cutout'):
                    #get relevant data of elements that aren't sub assembly cutouts, sort by b1x ascending
                    sql_subelem_query = f'''
                    SELECT elementguid, type, description, size, b1x,b1y,b2x,b2y,b3x,b3y,b4x,b4y,
                    e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,assembly_id
                    FROM cad2fab.system_elements
                    WHERE panelguid = '{panelguid}' and assembly_id = '{elem[-1]}' and type != 'Sub-Assembly Cutout'
                    ORDER BY b1x ASC;
                    '''
                    subelemData = pgDB.query(sql_subelem_query)
                    #list of all sub elements and the sub assembly element, excluding rough cutouts(they don't need to be nailed)
                    subElemList = []
                    #loop through all the sub elements
                    for subelem in subelemData:
                        #if the sub elem has coordinates (isn't the sub assembly element)
                        if subelem[4] != None:
                            subelement = [panelguid,subelem[0],subelem[1],subelem[2],subelem[3],
                                          round(float(subelem[4]) * 25.4,1),round(float(subelem[5]) * 25.4,1),
                                round(float(subelem[6]) * 25.4,1),round(float(subelem[7]) * 25.4,1),round(float(subelem[8]) * 25.4,1),
                                round(float(subelem[9]) * 25.4,1),round(float(subelem[10]) * 25.4,1),round(float(subelem[11]) * 25.4,1),
                                round(float(subelem[12]) * 25.4,1),round(float(subelem[13]) * 25.4,1),round(float(subelem[14]) * 25.4,1),
                                round(float(subelem[15]) * 25.4,1),round(float(subelem[16]) * 25.4,1),round(float(subelem[17]) * 25.4,1),
                                round(float(subelem[18]) * 25.4,1),round(float(subelem[19]) * 25.4,1),subelem[-1],obj_count]
                        else: #if the sub elem is the subassembly element (always the last in the list due to sort by b1x)
                            subelement = [panelguid,subelem[0],subelem[1],subelem[2],subelem[3],subelem[4],subelem[5],
                                subelem[6],subelem[7],subelem[8],subelem[9],
                                subelem[10],subelem[11],subelem[12],subelem[13],
                                subelem[14],subelem[15],subelem[16],subelem[17],
                                subelem[18],subelem[19],subelem[-1],obj_count]
                        #add the item to the list
                        subElemList.append(subelement)
                    #place the sub assembly send(sub assembly element, first board in the sub assembly for b1x position)
                    tmp = self.placeElement(subElemList[-1],element)
                    #add to opdata and update counter
                    OpData.append(tmp[0])
                    obj_count = tmp[1]
                    #update the counter for all items in the subelemlist
                    for i in subElemList[:-1]:
                        i[-1] = obj_count
                    #get the nailing data, add it to the opdata list and update the counter
                    tmp = self.nailSubElement(subElemList[:-1])
                    for i in tmp[:-1]:
                        OpData.append(i)
                    obj_count = tmp[-1]
                    #add the assembly id to the list of placed sub assemblies
                    placedSubAssembly.append(elem[-1])
                elif elem[1] == 'Hole':
                    #pass
                    tmp = self.holeFeature(element)
                    for op in reversed(OpData):
                        if op[0] > tmp[0][0]:
                            continue
                        else:
                            indexOp = OpData.index(op)
                            OpData.insert(indexOp+1, tmp[0])
                            for i in range(op[-1]-1, len(OpData)):
                                OpData[i][-1] = i+1
                            break
                    obj_count = i+2
        #send OpData to JobData table
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
        #make a list of tuples for querymany
        jdQueryData = []
        for item in OpData:
            jdQueryData.append((panelguid, item[0],item[1],item[2],item[3],item[4],
                                item[5],item[6],item[7],item[8],item[9],item[10],item[11]))
            
        pgDB.querymany(sql_JobData_query,jdQueryData)
        #close the DB connection
        pgDB.close()


    def placeElement(self,element,subelement = None):
        #call function with (self,element, subassembly board if applicable)

        #list of [panelguid,elementguid,type,description,size,b1x,b1y,b2x,b2y,b3x,
        #                       b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,assembly_id,count]
        clear = fc.Clear()
        #empty list for [Xpos,OpText,OpCodeFS,ZposFS,YposFS,SSupPosFS,OpCodeMS,ZposMS,YposMS,SSupPosMS,IMG_NAME,OBJ_ID]
        OpJob = []
        # if placing a standard board
        if subelement == None:
            #add X Pos from element
            OpJob.append(element[5])
        #if placing a subassembly
        else:
            #add X pos from sub assembly board
            OpJob.append(float(subelement[5]))
        #list of bools for FS & MS containing [StudStop,Hammer,Multi-Device,Option,Autostud,Operator Confirm, Nailing, Insulation, Drill]
        OpFS = [False,False,False,False,False,False,False, False, False]
        OpMS = [False,False,False,False,False,False,False, False, False]
        #check if the stud stops are clear for standard elements
        if subelement == None:
            if clear.studStopFS(element[1]) == True:
                OpFS[0] = True
            
            if clear.studStopMS(element[1]) == True:
                OpMS[0] = True
        #check if the stud stops are clear for sub assemblies
        else:
            if clear.studStopFS(subelement[1]) == True:
                OpFS[0] = True
            
            if clear.studStopMS(subelement[1]) == True:
                OpMS[0] = True
        #if element is a stud enable hammer and autostud
        if element[2] == 'Board' and element[3] == 'Stud':
            OpFS[1] = True
            OpFS[4] = True
            OpMS[1] = True
            OpMS[4] = True
            # if element is the first stud enable operator confirm
            if element[5] <= 25.4:
                OpFS[5] = True
                OpMS[5] = True
        #if element is a sub assembly
        elif element[2] == 'Sub Assembly':
            #set operator confirm
            OpFS[5] = True
            OpMS[5] = True
        #other element types -> error
        else:
            if clear.hammerFS(element[1]) == True:
                OpFS[1] = True
            if clear.hammerMS(element[1]) == True:
                OpMS[1] = True
            print(f'error with elementguid: {element[1]} \n Type unknown')
            
        #generate OpText and OpCodes from list of bools
        tmpFS = JobData.genOpCode(OpFS)
        tmpMS = JobData.genOpCode(OpMS)
        #list to append to OpJob & append it
        OpJobAppend = [tmpFS[0],tmpFS[1], 0, 0, 0, tmpMS[1], 0, 0, 0, 'ImgName', element[-1]]
        for i in OpJobAppend:
            OpJob.append(i)
        # increase OBJ_ID Count for studs or subassemblies
        if subelement == None:
            element[-1] += 1
        else:
            element[-1] = subelement[-1] + 1
        # Return OpJob and updated count
        
        return(OpJob,element[-1])
    

    def genOpCode(OpIn):
        #This function converts a list of bools to a list containing OpText and an integer opcode

        #OpIn is a list of opcode parameters 
        #[Stud Stop, Hammer, Multi-device, Option, AutoStud, Operator Confirm, Nailing]
        opcode = ['', 0]
        if OpIn[0] == True:
            opcode[0] += 'StudStop | '
            opcode[1] += 1
        if OpIn[1] == True:
            opcode[0] += 'HammerUnit | '
            opcode[1] += 2
        if OpIn[2] == True:
            opcode[0] += 'Multi-Device | '
            opcode[1] += 4
        if OpIn[3] == True:
            opcode[0] += 'Option | '
            opcode[1] += 8
        if OpIn[4] == True:
            opcode[0] += 'AutoStud | '
            opcode[1] += 16
        if OpIn[5] == True:
            opcode[0] += 'OperatorConfirmation | '
            opcode[1] += 32
        if OpIn[6] == True:
            opcode[0] += 'Nailing'
            opcode[1] += 64
        if OpIn[8]:
            opcode[0] += ' Drill '
            opcode[1] += 256            
            
        #remove trailing ' | ' from OpText string
        if opcode[0] != '':
            if opcode[0][-3] == ' ':
                opcode[0] = opcode[0][:-3]
        
        return opcode


    def nailElement(self,element):
        #element is a list consisting of [panelguid,elementguid,type,description,size,b1x,b1y,b2x,b2y,b3x,b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,count]
        #Used for calling StudStop or Hamer Unit Functions
        clear = fc.Clear()
        #Obj_ID
        count = element[-1]
        #List used as output of nailElement Function
        OpElement = []
        #Z positions for Nailing
        nailCount_2x4 = self.getNailCount('2x4', 'FS')[0]
        nailCount_2x6 = self.getNailCount('2x6', 'FS')[0]
        Zpos_2x4 = self.getNailCount('2x4', 'FS')[1]
        Zpos_2x6 = self.getNailCount('2x6', 'FS')[1]
        #list of bools for FS & MS containing [StudStop,Hammer,Multi-Device,Option,Autostud,Operator Confirm, Nailing, Insulation, Drill]
        OpFS = [False,False,False,False,False,False,False, False, False]
        OpMS = [False,False,False,False,False,False,False, False, False]
        if element[4] == "2X4":
            ct = 0
            while ct < nailCount_2x4:
                OpJob = []
                #Xpos
                OpJob.append(element[5])
                #check if the stud stops are clear
                if clear.studStopFS(element[1]) == True:
                    OpFS[0] = True

                if clear.studStopMS(element[1]) == True:
                    OpMS[0] = True

                #if element is a stud enable hammer, autostud, and nailing
                if element[2] == 'Board' and element[3] == 'Stud':
                    OpFS[1] = True
                    OpFS[4] = True
                    OpFS[6] = True
                    OpMS[1] = True
                    OpMS[4] = True
                    OpMS[6] = True 
                #other element types? -> error?
                else:
                    if clear.hammerFS(element[1]) == True:
                        OpFS[1] = True
                    if clear.hammerMS(element[1]) == True:
                        OpMS[1] = True
                    print(f'error with elementguid: {element[1]} \n Type unknown')

                #generate OpText and OpCodes from list of bools
                tmpFS = JobData.genOpCode(OpFS)
                tmpMS = JobData.genOpCode(OpMS)
                #list to append to OpJob & append it
                OpJobAppend = [tmpFS[0],tmpFS[1],Zpos_2x4[ct], 0, 0,tmpMS[1],Zpos_2x4[ct],0, 0, 'ImgName', count]
                
                for i in OpJobAppend:
                    OpJob.append(i)
                # increase Nail position counter and OBJ_ID Counter
                ct += 1
                count += 1
                OpElement.append(OpJob)

        elif element[4] == "2X6":
            ct = 0
            while ct < nailCount_2x6:
                OpJob = []
                #Xpos
                OpJob.append(element[5])
                #check if the stud stops are clear
                if clear.studStopFS(element[1]) == True:
                    OpFS[0] = True

                if clear.studStopMS(element[1]) == True:
                    OpMS[0] = True

                #if element is a stud enable hammer, autostud and nailing
                if element[2] == 'Board' and element[3] == 'Stud':
                    OpFS[1] = True
                    OpFS[4] = True
                    OpFS[6] = True
                    OpMS[1] = True
                    OpMS[4] = True
                    OpMS[6] = True 
                #other element types? -> error?
                else:
                    if clear.hammerFS(element[1]) == True:
                        OpFS[1] = True
                    if clear.hammerMS(element[1]) == True:
                        OpMS[1] = True
                    print(f'error with elementguid: {element[1]} \n Type unknown')

                #generate OpText and OpCodes from list of bools
                tmpFS = JobData.genOpCode(OpFS)
                tmpMS = JobData.genOpCode(OpMS)
                #list to append to OpJob & append it
                OpJobAppend = [tmpFS[0],tmpFS[1],Zpos_2x6[ct], 0, 0,tmpMS[1],Zpos_2x6[ct],0, 0, 'ImgName', count]
                for i in OpJobAppend:
                    OpJob.append(i)
                # increase Nail position counter and OBJ_ID Counter
                ct += 1
                count += 1
                OpElement.append(OpJob)
        OpElement.append(count)
        # Return OpJob and updated count
        return(OpElement)


    def nailSubElement(self,elementList):
        #Used for calling StudStop or Hamer Unit Functions
        clear = fc.Clear()
        #Top and Bottom Plate variables used to check if Sub-Assembly element is touching
        TopPlate = round(38.1 + self.studHeight,1)
        BottomPlate = 38.1
        #Z positions for Nailing
        nailCount_2x4 = self.getNailCount('2x4', 'FS')[0]
        nailCount_2x6 = self.getNailCount('2x6', 'FS')[0]
        Zpos_2x4 = self.getNailCount('2x4', 'FS')[1]
        Zpos_2x6 = self.getNailCount('2x6', 'FS')[1]
        #Value Used for Nail spacing along Header oriented elements (mm)
        HeaderNailSpacing = 304.8
        #List that Function will return containing all OpJobs for Sub Assembly being evaluated
        OpJobList = []
        #elementList [panelguid,elementguid,type,description,size,b1x,b1y,b2x,b2y,b3x,b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,count]
        #            [   0     ,      1    ,  2 ,    3      ,  4 , 5 , 6 , 7 , 8 , 9 , 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]
        for elem in elementList:
            print(elem[5])
            #list of bools for FS & MS containing [StudStop,Hammer,Multi-Device,Option,Autostud,Operator Confirm, Nailing]
            OpFS = [False,False,False,False,False,False,False, False, False]
            OpMS = [False,False,False,False,False,False,False, False, False]
            #Sub Assembly Element is only touching Top plate
            if elem[16] == TopPlate and elem[14] != BottomPlate:
                # Check if StudStop and Hammer are being used for TopPlate side
                if clear.studStopMS(elem[1]) == True:
                    OpMS[0] = True

                if clear.hammerMS(elem[1]) == True:
                    OpMS[1] = True

                #Set Nailing TopPlate Side in Opcode
                OpMS[6] = True

                #Is the element in the sub assembly normal stud orientation against Top Plate
                if (elem[17] - elem[13]) < 50.8:
                    if elem[4] == "2X4":
                        ct = 0
                        while ct < nailCount_2x4:
                            OpJob = [] 
                            #Xpos
                            OpJob.append(elem[5])
                            #generate OpText and OpCodes from list of bools
                            tmpMS = JobData.genOpCode(OpMS)
                            #list to append to OpJob 
                            OpJobAppend = [tmpMS[0],0,0, 0, 0,tmpMS[1],Zpos_2x4[ct],0, 0, 'ImgName', 0]
                            for i in OpJobAppend:
                                OpJob.append(i)
                            ct += 1
                            OpJobList.append(OpJob)

                    if elem[4] == "2X6":
                        ct = 0
                        while ct < nailCount_2x6:
                            OpJob = []
                            #Xpos
                            OpJob.append(elem[5])
                            #generate OpText and OpCodes from list of bools
                            tmpMS = JobData.genOpCode(OpMS)
                            #list to append to OpJob
                            OpJobAppend = [tmpMS[0],0,0, 0, 0,tmpMS[1],Zpos_2x6[ct],0, 0, 'ImgName', 0]
                            for i in OpJobAppend:
                                OpJob.append(i)
                            ct += 1
                            OpJobList.append(OpJob)
                

                #Non Header Orientation along Top Plate (Flat against Top Plate)
                elif (elem[16] - elem[14]) < 50.8:
                    # b3x - b1x 
                    Length_of_Header = elem[17] - elem[13]
                    Number_of_NailSpacings = Length_of_Header/HeaderNailSpacing
                    if elem[4] == "2X4":
                        NailCounter = 0
                        while NailCounter < Number_of_NailSpacings:
                            ct = 0
                            while ct < nailCount_2x4:
                                OpJob = []  
                                #Xpos
                                OpJob.append(elem[5] + (NailCounter*HeaderNailSpacing))
                                #generate OpText and OpCodes from list of bools
                                tmpMS = JobData.genOpCode(OpMS)
                                #list to append to OpJob & append it
                                OpJobAppend = [tmpMS[0],0,0, 0, 0,tmpMS[1],Zpos_2x4[ct],0, 0, 'ImgName', 0]
                                for i in OpJobAppend:
                                    OpJob.append(i)
                                ct += 1
                                OpJobList.append(OpJob)
                            NailCounter += 1

                    if elem[4] == "2X6":
                        NailCounter = 0
                        while NailCounter < Number_of_NailSpacings: 
                            ct = 0
                            while ct < nailCount_2x6:
                                OpJob = []
                                #Xpos
                                OpJob.append(elem[5] + (NailCounter*HeaderNailSpacing))
                                #generate OpText and OpCodes from list of bools
                                tmpMS = JobData.genOpCode(OpMS)
                                #list to append to OpJob & append it
                                OpJobAppend = [tmpMS[0],0,0, 0, 0,tmpMS[1],Zpos_2x6[ct],0, 0, 'ImgName', 0]
                                for i in OpJobAppend:
                                    OpJob.append(i)
                                ct += 1
                                OpJobList.append(OpJob)

                            NailCounter += 1
                #Header Orientation along Top Plate(Perpendicular to Top Plate)
                elif (elem[16] - elem[14]) > 50.8:
                    # b3x - b1x 
                    Length_of_Header = elem[17] - elem[13]
                    Number_of_NailSpacings = Length_of_Header/HeaderNailSpacing
                    NailCounter = 0
                    Zpos = round((self.panelThickness * 25.4)- abs(elem[6]) + 19,0)
                    while NailCounter < Number_of_NailSpacings:  
                        OpJob = []
                        #Xpos
                        OpJob.append(elem[5] + (NailCounter*HeaderNailSpacing))
                        #generate OpText and OpCodes from list of bools
                        tmpFS = JobData.genOpCode(OpFS)
                        tmpMS = JobData.genOpCode(OpMS)
                        #list to append to OpJob & append it
                        OpJobAppend = [tmpMS[0],0,0, 0, 0,tmpMS[1],Zpos,0, 0, 'ImgName', 0]
                        for i in OpJobAppend:
                            OpJob.append(i)
                        OpJobList.append(OpJob)
                        NailCounter += 1



            # Sub Assembly Element is only Touching Bottom Plate
            if elem[14] == BottomPlate and elem[16] != TopPlate:
                # Check if StudStop and Hammer are being used for Bottom Plate side
                if clear.studStopFS(elem[1]) == True:
                    OpFS[0] = True

                if clear.hammerFS(elem[1]) == True:
                    OpFS[1] = True

                # Set Nailing Bottom Plate Side in Opcode
                OpFS[6] = True
                
                #Is the element in the sub assembly normal stud orientation against Bottom Plate
                if (elem[17] - elem[13]) < 50.8: 
                    if elem[4] == "2X4": 
                        ct = 0
                        while ct < nailCount_2x4:
                            OpJob = []
                            #Xpos
                            OpJob.append(elem[5])
                            #generate OpText and OpCodes from list of bools
                            tmpFS = JobData.genOpCode(OpFS)
                            #list to append to OpJob & append it
                            OpJobAppend = [tmpFS[0],tmpFS[1],Zpos_2x4[ct], 0, 0,0,0,0, 0, 'ImgName', 0]
                            for i in OpJobAppend:
                                OpJob.append(i)
                            ct += 1
                            OpJobList.append(OpJob)


                    if elem[4] == "2X6":
                        ct = 0
                        while ct < nailCount_2x6:
                            OpJob = []
                            #Xpos
                            OpJob.append(elem[5])
                            #generate OpText and OpCodes from list of bools
                            tmpFS = JobData.genOpCode(OpFS)
                            #list to append to OpJob & append it
                            OpJobAppend = [tmpFS[0],tmpFS[1],Zpos_2x6[ct], 0, 0,0,0,0, 0, 'ImgName', 0]
                            for i in OpJobAppend:
                                OpJob.append(i)
                            ct += 1
                            OpJobList.append(OpJob)
                

                #Non Header Orientation along Bottom Plate (Flat against Top Plate)
                elif (elem[16] - elem[14]) < 50.8:
                    # b3x - b1x 
                    Length_of_Header = elem[17] - elem[13]
                    Number_of_NailSpacings = Length_of_Header/HeaderNailSpacing
                    if elem[4] == "2X4":
                        NailCounter = 0
                        while NailCounter < Number_of_NailSpacings:  
                            ct = 0
                            while ct < nailCount_2x4:
                                OpJob = []
                                #Xpos
                                OpJob.append(elem[5] + (NailCounter*HeaderNailSpacing))
                                #generate OpText and OpCodes from list of bools
                                tmpFS = JobData.genOpCode(OpFS)
                                #list to append to OpJob & append it
                                OpJobAppend = [tmpFS[0],tmpFS[1],Zpos_2x4[ct],0,0,0,0,0,0, 'ImgName', 0]

                                for i in OpJobAppend:
                                    OpJob.append(i)
                                ct += 1
                                OpJobList.append(OpJob)
                            NailCounter += 1

                    if elem[4] == "2X6":
                        NailCounter = 0
                        while NailCounter < Number_of_NailSpacings: 
                            ct = 0
                            while ct < nailCount_2x6:
                                OpJob = []
                                #Xpos
                                OpJob.append(elem[5] + (NailCounter*HeaderNailSpacing))
                                #generate OpText and OpCodes from list of bools
                                tmpFS = JobData.genOpCode(OpFS)
                                #list to append to OpJob & append it
                                OpJobAppend = [tmpFS[0],tmpFS[1],Zpos_2x6[ct],0,0,0,0,0,0, 'ImgName', 0]

                                for i in OpJobAppend:
                                    OpJob.append(i)
                                ct += 1
                                OpJobList.append(OpJob)
                            NailCounter += 1

                #Header Orientation along Bottom Plate (Perpendicular to Top Plate)
                elif (elem[16] - elem[14]) > 50.8:
                    # b3x - b1x 
                    Length_of_Header = elem[17] - elem[13]
                    Number_of_NailSpacings = Length_of_Header/HeaderNailSpacing
                    NailCounter = 0
                    Zpos = round((elem[8] - elem[6])/2,0)
                    while NailCounter < Number_of_NailSpacings:  
                        OpJob = []
                        #Xpos
                        OpJob.append(elem[5] + (NailCounter*HeaderNailSpacing))
                        #generate OpText and OpCodes from list of bools
                        tmpFS = JobData.genOpCode(OpFS)
                        #list to append to OpJob & append it
                        OpJobAppend = [tmpFS[0],tmpFS[1],Zpos,0,0,0,0,0,0, 'ImgName', 0]

                        for i in OpJobAppend:
                            OpJob.append(i)
                        OpJobList.append(OpJob)
                        NailCounter += 1

            # Sub Assembly Element is Touching Top and Bottom Plate
            if elem[14] == BottomPlate and elem[16] == TopPlate:
                if elem[5] == 5772.1:
                    pass
                # Check if StudStop and Hammer are being used for Bottom Plate side
                if clear.studStopFS(elem[1]) == True:
                    OpFS[0] = True

                if clear.hammerFS(elem[1]) == True:
                    OpFS[1] = True

                # Set Nailing Bottom Plate Side in Opcode
                OpFS[6] = True

                # Check if StudStop and Hammer are being used for Top Plate side
                if clear.studStopMS(elem[1]) == True:
                    OpMS[0] = True

                if clear.hammerMS(elem[1]) == True:
                    OpMS[1] = True              

                # Set Nailing Top Plate Side in Opcode
                OpMS[6] = True
                
                #Is the element in the sub assembly normal stud orientation
                if (elem[17] - elem[13]) < 50.8: 
                    if elem[4] == "2X4":
                        ct = 0
                        while ct < nailCount_2x4:
                            OpJob = []
                            #Xpos
                            OpJob.append(elem[5])
                            #generate OpText and OpCodes from list of bools
                            tmpFS = JobData.genOpCode(OpFS)
                            tmpMS = JobData.genOpCode(OpMS)

                            #list to append to OpJob & append it
                            OpJobAppend = [tmpFS[0],tmpFS[1],Zpos_2x4[ct], 0, 0,tmpMS[1],Zpos_2x4[ct],0, 0, 'ImgName', 0]
                            for i in OpJobAppend:
                                OpJob.append(i)
                            OpJobList.append(OpJob)
                            ct += 1

                    if elem[4] == "2X6":
                        
                        ct = 0
                        while ct < nailCount_2x6:
                            OpJob = []
                            #Xpos
                            OpJob.append(elem[5])
                            #generate OpText and OpCodes from list of bools
                            tmpFS = JobData.genOpCode(OpFS)
                            tmpMS = JobData.genOpCode(OpMS)
                            #list to append to OpJob & append it
                            OpJobAppend = [tmpFS[0],tmpFS[1],Zpos_2x6[ct], 0, 0,tmpMS[1],Zpos_2x6[ct],0, 0, 'ImgName', 0]
                            for i in OpJobAppend:
                                OpJob.append(i)
                            OpJobList.append(OpJob)
                            ct += 1
                
                #Is the element in the sub assembly Flat stud orientation
                if (elem[17] - elem[13]) > 50.8:
                    if elem[4] == "2X4":
                        NailCounter = 0
                        XposOffset2X4 = [0,70]
                        Zpos = round((elem[8] - elem[6])/2,0)
                        while NailCounter < 2:
                            if NailCounter > 0:
                                OpFS[0] = False
                                OpMS[0] = False
                            OpJob = []
                            #Xpos
                            OpJob.append(elem[5] + XposOffset2X4[NailCounter])
                            #generate OpText and OpCodes from list of bools
                            tmpFS = JobData.genOpCode(OpFS)
                            tmpMS = JobData.genOpCode(OpMS)
                            #list to append to OpJob & append it
                            OpJobAppend = [tmpFS[0],tmpFS[1],Zpos, 0, 0,tmpMS[1],Zpos,0, 0, 'ImgName', 0]
                            for i in OpJobAppend:
                                OpJob.append(i)
                            OpJobList.append(OpJob)
                            NailCounter += 1
                    

                    if elem[4] == "2X6":
                        NailCounter = 0
                        XposOffset2X6 = [15,70,125]
                        Zpos = round((elem[8] - elem[6])/2,0)
                        while NailCounter < 2:
                            OpJob = []
                            #Xpos
                            OpJob.append(elem[5] + XposOffset2X6[NailCounter])
                            #generate OpText and OpCodes from list of bools
                            tmpFS = JobData.genOpCode(OpFS)
                            tmpMS = JobData.genOpCode(OpMS)
                            #list to append to OpJob & append it
                            OpJobAppend = [tmpFS[0],tmpFS[1],Zpos, 0, 0,tmpMS[1],Zpos,0, 0, 'ImgName', 0]
                            for i in OpJobAppend:
                                OpJob.append(i)
                            OpJobList.append(OpJob)
                            NailCounter += 1

        OplistSorted = sorted(OpJobList,key=lambda var:(var[0],var[3],var[7]))
        if len(elementList) > 0:
            count = elementList[0][-1]
            
        for OpJob in OplistSorted:
            OpJob[-1] = count
            count += 1
        if len(elementList) > 0:
            OplistSorted.append(count)
        # Return OpJob and updated count
        return(OplistSorted)
    
    def holeFeature(self, element):
        #element is a list consisting of [panelguid,elementguid,type,description,size,b1x,b1y,b2x,b2y,b3x,b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,count]
        #Used for calling StudStop or Hamer Unit Functions
        count = element[-1]
        #List used as output of nailElement Function
        OpElement = []
        #Z positions for Nailing
        Zpos_2x4 = [19,70]
        Zpos_2x6 = [15,70,125]
        #list of bools for FS & MS containing [StudStop,Hammer,Multi-Device,Option,Autostud,Operator Confirm, Nailing, Insulation, Drill]
        OpFS = [False,False,False,False,False,False,False, False, False]
        OpMS = [False,False,False,False,False,False,False, False, False]
        offset = 439.5
        position = {
            'x' : round(element[5], 2),
            'y' : round(element[6], 2)}
        if element[2] == 'Hole':
            OpMS[8] = True
                
        #other element types? -> error?
        else:
            print(f'error with elementguid: {element[1]} \n Type unknown')

        #generate OpText and OpCodes from list of bools
        tmpFS = JobData.genOpCode(OpFS)
        tmpMS = JobData.genOpCode(OpMS)
        #list to append to OpJob & append it
        OpElement = [position['x'], 'Drill',tmpFS[1],0, 0, 0,tmpMS[1],0,0, 0, 'ImgName', count]
        # Return OpJob and updated count
        return(OpElement, count+1)

    def getNailCount(self, size, side):
        # result -- [quantity, [pos1, pos2, pos3]]
        result = []
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
        return [count, positions]