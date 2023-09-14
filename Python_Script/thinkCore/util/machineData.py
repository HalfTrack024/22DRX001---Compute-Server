from typing import Any
import util.designtree as dt
from util.Parameters import Parameters

app_config_settings = {}


class Station:
    station_id = None
    run_level = {}
    parmData = None
    fastenSpace = {}
    partial_board = None
    off_cut = None

    # def __init__(self, ec2=None, ec3=None):
    #     """id """
    #     if ec2 is None and ec3 is None:
    #         raise ValueError("At least one argument must be provided.")
    #     elif ec2 is not None and ec3 is not None:
    #         raise ValueError("At least one argument must be provided.")
    #     else:
    #         if ec2 is not None:
    #             self.ec = ec2
    #         elif ec3 is not None:
    #             self.ec = ec3

class EC1:

    def __init__(self) -> None:
        self.parmData = Parameters([], 1, 9)
        self.nailSpaceFS = {
            '2x4': {
                'nailCount': self.parmData.getParm("Nail Tool FS", "Nail Count 2x4"),
                'positions': [self.parmData.getParm("Nail Tool FS", "First Nail Position 2x4"),
                              self.parmData.getParm("Nail Tool FS", "Second Nail Position 2x4"),
                              self.parmData.getParm("Nail Tool FS", "Third Nail Position 2x4")]
            },
            '2x6': {
                'nailCount': self.parmData.getParm("Nail Tool FS", "Nail Count 2x6"),
                'positions': [self.parmData.getParm("Nail Tool FS", "First Nail Position 2x6"),
                              self.parmData.getParm("Nail Tool FS", "Second Nail Position 2x6"),
                              self.parmData.getParm("Nail Tool FS", "Third Nail Position 2x6")]
            }
        }
        self.nailSpaceMS = {
            '2x4': {
                'nailCount': self.parmData.getParm("Nail Tool MS", "Nail Count 2x4"),
                'positions': [self.parmData.getParm("Nail Tool MS", "First Nail Position 2x4"),
                              self.parmData.getParm("Nail Tool MS", "Second Nail Position 2x4"),
                              self.parmData.getParm("Nail Tool MS", "Third Nail Position 2x4")]
            },
            '2x6': {
                'nailCount': self.parmData.getParm("Nail Tool MS", "Nail Count 2x6"),
                'positions': [self.parmData.getParm("Nail Tool MS", "First Nail Position 2x6"),
                              self.parmData.getParm("Nail Tool MS", "Second Nail Position 2x6"),
                              self.parmData.getParm("Nail Tool MS", "Third Nail Position 2x6")]
            }
        }


class EC2(Station):

    def __init__(self) -> None:
        self.station_id = 2
        self.run_lvl = {}
        self.parmData = Parameters([], 10, 19)
        self.run_lvl = {
            'ec2_20': self.parmData.getParm("Application", "Run Level 20 missions (True/false)"),
            'ec2_30': self.parmData.getParm("Application", "Run Level 30 missions (True/false)"),
            'ec2_40': self.parmData.getParm("Application", "Run Level 40 missions (True/false)")}
        self.fastenSpace = {
            'edge': self.parmData.getParm("ZL Core", "Default Edge Fasten Spacer"),
            'field': self.parmData.getParm("ZL Core", "Default Field Fasten Spacer")
        }
        self.partial_board = self.parmData.getParm("ZL Core", "Partial Board Min")
        self.off_cut = self.parmData.getParm("ZL Core", "Offcut Board Min")


class EC3(Station):

    def __init__(self) -> None:
        self.station_id = 3
        self.run_lvl = {}
        self.parmData = Parameters([], 20, 29)
        self.run_lvl = {
            'ec3_20': self.parmData.getParm("Application", "Run Level 20 missions (True/false)"),
            'ec3_30': self.parmData.getParm("Application", "Run Level 30 missions (True/false)"),
            'ec3_40': self.parmData.getParm("Application", "Run Level 40 missions (True/false)")}
        self.fastenSpace = {
            'edge': self.parmData.getParm("ZL Core", "Default Edge Fasten Spacer"),
            'field': self.parmData.getParm("ZL Core", "Default Field Fasten Spacer")
        }
        self.partial_board = self.parmData.getParm("ZL Core", "Partial Board Min")
        self.off_cut = self.parmData.getParm("ZL Core", "Offcut Board Min")


class Line(EC1, EC2, EC3):

    def __init__(self, app_settings) -> None:
        global app_config_settings
        app_config_settings = app_settings
        super().__init__()
        self.ec1 = EC1()
        self.ec2 = EC2()
        self.ec3 = EC3()
        self.toolIndex = 1
        self.determine = []
        self.determine.extend(self.ec2.run_lvl.values())
        self.determine.extend(self.ec3.run_lvl.values())

        self.predict_layer_count = 1

        self.determine.append(self.predict_layer_count)
        self.predict = dt.process_builder(self.determine, app_config_settings)

    def get_prediction(self):
        return self.predict

    def change_prediction(self, layer_count):
        self.predict_layer_count = layer_count
        self.determine[6] = layer_count

        self.predict = dt.process_builder(self.determine, app_config_settings)

    def get_system_parms(self, system_index):
        """EC1: 1, EC2:2, EC3:3"""
        match system_index:
            case 1:
                return 0
            case 2:
                return self.ec2.parmData
            case 3:
                return self.ec3.parmData





# if __name__ == "__main__":
#     machine = Line()

#     print(machine.getPrediction())
