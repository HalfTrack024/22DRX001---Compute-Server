
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
    info_12 : int

class BoardData_RBC:
    boardPick : missionData_RBC
    boardPlace : missionData_RBC 
    Fastening : list[missionData_RBC]   

class Layer_RBC:
    board : list[BoardData_RBC]
    missions : list[missionData_RBC]


