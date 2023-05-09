import dataBaseConnect as dbc
import panelData
import runData_Helper as rdh
from Parameters import Parameters
import panelData

    

class RunData:
    refMatTypes = ["OSB", "Dow", "ZIP", "DENSGLAS","SOUNDBOARD","Neopor"]
    fastenTypes : list[str]
    materialTypes : list[str]
    layers : list[float]


    def __init__(self, panel : panelData.Panel):
        self.panel = panel

        ec2TabNames = ["Stud Inverter speeds","Nail Tool MS","Axis LBH","Axis HSP","Computer Settings",
            "Joint Rules","Studfeeder","Axis Width","Axis GUM","Axis GUF","Axis NPM","Positions",
            "Nail Tool FS","Stud stack positions","Axis NPF","Axis WAN","Axis SPR",
            "Program Settings And Parameters","Device Offsets","Program Settings and Parameters"]
        self.ec2Parm = Parameters(ec2TabNames)
        ec3TabNames = ["Stud Inverter speeds","Nail Tool MS","Axis LBH","Axis HSP","Computer Settings",
            "Joint Rules","Studfeeder","Axis Width","Axis GUM","Axis GUF","Axis NPM","Positions",
            "Nail Tool FS","Stud stack positions","Axis NPF","Axis WAN","Axis SPR",
            "Program Settings And Parameters","Device Offsets","Program Settings and Parameters"]
        self.ec3Parm = Parameters(ec3TabNames)        
        
        layers : list[rdh.BoardData_RBC]

        self.rdMain() # Main Call to Programs
        
    def rdMain(self): #Main Call for Run Data. 
                # Open Database Connection
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        sql_var1= self.panel.guid
        sql_select_query=f"""
                        SELECT "size", actual_thickness, materialdesc, b1x, b1y, b2y, e1y, e2y
                        FROM cad2fab.system_elements
                        where panelguid = '{sql_var1}' AND "type" = 'Sheet'
                        order by b1x, e1y;
                        """        
        #
        results = pgDB.query(sqlStatement=sql_select_query) 
        pgDB.close()

        # for sheet in results:
        #     self.getMaterials(sheet)

        #self.rdEC2_Main()
        #self.rdEC3_Main()


    def rdEC2_Main(self): #Main Call to assign what work will be allowed to complete on EC2
        lvl20 = self.ec2Parm.getParm("Programs Settings and Parameters", "Run Level 20 missions (True/False)")
        lvl30 = self.ec2Parm.getParm("Programs Settings and Parameters", "Run Level 30 missions (True/False)")
        lvl40 = self.ec2Parm.getParm("Programs Settings and Parameters", "Run Level 40 missions (True/False)")

        if lvl20: #Applying Sheathing
            for layer in self.layers:
                self.getSheets(layer)

        if lvl30: #Fastening
            self.getFastener()
        
        if lvl40: #Milling CutOuts
            self.getRoughOut()


    def rdEC3_Main(self): #Main Call to assign what work will be allowed to complete on EC3
        lvl20 = self.ec3Parm.getParm("Programs Settings and Parameters", "Run Level 20 missions (True/False)")
        lvl30 = self.ec3Parm.getParm("Programs Settings and Parameters", "Run Level 30 missions (True/False)")
        lvl40 = self.ec3Parm.getParm("Programs Settings and Parameters", "Run Level 40 missions (True/False)")

        if lvl20:
            self.getSheets(0)

        if lvl30:
            self.getFastener()
        
        if lvl40:
            self.getRoughOut()


    def getMaterial(self, sheet):
        #Board Pick
        mat : str = sheet[2]
        for reftype in self.refMatTypes:        
            if reftype in mat:
                if self.materialTypes.count > 0:
                    if not reftype in self.materialTypes:
                        self.materialTypes.append(reftype)
                    if not float(sheet[4]) in self.layers:
                        self.layers.append(float(sheet[1]))
                else:
                    self.materialTypes.append(reftype)
                        

            
    def getSheets(self, layer): #This fucntion will load the sheets of Material to the 
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
        boards = list[rdh.BoardData_RBC]
        for sheet in results:
            sheet = sheet[0]
            boardData = rdh.BoardData_RBC

            # Board Pick
            board = rdh.missionData_RBC
            board.missionID = 400
            board.info_01 = sheet['e1x'] # e1x
            board.info_02 = sheet['e1y'] # e1y
            board.info_03 = sheet['actual_width']
            board.info_04 = sheet['e2y']
            board.info_05 = sheet['actual_thickness']
            board.info_06 = 1 #TBD got to get panel thickness
            board.info_11 = self.getMaterial(sheet['materialdesc'])
            board.info_12 = getStack(board.info_11)
            
            boardData.boardPick = board

            # Board Place
            board = rdh.missionData_RBC
            board.missionID = self.fastenTypes
            board.info_01 = sheet['e1x'] # e1x
            board.info_02 = sheet['e1y'] # e1y
            board.info_03 = 0
            board.info_04 = 0
            board.info_05 = sheet['actual_thickness']
            board.info_06 = 1 #TBD got to get panel thickness
            board.info_11 = self.getMaterial(sheet['materialdesc'])
            board.info_12 = getStack(board.info_11)
            
            # Fastening
            
            
            boards.append()




    def getFastener(self):
        pass

    def getRoughOut(self):
        pass         

        
def getStack():
    pass




if __name__ == "__main__":
    panel = panelData.Panel("4a4909bf-f877-4f2f-8692-84d7c6518a2d")
    sheeting = RunData(panel)
    sheeting.getSheets(0)

