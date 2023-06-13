from typing import Any
import designtree as dt
from Parameters import Parameters


class EC1:

    def __init__(self) -> None:
        pass



class EC2:

    def __init__(self) -> None:
        self.parmData = Parameters([], 10, 19)
        self.runlvl = {
            'ec2_20' : self.parmData.getParm("Application", "Run Level 20 missions (True/false)"), 
            'ec2_30' : self.parmData.getParm("Application", "Run Level 30 missions (True/false)"),
            'ec2_40' : self.parmData.getParm("Application", "Run Level 40 missions (True/false)")}

class EC3:

    def __init__(self) -> None:
        self.parmData = Parameters([], 20, 29)
        self.runlvl = {
            'ec3_20' : self.parmData.getParm("Application", "Run Level 20 missions (True/false)"), 
            'ec3_30' : self.parmData.getParm("Application", "Run Level 30 missions (True/false)"),
            'ec3_40' : self.parmData.getParm("Application", "Run Level 40 missions (True/false)")}
     

class Line(EC1, EC2, EC3):
    
    

    def __init__(self) -> None:
        ec1 = EC1()
        ec2 = EC2()
        ec3 = EC3()
        self.determine = []
        self.determine.extend(ec2.runlvl.values())
        self.determine.extend(ec3.runlvl.values())
        
        self.predictlayercount = 1

        self.determine.append(self.predictlayercount)
        self.predict = dt.processBuilder(self.determine)        

    def getPrediction(self):
        return self.predict
    
    def changePrediction(self, layercount):
        self.predictlayercount = layercount
        self.determine[6] = layercount

        self.predict = dt.processBuilder(self.determine)


    





if __name__ == "__main__":
    machine = Line()

    print(machine.getPrediction())