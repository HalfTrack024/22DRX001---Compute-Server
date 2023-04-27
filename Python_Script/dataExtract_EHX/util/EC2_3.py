import dataBaseConnect as dbc
import framingCheck as fc
import panelData
import runData_Helper as rdh
from Parameters import Parameters


class RunData:

    def __init__(self, panel : panelData.Panel):
        self.panel = panel

        dbc.credentials()
        pgDB = dbc.DB_Connect()
        pgDB.open()

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
        self.ec2Parm.
        layers : list[rdh.BoardData_RBC]
        

    def rdEC2_Main(self):
        pass

    def rdEC3_Main(self):
        pass

    def 

    def getPanel(self):
        pass

    def panelReq(self):
        pass

    def tempFasten(self):
        pass


if __name__ == "__main__":
