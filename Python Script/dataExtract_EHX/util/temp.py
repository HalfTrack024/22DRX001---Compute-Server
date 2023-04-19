def panelOpData(panelguid):
    #query relevant data from elements table
    sql_elemData_query = f'''
    SELECT elementguid, type, description, size, b1x,b1y,b2x,b2y,b3x,b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y
    FROM elements
    WHERE panelguid = '{panelguid}'
    ORDER BY b1x ASC
    '''

    elemData = pgDB.query(sql_elemData_query)
    #counter for obj
    obj_count = 1
    OpData = []

    for elem in elemData:
        if elem[1] != 'Sheet' and elem[2] != 'BottomPlate' and elem[2] != 'TopPlate' and elem[1] != 'Sub-Assembly Board':
            tmp = placeElement(elem[1],elem[2],obj_count,elem[4],elem[5],elem[6],elem[7],elem[8],elem[9],elem[10],elem[11],elem[12],elem[13],elem[14],elem[15],elem[16],elem[17],elem[18],elem[19],panelguid,elem[0])
            OpData.append(tmp[0])
            tmp = nailElement(elem[1],elem[2], elem[3], obj_count,elem[4],elem[5],elem[6],elem[7],elem[8],elem[9],elem[10],elem[11],elem[12],elem[13],elem[14],elem[15],elem[16],elem[17],elem[18],elem[19],panelguid,elem[0])
            for i in tmp:
                OpData.append(i)
    #send OpData to a DB

def placeElement(type,desc,count,b1x,b1y,b2x,b2y,b3x,b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,panelguid,elemguid):
    OpJob = []
    OpJob.append(b1x)
    OpFS = [False,False,False,False,False,False,False]
    OpMS = [False,False,False,False,False,False,False]

    if clear.Ss_FS(panelguid,elemguid) == True:
        OpFS[0] = True
    
    if clear.Ss_MS(panelguid,elemguid) == True:
        OpMS[0] = True
    
    if type == 'Board' and desc == 'Stud':
        OpFS[1] = True
        OpFS[4] = True
        OpMS[1] = True
        OpMS[4] = True
        if b1x <= 1:
            OpFS[5] == True
            OpMS[5] == True
    elif type == 'Sub-Assembly':
        if clear.Hu_FS(panelguid,elemguid) == True:
            OpFS[1] = True
        if clear.Hu_MS(panelguid,elemguid) == True:
            OpMS[1] = True
        OpFS[5] == True
        OpMS[5] == True
    else:
        if clear.Hu_FS(panelguid,elemguid) == True:
            OpFS[1] = True
        if clear.Hu_MS(panelguid,elemguid) == True:
            OpMS[1] = True
        

    tmpFS = genOpCode(OpFS)
    tmpMS = genOpCode(OpMS)

    OpJobAppend = [tmpFS[0],tmpFS[1], 0, 0, 0, tmpMS[1], 0, 0, 0, 'ImgName', count]
    
    for i in OpJobAppend:
        OpJob.append(i)

    count += 1

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

#placeholder Function
def nailElement(tmp):
    pass