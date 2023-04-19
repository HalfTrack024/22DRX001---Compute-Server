from util import dataBaseConnect as dbc
from util import framingCheck as fc
import panelData

class MtrlData:

    def mdMain():
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

    def __init__(self, panelguid, panelData):
        self.pdData = panelData.Panel
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        #
        sql_var= " "
        sql_select_query=f"""
                        SELECT thickness, studheight, walllength, category
                        FROM panel
                        WHERE panelguid = '{panelguid}';
                        """
        
        results = pgDB.query(sql_select_query)
        dbc.printResult(results)
        #assign results of query to variables
        self.panelGuid = panelguid
        self.panelThickness = float(results[0][1])
        self.studHeight = float(results[1][1])
        self.panelLength = float(results[2][1])
        self.catagory = float(results[3][1])

        #self.plateInnerBottom = 1.5
        #self.plateInnerTop  = 1.5 + self.studHeight        

        #Always close the connection after all queries are complete
        pgDB.close()

    def jdMain(self, panelguid): # Job Data Main
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()

        #query relevant data from elements table
        sql_elemData_query = f'''
        SELECT elementguid, type, description, size, b1x,b1y,b2x,b2y,b3x,b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y
        FROM elements
        WHERE panelguid = '{panelguid}'
        ORDER BY b1x ASC;
        '''

        elemData = pgDB.query(sql_elemData_query)
        #counter for obj
        obj_count = 1
        #list of OpDatas
        OpData = []
        #loop through all elements in the panel
        for elem in elemData:
            #if the element isn't a sheet, sub-assembly board, top plate or bottom plate
            if elem[1] != 'Sheet' and elem[2] != 'BottomPlate' and elem[2] != 'TopPlate' and elem[1] != 'Sub-Assembly Board':
                #get opData for placeing the element
                tmp = JobData.placeElement(elem[1],elem[2],obj_count,elem[4],elem[5],elem[6],elem[7],elem[8],
                                           elem[9],elem[10],elem[11],elem[12],elem[13],elem[14],elem[15],elem[16],
                                           elem[17],elem[18],elem[19],panelguid,elem[0])
                #Add to OpDatas and increase the count
                OpData.append(tmp[0])
                obj_count = tmp[1]
                #Add get OpDatas for nailing
                tmp = JobData.nailElement(elem[1],elem[2], elem[3], obj_count,elem[4],elem[5],elem[6],elem[7],
                                          elem[8],elem[9],elem[10],elem[11],elem[12],elem[13],elem[14],elem[15],
                                          elem[16],elem[17],elem[18],elem[19],panelguid,elem[0])
                # loop through the OpDatas from the function and append to the list
                # exclude the last list item because that is the counter
                for i,j in enumerate(tmp):
                    if i+1 < len(tmp):
                        OpData.append(j)
                #update counter
                obj_count = tmp[-1]
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
        jdQueryData = []
        for item in OpData:
            jdQueryData.append((panelguid, item[0],item[1],item[2],item[3],item[4],
                                item[5],item[6],item[7],item[8],item[9],item[10],item[11]))

        pgDB.querymany(sql_JobData_query,jdQueryData)
        pgDB.close()

    def jdBuild(panelguid): # Job Data Build
        
        pass

    def placeElement(type,desc,count,b1x,b1y,b2x,b2y,b3x,b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,panelguid,elemguid):
        clear = fc.Clear()
        #empty list for [Xpos,OpText,OpCodeFS,ZposFS,YposFS,SSupPosFS,OpCodeMS,ZposMS,YposMS,SSupPosMS,IMG_NAME,OBJ_ID]
        OpJob = []
        #add X Pos from element
        OpJob.append(b1x)
        #list of bools for FS & MS containing [StudStop,Hammer,Multi-Device,Option,Autostud,Operator Confirm, Nailing]
        OpFS = [False,False,False,False,False,False,False]
        OpMS = [False,False,False,False,False,False,False]
        #check if the stud stops are clear
        if clear.Ss_FS(panelguid,elemguid) == True:
            OpFS[0] = True
        
        if clear.Ss_MS(panelguid,elemguid) == True:
            OpMS[0] = True
        #if element is a stud enable hammer and autostud
        if type == 'Board' and desc == 'Stud':
            OpFS[1] = True
            OpFS[4] = True
            OpMS[1] = True
            OpMS[4] = True
            # if element is the first stud enable operator confirm
            if b1x <= 1:
                OpFS[5] == True
                OpMS[5] == True
        #if element is a sub assembly
        elif type == 'Sub-Assembly':
            # check if hammers are clear
            if clear.Hu_FS(panelguid,elemguid) == True:
                OpFS[1] = True
            if clear.Hu_MS(panelguid,elemguid) == True:
                OpMS[1] = True
            #set operator confirm
            OpFS[5] == True
            OpMS[5] == True
        #other element types? -> error?
        else:
            if clear.Hu_FS(panelguid,elemguid) == True:
                OpFS[1] = True
            if clear.Hu_MS(panelguid,elemguid) == True:
                OpMS[1] = True
            print(f'error with elementguid: {elemguid}')
            
        #generate OpText and OpCodes from list of bools
        tmpFS = JobData.genOpCode(OpFS)
        tmpMS = JobData.genOpCode(OpMS)
        #list to append to OpJob & append it
        OpJobAppend = [tmpFS[0],tmpFS[1], 0, 0, 0, tmpMS[1], 0, 0, 0, 'ImgName', count]
        
        for i in OpJobAppend:
            OpJob.append(i)
        # increase OBJ_ID Count
        count += 1
        # Return OpJob and updated count
        return(OpJob,count)
    
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

    def nailElement(self,type,desc,size, count,b1x,b1y,b2x,b2y,b3x,b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,panelguid,elemguid):
        Zpos_2x4 = [0.75,2.75]
        Zpos_2x6 = [0.75,2.75,4.75]
        #list of bools for FS & MS containing [StudStop,Hammer,Multi-Device,Option,Autostud,Operator Confirm, Nailing]
        OpFS = [False,False,False,False,False,False,False]
        OpMS = [False,False,False,False,False,False,False]
        if size == "2x4":
            ct = 0
            while ct < 2:
                OpJob = [] 
                #Xpos
                OpJob.append(b1x)
                #check if the stud stops are clear
                if clear.Ss_FS(panelguid,elemguid) == True:
                    OpFS[0] = True

                if clear.Ss_MS(panelguid,elemguid) == True:
                    OpMS[0] = True

                #if element is a stud enable hammer and autostud
                if type == 'Board' and desc == 'Stud':
                    OpFS[1] = True
                    OpFS[6] = True
                    OpMS[1] = True
                    OpMS[6] = True 

                #if element is a sub assembly
                elif type == 'Sub-Assembly':
                    #SubTopPlate = 38.1 + self.studHeight
                    #SubBottomPlate = 38.1
                    # check if hammers are clear
                    if clear.Hu_FS(panelguid,elemguid) == True:
                        OpFS[1] = True
                    if clear.Hu_MS(panelguid,elemguid) == True:
                        OpMS[1] = True

                    #if e2y == SubTopPlate:
                    #    if (e1x-e4x) < 2:
                    #            ZposMS = Zpos_2x4[ct]
                    #    elif (b1y-b2y) < 2:
                    #        ZposMS = Zpos_2x4[ct]


                    #if e1y == SubBottomPlate:
                    #   if (e1x-e4x) < 2:
                    #        ZposMS = Zpos_2x4[ct]

                #other element types? -> error?
                else:
                    if clear.Hu_FS(panelguid,elemguid) == True:
                        OpFS[1] = True
                    if clear.Hu_MS(panelguid,elemguid) == True:
                        OpMS[1] = True
                    print(f'error with elementguid: {elemguid}')

                #generate OpText and OpCodes from list of bools
                tmpFS = genOpCode(OpFS)
                tmpMS = genOpCode(OpMS)
                #list to append to OpJob & append it
                OpJobAppend = [tmpFS[0],tmpFS[1],Zpos_2x4[ct], 0, 0,tmpMS[1],Zpos_2x4[ct],0, 0, 'ImgName', count]

                for i in OpJobAppend:
                    OpJob.append(i)
                # increase Nail position counter and OBJ_ID Counter
                ct += 1
                count += 1

                
        if size == "2x6":
            ct = 0
            while ct < 3:
                OpJob = []
                #Xpos
                OpJob.append(b1x)
                #check if the stud stops are clear
                if clear.Ss_FS(panelguid,elemguid) == True:
                    OpFS[0] = True

                if clear.Ss_MS(panelguid,elemguid) == True:
                    OpMS[0] = True

                #if element is a stud enable hammer and autostud
                if type == 'Board' and desc == 'Stud':
                    OpFS[1] = True
                    OpFS[6] = True
                    OpMS[1] = True
                    OpMS[6] = True 

                #if element is a sub assembly
                elif type == 'Sub-Assembly':
                    # check if hammers are clear
                    if clear.Hu_FS(panelguid,elemguid) == True:
                        OpFS[1] = True
                    if clear.Hu_MS(panelguid,elemguid) == True:
                        OpMS[1] = True

                #other element types? -> error?
                else:
                    if clear.Hu_FS(panelguid,elemguid) == True:
                        OpFS[1] = True
                    if clear.Hu_MS(panelguid,elemguid) == True:
                        OpMS[1] = True
                    print(f'error with elementguid: {elemguid}')

                #generate OpText and OpCodes from list of bools
                tmpFS = genOpCode(OpFS)
                tmpMS = genOpCode(OpMS)
                #list to append to OpJob & append it
                OpJobAppend = [tmpFS[0],tmpFS[1],Zpos_2x6[ct], 0, 0,tmpMS[1],Zpos_2x6[ct],0, 0, 'ImgName', count]

                for i in OpJobAppend:
                    OpJob.append(i)
                # increase Nail position counter and OBJ_ID Counter
                ct += 1
                count += 1

        # Return OpJob and updated count
        return(OpJob,count)

    

 

if __name__ == "__main__":
    Panel = JobData("4a4909bf-f877-4f2f-8692-84d7c6518a2d")
