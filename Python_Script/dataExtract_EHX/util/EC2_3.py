import dataBaseConnect as dbc
import framingCheck as fc
import panelData
import runData_Helper as rdh


class RunData:

    def __init__(self, panel : panelData.Panel):
        self.panel = panel

        dbc.credentials()
        pgDB = dbc.DB_Connect()
        pgDB.open()
        

        

    def rdEC2_Main(self):
        pass

    def rdEC3_Main(self):
        pass

    def getPanel(self):
        pass

    def panelReq(self):
        pass

    def tempFasten(self):
        pass



