import dataBaseConnect as dbc
import framingCheck as fc

class Panel:
    plateInnerBottom = 0
    plateInnerTop = 0
    def __init__(self, panelguid):
        # Open Database Connection
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()

        sql_var= panelguid
        sql_select_query=f"""
                        SELECT thickness, studheight, walllength, category
                        FROM panel
                        WHERE panelguid = '{sql_var}';
                        """
        #
        results = pgDB.query(sqlStatement=sql_select_query)
        #dbc.printResult(results)
        pgDB.close()
        #assign results of query to variables
        self.guid = panelguid
        self.panelThickness = float(results[0][0])
        Panel.studHeight = float(results[0][1])
        self.panelLength = float(results[0][2])
        self.catagory = results[0][3]

        self.plateInnerBottom = 1.5
        self.plateInnerTop  = 1.5 + self.studHeight

    def getPanel(self, panelGUID):
        pass
    
    def genOPCode(OpIn):
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
    
if __name__ == "__main__":
    credentials = dbc.getCred()
    pgDB = dbc.DB_Connect(credentials)
    pgDB.open()
    #get panel details dimensions
    sql_var= "4a4909bf-f877-4f2f-8692-84d7c6518a2d"
    sql_select_query=f"""SELECT "label", height, thickness, studheight, walllength
                        FROM panel
                        WHERE panelguid='{sql_var}';
                    """
    
    results = pgDB.query(sqlStatement=sql_select_query)
    print(type(results[0][4]))
    #initialize Panel
    itterPanel = Panel(results)
    sql_select_query=f"""SELECT elementguid, "type", description, "size", b1x
                        FROM elements
                        WHERE panelguid = '{sql_var}' AND e1y = 1.5
                        ORDER BY b1x ASC;
                    """
    results = pgDB.query(sqlStatement=sql_select_query)
    
    clear = fc.Clear()
    oplistFS = [False,False,False,False,False,False,False]
    oplistMS = [False,False,False,False,False,False,False]
    #still need to add the parameters to pass to the functions below
    if clear.studStopFS() == True: 
        #add for when stud stop is allowed
        oplistFS[0] = True
        pass
    if clear.hammerFS() == True:
        #add for when hammer is allowed
        oplistFS[1] = True
        pass
    if clear.studStopMS() == True:
        #add for when stud stop is allowed
        oplistMS[0] = True
        pass
    if clear.hammerMS() == True:
        #add for when hammer is allowed
        oplistMS[1] = True
        if (oplistFS[0] == True) and (oplistFS[1] == True) and (oplistMS[0] == True):
            oplistMS[4] = True
            oplistFS[4] = True
        pass
    
    opcodeFS = Panel.genOPCode(oplistFS)
    opcodeMS = Panel.genOPCode(oplistMS)
    results = pgDB.query(sqlStatement=sql_select_query)
    dbc.printResult(data=results)
    results = pgDB.query(sqlStatement=sql_select_query)
    pgDB.close()