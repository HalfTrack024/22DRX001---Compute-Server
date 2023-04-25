import dataBaseConnect as dbc
import framingCheck as fc
import panelData

class missionData_RBC:

    missionID : int
    info_01 : float
    info_02 : float
    info_03 : float
    info_04 : float
    info_05 : float
    info_06 : float
    info_07 : float
    info_08 : float 
    info_09 : float
    info_10 : int
    info_11 : int

class BoardData_RBC:
    board : missionData_RBC
    boardPlace : missionData_RBC 
    Fastening : list[missionData_RBC]   

class BoardData_RBC:
    board : list[BoardData_RBC]
    missions : list[missionData_RBC]


    def __init__(self) -> None:
        pass

class Layer:



class RunData:

    Miss

    def __init__(self):
        pass

    def rdMain(self):
        pass

    def getPanel(self):
        pass

    def panelReq(self):
        pass

    def tempFasten(self):
        pass
