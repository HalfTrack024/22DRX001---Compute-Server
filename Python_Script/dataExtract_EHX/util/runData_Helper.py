import dataBaseConnect as dbc

class missionData_RBC:
    # Base Class of a mission statement that is required
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
        dbc.credentials()
        pgDB = dbc.DB_Connect()
        pgDB.open()
        
        self.centerPos = 0