import dataBaseConnect as dbc
import framingCheck as fc
import panelData

class MtrlData:

    mtrldata = []

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
        sql_select_query=f"""SELECT DISTINCT ON ("size") "type", description, "size", actual_thickness, actual_width
                    FROM elements
                    WHERE panelguid = '{sql_var}' AND description = 'Stud' AND type = 'Board'
                    ORDER BY "size" ASC;
                """       

        results = pgDB.query(sqlStatement=sql_select_query)
        pgDB.close()
        if len(results) == 1:            
            self.mrtldata = self.mdBuild(results[0])
        else:
            print("returned to many options")

        self.mdInsert()

    def mdBuild(self, studs): # This function will assemble the entry line of Material Data
        uiItemLength = self.panel.studHeight
        uiItemHeight = float(studs[3])
        uiItemThickness = float(studs[4])
        sMtrlCode = self.getMatCode(studs[2])
        uiOpCode = 0
        sPrinterWrite = 0	
        sType = 0
        uiItemID = studs[0]	
        sCADPath = 0
        sProjectName = 0	
        sItemName = self.panel.guid

        line = [uiItemLength, uiItemHeight, uiItemThickness, sMtrlCode, uiOpCode, sPrinterWrite, sType, uiItemID, sCADPath, sProjectName, sItemName]
        return line
    
    def getMatCode(self, studType): # returns material code for size of material (1: 2x4, 2:2x6)
        #NEED TO DETERMINE HOW TO GET STUD MATERIAL CODE
        pass

    def mdInsert(self, data): # Inserts "mtrldata" list into table "materialData"
    
        #send OpData to JobData table
        sql_JobData_query = '''
        INSERT INTO materialData(uiItemLength, uiItemHeight, uiItemThickness, sMtrlCode, uiOpCode, 
        sPrinterWrite, sType, uiItemID, sCADPath, sProjectName, sItemName)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
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
        #for item in OpData:
        #    jdQueryData.append((panelguid, item[0],item[1],item[2],item[3],item[4],
        #                        item[5],item[6],item[7],item[8],item[9],item[10],item[11]))

        #tmp = pgDB.querymany(sql_JobData_query,jdQueryData)

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
        self.panel = panel

        #self.plateInnerBottom = 1.5
        #self.plateInnerTop  = 1.5 + self.studHeight        



    def jdMain(self): # Job Data Main
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        panelguid = self.panel.guid
        sql_var = self.panel.guid
        #query relevant data from elements table
        sql_elemData_query = f'''
        SELECT elementguid, type, description, size, b1x,b1y,b2x,b2y,b3x,b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y
        FROM elements
        WHERE panelguid = '{sql_var}'
        ORDER BY b1x ASC;
        '''

        elemData = pgDB.query(sql_elemData_query)
        #counter for obj
        obj_count = 1
        #list of OpDatas
        OpData = []
        #loop through all elements in the panel
        inSubAssembly = False
        for elem in elemData:
            #convert to mm and:
            #list of [panelguid,elementguid,type,description,size,b1x,b1y,b2x,b2y,b3x,
            #                       b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,count]
            element = [panelguid,elem[0],elem[1],elem[2],elem[3],elem[4],elem[5] * 25.4,
                       elem[6] * 25.4,elem[7] * 25.4,elem[8] * 25.4,elem[9] * 25.4,
                       elem[10] * 25.4,elem[11] * 25.4,elem[12] * 25.4,elem[13] * 25.4,
                       elem[14] * 25.4,elem[15] * 25.4,elem[16] * 25.4,elem[17] * 25.4,
                       elem[18] * 25.4,elem[19] * 25.4,obj_count]

            if inSubAssembly == True and elem[1] != 'Sub-Assembly Board':
                inSubAssembly = False
                tmp = JobData.nailSubElement(subElements)
                for i,ct in enumerate(tmp):
                    if ct + 1 < len(tmp):
                        OpData.append(i)
                    obj_count = tmp[-1]


            #if the element isn't a sheet, sub-assembly board, top plate or bottom plate
            if elem[1] != 'Sheet' and elem[2] != 'BottomPlate' and elem[2] != 'TopPlate':
                if elem[1] != 'Sub-Assembly Board' and elem[1] != 'Sub Assembly':
                    #get opData for placeing the element
                    tmp = JobData.placeElement(element)
                    #Add to OpDatas and increase the count
                    OpData.append(tmp[0])
                    obj_count = tmp[1]
                    #Add get OpDatas for nailing
                    tmp = JobData.nailElement(element)
                    # loop through the OpDatas from the function and append to the list
                    # exclude the last list item because that is the counter
                    for i,j in enumerate(tmp):
                        if i+1 < len(tmp):
                            OpData.append(j)
                    #update counter
                    obj_count = tmp[-1]
                elif elem[1] == 'Sub Assembly':
                    #get opData for placeing the element
                    tmp = JobData.placeElement(element)
                    #Add to OpDatas and increase the count
                    OpData.append(tmp[0])
                    obj_count = tmp[1]

                    inSubAssembly = True
                    subElements = []
                elif elem[1] == 'Sub-Assembly Board':
                    if inSubAssembly == True:
                        subElements.append(element)
                    else:
                        print(f'ERROR: subassembly board outside of sub assembly, elementguid = {elem[0]}')
        #send OpData to JobData table
        sql_JobData_query = '''
        INSERT INTO JobData(panelguid, xpos, optext, opcode_fs, zpos_fs, ypos_fs, ssuppos_fs, 
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

        tmp = pgDB.querymany(sql_JobData_query,jdQueryData)
        #print the no. of rows modified
        print(tmp + ' rows modified')
        pgDB.close()

    def jdBuild(panelguid): # Job Data Build
        
        pass

    def placeElement(self,element):
        #list of [panelguid,elementguid,type,description,size,b1x,b1y,b2x,b2y,b3x,
        #                       b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,count]
        clear = fc.Clear()
        #empty list for [Xpos,OpText,OpCodeFS,ZposFS,YposFS,SSupPosFS,OpCodeMS,ZposMS,YposMS,SSupPosMS,IMG_NAME,OBJ_ID]
        OpJob = []
        #add X Pos from element
        OpJob.append(element[5])
        #list of bools for FS & MS containing [StudStop,Hammer,Multi-Device,Option,Autostud,Operator Confirm, Nailing]
        OpFS = [False,False,False,False,False,False,False]
        OpMS = [False,False,False,False,False,False,False]
        #check if the stud stops are clear
        if clear.Ss_FS(element[0],element[1]) == True:
            OpFS[0] = True
        
        if clear.Ss_MS(element[0],element[1]) == True:
            OpMS[0] = True
        #if element is a stud enable hammer and autostud
        if element[2] == 'Board' and element[3] == 'Stud':
            OpFS[1] = True
            OpFS[4] = True
            OpMS[1] = True
            OpMS[4] = True
            # if element is the first stud enable operator confirm
            if element[5] <= 1:
                OpFS[5] == True
                OpMS[5] == True
        #if element is a sub assembly
        elif element[2] == 'Sub-Assembly':
            # check if hammers are clear
            if clear.Hu_FS(element[0],element[1]) == True:
                OpFS[1] = True
            if clear.Hu_MS(element[0],element[1]) == True:
                OpMS[1] = True
            #set operator confirm
            OpFS[5] == True
            OpMS[5] == True
        #other element types? -> error?
        else:
            if clear.Hu_FS(element[0],element[1]) == True:
                OpFS[1] = True
            if clear.Hu_MS(element[0],element[1]) == True:
                OpMS[1] = True
            print(f'error with elementguid: {element[1]} \n Type unknown')
            
        #generate OpText and OpCodes from list of bools
        tmpFS = JobData.genOpCode(OpFS)
        tmpMS = JobData.genOpCode(OpMS)
        #list to append to OpJob & append it
        OpJobAppend = [tmpFS[0],tmpFS[1], 0, 0, 0, tmpMS[1], 0, 0, 0, 'ImgName', element[-1]]
        
        for i in OpJobAppend:
            OpJob.append(i)
        # increase OBJ_ID Count
        element[-1] += 1
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
            
        #remove trailing ' | ' from OpText string
        if opcode[0][-3] == ' ':
            opcode[0] = opcode[0][:-3]
        return opcode

    def nailElement(self,element):
        #list of [panelguid,elementguid,type,description,size,b1x,b1y,b2x,b2y,b3x,
        #                       b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,count]
        clear = fc.Clear
        #list of OpJobs for the current Element
        OpElement = []
        Zpos_2x4 = [19,70]
        Zpos_2x6 = [15,70,125]
        #list of bools for FS & MS containing [StudStop,Hammer,Multi-Device,Option,Autostud,Operator Confirm, Nailing]
        OpFS = [False,False,False,False,False,False,False]
        OpMS = [False,False,False,False,False,False,False]
        if element[4] == "2x4":
            ct = 0
            while ct < 2:
                OpJob = []
                #Xpos
                OpJob.append(element[5])
                #check if the stud stops are clear
                if clear.Ss_FS(element[0],element[1]) == True:
                    OpFS[0] = True

                if clear.Ss_MS(element[0],element[1]) == True:
                    OpMS[0] = True

                #if element is a stud enable hammer, autostud, and nailing
                if element[2] == 'Board' and element[3] == 'Stud':
                    OpFS[1] = True
                    OpFS[4] = True
                    OpFS[4] = True
                    OpFS[6] = True
                    OpMS[1] = True
                    OpMS[4] = True
                    OpMS[6] = True 
                #other element types? -> error?
                else:
                    if clear.Hu_FS(element[0],element[1]) == True:
                        OpFS[1] = True
                    if clear.Hu_MS(element[0],element[1]) == True:
                        OpMS[1] = True
                    print(f'error with elementguid: {element[1]} \n Type unknown')

                #generate OpText and OpCodes from list of bools
                tmpFS = self.genOpCode(OpFS)
                tmpMS = self.genOpCode(OpMS)
                #list to append to OpJob & append it
                OpJobAppend = [tmpFS[0],tmpFS[1],Zpos_2x4[ct], 0, 0,tmpMS[1],Zpos_2x4[ct],0, 0, 'ImgName', element[-1]]

                for i in OpJobAppend:
                    OpJob.append(i)
                # increase Nail position counter and OBJ_ID Counter
                ct += 1
                element[-1] += 1
                OpElement.append(OpJob)

        elif element[4] == "2x6":
            ct = 0
            while ct < 3:
                OpJob = []
                #Xpos
                OpJob.append(element[5])
                #check if the stud stops are clear
                if clear.Ss_FS(element[0],element[1]) == True:
                    OpFS[0] = True

                if clear.Ss_MS(element[0],element[1]) == True:
                    OpMS[0] = True

                #if element is a stud enable hammer and autostud
                if element[2] == 'Board' and element[3] == 'Stud':
                    OpFS[1] = True
                    OpFS[6] = True
                    OpMS[1] = True
                    OpMS[6] = True 
                #other element types? -> error?
                else:
                    if clear.Hu_FS(element[0],element[1]) == True:
                        OpFS[1] = True
                    if clear.Hu_MS(element[0],element[1]) == True:
                        OpMS[1] = True
                    print(f'error with elementguid: {element[1]} \n Type unknown')

                #generate OpText and OpCodes from list of bools
                tmpFS = self.genOpCode(OpFS)
                tmpMS = self.genOpCode(OpMS)
                #list to append to OpJob & append it
                OpJobAppend = [tmpFS[0],tmpFS[1],Zpos_2x6[ct], 0, 0,tmpMS[1],Zpos_2x6[ct],0, 0, 'ImgName', element[-1]]

                for i in OpJobAppend:
                    OpJob.append(i)
                # increase Nail position counter and OBJ_ID Counter
                ct += 1
                element[-1] += 1
                OpElement.append(OpJob)

        OpElement.append(element[-1])
        # Return OpJob and updated count
        return(OpElement)
        

    def nailSubElement(self,elementList):
        clear = fc.Clear
        TopPlate = 38.1 + self.studHeight
        BottomPlate = 38.1
        OpFS = [False,False,False,False,False,False,False]
        OpMS = [False,False,False,False,False,False,False]
        OpJobList = []
        #list of [panelguid,elementguid,type,description,size,b1x,b1y,b2x,b2y,b3x,b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,count]
        #        [   0     ,      1    ,  2 ,    3      ,  4 , 5 , 6 , 7 , 8 , 9 , 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]
        for elem in elementList:
            #Sub Assembly Element is only touching Top plate
            if elem[16] == TopPlate and elem[14] != BottomPlate:

                if clear.Ss_MS(elem[1]) == True:
                    OpMS[0] = True

                if clear.Hu_MS(elem[1]) == True:
                    OpMS[1] = True

                OpMS[6] = True

                #Is the element in the sub assembly normal stud orientation
                if (elem[17] - elem[13]) < 2:
                    if elem[4] == "2x4":
                        ct = 0
                        while ct < 2:
                            OpJob = [] 
                            #Xpos
                            OpJob.append(elem[5])
                            #generate OpText and OpCodes from list of bools
                            tmpFS = self.genOpCode(OpFS)
                            tmpMS = self.genOpCode(OpMS)
                            #list to append to OpJob & append it
                            OpJobAppend = [tmpFS[0],0,0, 0, 0,tmpMS[1],self.Zpos_2x4[ct],0, 0, 'ImgName', 0]
                            for i in OpJobAppend:
                                OpJob.append(i)
                            ct += 1
                            OpJobList.append(OpJob)


                    if elem[4] == "2x6":
                        ct = 0
                        while ct < 3:
                            OpJob = []
                            #Xpos
                            OpJob.append(elem[5])
                            #generate OpText and OpCodes from list of bools
                            tmpFS = self.genOpCode(OpFS)
                            tmpMS = self.genOpCode(OpMS)
                            #list to append to OpJob & append it
                            OpJobAppend = [tmpFS[0],0,0, 0, 0,tmpMS[1],self.Zpos_2x6[ct],0, 0, 'ImgName', 0]
                            for i in OpJobAppend:
                                OpJob.append(i)
                            ct += 1
                            OpJobList.append(OpJob)
                

                #Non Header Orientation along Top Plate (Flat against Top Plate)
                elif (elem[16] - elem[14]) < 2:
                    # b3x - b1x 
                    Length_of_Header = elem[17] - elem[13]
                    Number_of_NailSpacings = Length_of_Header/609.6
                    if elem[4] == "2x4":
                        NailCounter = 0
                        while NailCounter < Number_of_NailSpacings:
                            ct = 0
                            while ct < 2:
                                OpJob = []  
                                #Xpos
                                OpJob.append(elem[5] + (NailCounter*609.6))
                                #generate OpText and OpCodes from list of bools
                                tmpFS = self.genOpCode(OpFS)
                                tmpMS = self.genOpCode(OpMS)
                                #list to append to OpJob & append it
                                OpJobAppend = [tmpFS[0],0,0, 0, 0,tmpMS[1],self.Zpos_2x4[ct],0, 0, 'ImgName', 0]
                                for i in OpJobAppend:
                                    OpJob.append(i)
                                ct += 1
                                OpJobList.append(OpJob)
                            NailCounter += 1

                    if elem[4] == "2x6":
                        NailCounter = 0
                        while NailCounter < Number_of_NailSpacings: 
                            ct = 0
                            while ct < 3:
                                OpJob = []
                                #Xpos
                                OpJob.append(elem[5] + (NailCounter*609.6))
                                #generate OpText and OpCodes from list of bools
                                tmpFS = self.genOpCode(OpFS)
                                tmpMS = self.genOpCode(OpMS)
                                #list to append to OpJob & append it
                                OpJobAppend = [tmpFS[0],0,0, 0, 0,tmpMS[1],self.Zpos_2x6[ct],0, 0, 'ImgName', 0]
                                for i in OpJobAppend:
                                    OpJob.append(i)
                                ct += 1
                                OpJobList.append(OpJob)

                            NailCounter += 1
                #Header Orientation
                elif (elem[16] - elem[14]) > 2:
                    # b3x - b1x 
                    Length_of_Header = elem[17] - elem[13]
                    Number_of_NailSpacings = Length_of_Header/609.6
                    NailCounter = 0
                    Zpos = (elem[6] - elem[8])/2
                    while NailCounter < Number_of_NailSpacings:  
                        ct = 0
                        while ct < 3:
                            OpJob = []
                            #Xpos
                            OpJob.append(elem[5] + (NailCounter*609.6))
                            #generate OpText and OpCodes from list of bools
                            tmpFS = self.genOpCode(OpFS)
                            tmpMS = self.genOpCode(OpMS)
                            #list to append to OpJob & append it
                            OpJobAppend = [tmpFS[0],0,0, 0, 0,tmpMS[1],Zpos,0, 0, 'ImgName', 0]
                            for i in OpJobAppend:
                                OpJob.append(i)
                            ct += 1
                            OpJobList.append(OpJob)
                        NailCounter += 1



            # Sub Assembly Element is only Touching Bottom Plate
            if elem[14] == BottomPlate and elem[16] != TopPlate:

                if clear.Ss_FS(elem[1]) == True:
                    OpMS[0] = True

                if clear.Hu_FS(elem[1]) == True:
                    OpMS[1] = True

                OpFS[6] = True
                
                #Is the element in the sub assembly normal stud orientation
                if (elem[17] - elem[13]) < 2: 
                    if elem[4] == "2x4": 
                        ct = 0
                        while ct < 2:
                            OpJob = []
                            #Xpos
                            OpJob.append(elem[5])
                            #generate OpText and OpCodes from list of bools
                            tmpFS = self.genOpCode(OpFS)
                            tmpMS = self.genOpCode(OpMS)
                            #list to append to OpJob & append it
                            OpJobAppend = [tmpFS[0],tmpFS[1],self.Zpos_2x4[ct], 0, 0,0,0,0, 0, 'ImgName', 0]
                            for i in OpJobAppend:
                                OpJob.append(i)
                            ct += 1
                            OpJobList.append(OpJob)


                    if elem[4] == "2x6":
                        ct = 0
                        while ct < 3:
                            OpJob = []
                            #Xpos
                            OpJob.append(elem[5])
                            #generate OpText and OpCodes from list of bools
                            tmpFS = self.genOpCode(OpFS)
                            tmpMS = self.genOpCode(OpMS)
                            #list to append to OpJob & append it
                            OpJobAppend = [tmpFS[0],tmpFS[1],self.Zpos_2x6[ct], 0, 0,0,0,0, 0, 'ImgName', 0]
                            for i in OpJobAppend:
                                OpJob.append(i)
                            ct += 1
                            OpJobList.append(OpJob)
                

                #Non Header Orientation along Top Plate (Flat against Top Plate)
                elif (elem[16] - elem[14]) < 2:
                    # b3x - b1x 
                    Length_of_Header = elem[17] - elem[13]
                    Number_of_NailSpacings = Length_of_Header/609.6
                    if elem[4] == "2x4":
                        NailCounter = 0
                        while NailCounter < Number_of_NailSpacings:  
                            ct = 0
                            while ct < 2:
                                OpJob = []
                                #Xpos
                                OpJob.append(elem[5] + (NailCounter*609.6))
                                #generate OpText and OpCodes from list of bools
                                tmpFS = self.genOpCode(OpFS)
                                tmpMS = self.genOpCode(OpMS)
                                #list to append to OpJob & append it
                                OpJobAppend = [tmpFS[0],tmpFS[1],self.Zpos_2x4[ct],0,0,0,0,0,0, 'ImgName', 0]

                                for i in OpJobAppend:
                                    OpJob.append(i)
                                ct += 1
                                OpJobList.append(OpJob)
                            NailCounter += 1

                    if elem[4] == "2x6":
                        NailCounter = 0
                        while NailCounter < Number_of_NailSpacings: 
                            ct = 0
                            while ct < 3:
                                OpJob = []
                                #Xpos
                                OpJob.append(elem[5] + (NailCounter*609.6))
                                #generate OpText and OpCodes from list of bools
                                tmpFS = self.genOpCode(OpFS)
                                tmpMS = self.genOpCode(OpMS)
                                #list to append to OpJob & append it
                                OpJobAppend = [tmpFS[0],tmpFS[1],self.Zpos_2x6[ct],0,0,0,0,0,0, 'ImgName', 0]

                                for i in OpJobAppend:
                                    OpJob.append(i)
                                ct += 1
                                OpJobList.append(OpJob)
                            NailCounter += 1

                #Header Orientation
                elif (elem[16] - elem[14]) > 2:
                    # b3x - b1x 
                    Length_of_Header = elem[17] - elem[13]
                    Number_of_NailSpacings = Length_of_Header/609.6
                    NailCounter = 0
                    Zpos = (elem[6] - elem[8])/2
                    while NailCounter < Number_of_NailSpacings:  
                        ct = 0
                        while ct < 3:
                            OpJob = []
                            #Xpos
                            OpJob.append(elem[5] + (NailCounter*609.6))
                            #generate OpText and OpCodes from list of bools
                            tmpFS = self.genOpCode(OpFS)
                            tmpMS = self.genOpCode(OpMS)
                            #list to append to OpJob & append it
                            OpJobAppend = [tmpFS[0],tmpFS[1],Zpos,0,0,0,0,0,0, 'ImgName', 0]

                            for i in OpJobAppend:
                                OpJob.append(i)
                            ct += 1
                            OpJobList.append(OpJob)
                        NailCounter += 1

            # Sub Assembly Element is Touching Top and Bottom Plate
            if elem[14] == BottomPlate and elem[16] == TopPlate:

                if clear.Ss_FS(elem[1]) == True:
                    OpMS[0] = True

                if clear.Hu_FS(elem[1]) == True:
                    OpMS[1] = True

                OpFS[6] = True

                if clear.Ss_MS(elem[1]) == True:
                    OpMS[0] = True

                if clear.Hu_MS(elem[1]) == True:
                    OpMS[1] = True

                OpMS[6] = True
                
                #Is the element in the sub assembly normal stud orientation
                if (elem[17] - elem[13]) < 2: 
                    if elem[4] == "2x4":
                        ct = 0
                        while ct < 2:
                            OpJob = []
                            #Xpos
                            OpJob.append(elem[5])
                            #generate OpText and OpCodes from list of bools
                            tmpFS = self.genOpCode(OpFS)
                            tmpMS = self.genOpCode(OpMS)
                            #list to append to OpJob & append it
                            OpJobAppend = [tmpFS[0],tmpFS[1],self.Zpos_2x4[ct], 0, 0,tmpMS[1],self.Zpos_2x4[ct],0, 0, 'ImgName', 0]
                            for i in OpJobAppend:
                                OpJob.append(i)
                            OpJobList.append(OpJob)
                            ct += 1

                    if elem[4] == "2x6":
                        
                        ct = 0
                        while ct < 3:
                            OpJob = []
                            #Xpos
                            OpJob.append(elem[5])
                            #generate OpText and OpCodes from list of bools
                            tmpFS = self.genOpCode(OpFS)
                            tmpMS = self.genOpCode(OpMS)
                            #list to append to OpJob & append it
                            OpJobAppend = [tmpFS[0],tmpFS[1],self.Zpos_2x6[ct], 0, 0,tmpMS[1],self.Zpos_2x6[ct],0, 0, 'ImgName', 0]
                            for i in OpJobAppend:
                                OpJob.append(i)
                            OpJobList.append(OpJob)
                            ct += 1

        OplistSorted = sorted(OpJobList,key=lambda var:(var[0],var[3],var[7]))

        count = elementList[0][-1]
        
        for OpJob in OplistSorted:
            OpJob[-1] = count
            count += 1
        OplistSorted.append(count)
        # Return OpJob and updated count
        return(OplistSorted)
    
if __name__ == "__main__":
    panel = panelData.Panel("4a4909bf-f877-4f2f-8692-84d7c6518a2d")
    matData = MtrlData(panel)
    jobdata = JobData(panel)

