import json


class missionData_RBC:
    missionID: int
    Info_01: float
    Info_02: float
    Info_03: float
    Info_04: float
    Info_05: float
    Info_06: float
    Info_07: float
    Info_08: float
    Info_09: float
    Info_10: int
    Info_11: int
    Info_12: int

    def __init__(self, mission_id):
        self.missionID = mission_id

    def to_json(self):
        return self.__dict__

    def set_info(self, info: list):
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


class Layer_Properties:
    Item_Thickness: float

    def __init__(self):
        self.Item_Thickness = 0

    @property
    def to_json(self):
        return self.__dict__


class BoardData_RBC:
    boardPick: missionData_RBC
    boardPlace: missionData_RBC
    _fastening: list[missionData_RBC] = []

    def __init__(self, board_pick: missionData_RBC, board_place: missionData_RBC, board_fasten: list[missionData_RBC]):
        self.boardPick = board_pick
        self.boardPlace = board_place
        self._fastening = board_fasten

    def to_json(self):
        data = {"BoardPick": self.boardPick.__dict__, "BoardPlace": self.boardPlace.__dict__}
        jArr = []
        for i in range(len(self._fastening)):
            jArr.append(self._fastening[i].to_json())
        data["Fastening"] = jArr

        # data["mission"] = mission
        return data


class Layer_RBC:
    _layer_properties: Layer_Properties

    def __init__(self, layer_id):
        self._layerID: int = 0
        self._board: list[BoardData_RBC] = []
        self._missions: list[missionData_RBC] = []
        self._layer_properties = Layer_Properties()
        # self._board.clear()
        # self._missions.clear()
        self._layerID = layer_id

    def add_board(self, board: BoardData_RBC):
        if len(self._board) == 0:
            self._board = []
            self._board.append(board)
        else:
            self._board.append(board)

    def add_mission(self, mission: missionData_RBC):
        if len(self._missions) == 0:
            self._missions = []
            self._missions.append(mission)
        else:
            self._missions.append(mission)

    def add_mission(self, mission: list[missionData_RBC]):
        self._missions.extend(mission)

    def set_properties(self, item_thickness):
        self._layer_properties.Item_Thickness = item_thickness

    def to_json(self):
        # jObj = { }
        jPar = {}
        jArr = []
        for i in range(len(self._board)):
            # jObj["board" + str(i)] = self._board[i].toJSON()
            jArr.append(self._board[i].to_json())
        jPar["Board"] = jArr
        # jArr.clear()
        jArr2 = []
        for i in range(len(self._missions)):
            jArr2.append(self._missions[i].to_json())
            # jObj["mission" + str(i)] = self._missions[i].toJSON()
        jPar["Mission"] = jArr2
        # data = json.dumps(jPar, default=lambda o: o.__dict__)
        jPar["Material"] = self._layer_properties.__dict__
        return jPar

        # return jObj


class Layers_RBC:
    _layers: list[Layer_RBC] = []

    # _stationID : int
    def __init__(self, station_id: int):
        # self._stationID = stationID
        self._layers.clear()

    def add_layer(self, layer: Layer_RBC):
        if len(self._layers) == 0:
            # self._layers = []
            self._layers.append(layer)
        else:
            self._layers.append(layer)

    def get_count(self):
        return len(self._layers)

    def get_layer(self, index):
        return self._layers[index]

    def to_json(self):
        jObj = {}
        # data = json.dumps(self, default=lambda o: o.__dict__)
        for i in range(len(self._layers)):
            jObj[str(i)] = self._layers[i].to_json()

        data = json.dumps(jObj, default=lambda o: o.__dict__)
        return data

