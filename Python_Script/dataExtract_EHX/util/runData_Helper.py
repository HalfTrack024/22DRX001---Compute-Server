import json

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
    info_12 : int
    
    def __init__(self, missionID):
        self.missionID = missionID

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)
    
    def setInfo(self, info : list):
        self.info_01 = info[0]
        self.info_02 = info[1]
        self.info_03 = info[2]
        self.info_04 = info[3]
        self.info_05 = info[4]
        self.info_06 = info[5]
        self.info_07 = info[6]
        self.info_08 = info[7]
        self.info_09 = info[8]
        self.info_10 = info[9]
        self.info_11 = info[10]
        self.info_12 = info[11]

class BoardData_RBC():
    boardPick : missionData_RBC
    boardPlace : missionData_RBC 
    _fastening : list[missionData_RBC]  = []
    
    def __init__(self, boardpick : missionData_RBC, boardplace : missionData_RBC, boardfasten : list):
        self.boardPick = boardpick
        self.boardPlace = boardplace
        self._fastening = boardfasten

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)
    


class Layer_RBC:
    _layerID : int = 0
    _board : list[BoardData_RBC] = []
    _missions : list[missionData_RBC] = []
    
    def __init__(self, id):
        self._layerID = id

    def addBoard(self, board : BoardData_RBC):
        if len(self._board) == 0: 
            self._board = []
            self._board.append(board)
        else:
            self._board.append(board)

    def addMission(self, mission : BoardData_RBC):
        if len(self._missions) == 0: 
            self._missions = []
            self._missions.append(board)
        else:
            self._missions.append(board)
        
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)

class Layers_RBC:
    _stationID : int
    _layers : list[Layer_RBC] = []
    def __init__(self, stationID):
        self._stationID = stationID

    def addLayer(self, layer : Layer_RBC):
        if len(self._layers) == 0: 
            self._layers = []
            self._layers.append(layer)
        else:
            self._layers.append(layer)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)

if __name__ == "__main__":
    data = [1,2,3,4,5,6,7,8,9,10,11,12]
    pick = missionData_RBC(400)

    #pick.setInfo([1,2,3,4,5,6,7,8,9,10,11,12])
    place = missionData_RBC(402)
    place.info_01 = 1#sheet['e1x'] # e1x
    place.info_02 = 2#sheet['e1y'] # e1y
    place.info_03 = 0
    place.info_04 = 0
    place.info_05 = 0 #sheet['actual_thickness']
    place.info_06 = 1 #TBD got to get panel thickness
    place.info_11 = 0
    place.info_12 = 0
    #place.setInfo([1,2,3,4,5,6,7,8,9,10,11,12])
    mission = missionData_RBC(130)
    #mission.setInfo([1,2,3,4,5,6,7,8,9,10,11,12])

    board = BoardData_RBC(pick, place)
    #board.fastening.append([1,2,3,4,5,6,7,8,9,10,11,12])
    layer = Layer_RBC(board)
    layer.addBoard(board)
    rbcData = Layers_RBC(layer)
    rbcData.addLayer(layer)
    jsondd = rbcData.toJSON()
    print(jsondd)