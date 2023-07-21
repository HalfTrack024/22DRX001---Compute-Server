import json
import ast

class missionData_RBC:
    missionID : int
    Info_01 : float
    Info_02 : float
    Info_03 : float
    Info_04 : float
    Info_05 : float
    Info_06 : float
    Info_07 : float
    Info_08 : float 
    Info_09 : float
    Info_10 : int
    Info_11 : int
    Info_12 : int
    
    def __init__(self, missionID):
        self.missionID = missionID

    def toJSON(self):
        return self.__dict__
    
    def setInfo(self, info : list):
        self.Info_01 = info[0]
        self.Info_02 = info[1]
        self.Info_03 = info[2]
        self.Info_04 = info[3]
        self.Info_05 = info[4]
        self.Info_06 = info[5]
        self.Info_07 = info[6]
        self.Info_08 = info[7]
        self.Info_09 = info[8]
        self.Info_10 = info[9]
        self.Info_11 = info[10]
        self.Info_12 = info[11]

class BoardData_RBC():
    boardPick : missionData_RBC
    boardPlace : missionData_RBC 
    _fastening : list[missionData_RBC]  = []
    
    def __init__(self, boardpick : missionData_RBC, boardplace : missionData_RBC, boardfasten : list [missionData_RBC]):
        self.boardPick = boardpick
        self.boardPlace = boardplace
        self._fastening = boardfasten

    def toJSON(self):
        data = { }
        data["BoardPick"] = self.boardPick.__dict__
        data["BoardPlace"] = self.boardPlace.__dict__
        jArr = []
        for i in range(len(self._fastening)):
            jArr.append(self._fastening[i].toJSON()) 
        data["Fastening"] = jArr           

                
        #data["mission"] = mission
        return data
    


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

    def addMission(self, mission : missionData_RBC):
        if len(self._missions) == 0: 
            self._missions = []
            self._missions.append(mission)
        else:
            self._missions.append(mission)

    def addMission(self, mission : list[missionData_RBC]):
        self._missions.extend(mission)
        
    def toJSON(self):
        #jObj = { }
        jPar = { }
        jArr = []
        for i in range(len(self._board)):
            #jObj["board" + str(i)] = self._board[i].toJSON()
            jArr.append(self._board[i].toJSON())
        jPar["Board"] = jArr
        #jArr.clear()
        jArr2 = []
        for i in range(len(self._missions)):
            jArr2.append(self._missions[i].toJSON())
            #jObj["mission" + str(i)] = self._missions[i].toJSON()     
        jPar["Mission"] = jArr2   
        #data = json.dumps(jPar, default=lambda o: o.__dict__)
        return jPar
        
        #return jObj

class Layers_RBC:
    
    _layers : list[Layer_RBC] = []
    #_stationID : int
    def __init__(self, stationID : int):
        #self._stationID = stationID
        self._layers.clear()

    def addLayer(self, layer : Layer_RBC):
        if len(self._layers) == 0: 
            #self._layers = []
            self._layers.append(layer)
        else:
            self._layers.append(layer)

    def getCount(self):
        return len(self._layers)
    
    def getLayer(self, index):
        return self._layers[index]

    def toJSON(self):
        jObj = { }
        #data = json.dumps(self, default=lambda o: o.__dict__)
        i = 0
        for i in range(len(self._layers)):
            jObj[str(i)] = self._layers[i].toJSON()
        
        data = json.dumps(jObj, default=lambda o: o.__dict__)
        return data


if __name__ == "__main__":
    data = [1,2,3,4,5,6,7,8,9,10,11,12]
    pick = missionData_RBC(400)

    #pick.setInfo([1,2,3,4,5,6,7,8,9,10,11,12])
    place = missionData_RBC(402)
    place.Info_01 = 1#sheet['e1x'] # e1x
    place.Info_02 = 2#sheet['e1y'] # e1y
    place.Info_03 = 0
    place.Info_04 = 0
    place.Info_05 = 0 #sheet['actual_thickness']
    place.Info_06 = 1 #TBD got to get panel thickness
    place.Info_11 = 0
    place.Info_12 = 0
    #place.setInfo([1,2,3,4,5,6,7,8,9,10,11,12])
    mission = missionData_RBC(130)
    #mission.setInfo([1,2,3,4,5,6,7,8,9,10,11,12])

    board = BoardData_RBC(pick, place, [place, place])
    #board.fastening.append([1,2,3,4,5,6,7,8,9,10,11,12])
    layer = Layer_RBC(board)
    board = BoardData_RBC(pick, place, [])
    
    layer.addBoard(board)
    layer.addMission([place, place])
    rbcData = Layers_RBC(55)
    rbcData.addLayer(layer)
    layer.addMission([place, place])
    rbcData.addLayer(layer)

    data1 = rbcData.toJSON()


    print(data1)