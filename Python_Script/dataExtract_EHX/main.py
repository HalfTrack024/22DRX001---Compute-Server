from datetime import datetime
import time
import logging
import glob, shutil
import EHXBuild.xmlparse as EHX
from util.opcuaConnect import OPC_Connect
from util.EC1 import MtrlData, JobData
from util.EC2_3 import RunData
from util.panelData import Panel
from util.machineData import Line
import json

# This Program will Run Continuously in the background of the Server PC to monitor if:
# - New EHX File has been loaded
# - A Job Has been added to the queue and needs run data built for it

def checkFolder() -> bool: #Checks to See if a new EHX File has been added to the folder
    folder_path = r'C:\Users\Andrew Murray\Desktop\SampleTestPull Folder'
    xml_files = glob.glob(folder_path + '\\*.EHX')

    if xml_files:
        filePresent = True
    else:
        filePresent = False
    
    return filePresent

def ehxParse(): # Calls the XML Parse to to Break down Job data into (Jobs, Bundles, Panels, Headers, Elements)

    folder_path = r"C:\Users\Andrew Murray\Desktop\SampleTestPull Folder"  # Replace with the actual folder path

    # Use glob to find all XML files in the folder
    xml_files = glob.glob(folder_path + "/*.EHX")

    # Print the list of XML files
    for file in xml_files:
        print(file)
        EHX(file)

def checkQueueRequest(opcConnection : OPC_Connect) -> bool:    
    nodeID = "ns=2;s=[22DRX001_EC1]/CAD2FAB/Add_Run_Data"
    val = opcConnection.getValue(nodeID= nodeID)
    if val:
        requestRunData = True
    else:
        requestRunData = False

    print('trig val: ' + str(val))

    return requestRunData

def buildPanelData(opcConnection : OPC_Connect):
    nodeID = "ns=2;s=[22DRX001_EC1]/CAD2FAB/PanelGUID"
    panelID = opcConnection.getValue(nodeID= nodeID)
    # Build EC1 Run Data for:
    # - Stud Picker (SF3)
    # - Framer (FM3)

    
    # Build Panel Definition
    panel = Panel(panelID)
    # Build Machine Definition
    machine = Line()
    # Material Definition (SF3)
    matData = MtrlData(panel)    
    sf3Status = matData.mdMain()
    # Framer Definition (FM3)
    jobdata = JobData(panelID)
    fm3Status = jobdata.jdMain()
    #EC2 and EC3 RunData Definition
    runData = RunData(panel, machine)
    rbcStatus : list = runData.rdMain()

    nodeID = "ns=2;s=[22DRX001_EC1]/CAD2FAB/Add_Run_Data"
    opcConnection.setValue(nodeID, False)

    nodeID = "ns=2;s=[22DRX001_EC1]/CAD2FAB/Data_Status"
    dataDoc = opcConnection.getValue(nodeID)
    dataDoc = json.loads(dataDoc)

    dataDoc['EC1']['Status'] = 1
    dataDoc['EC1']['Description'] = 'Complete'
    dataDoc['EC2']['Status'] = 1
    dataDoc['EC2']['Description'] = 'Complete'
    dataDoc['EC3']['Status'] = 1
    dataDoc['EC3']['Description'] = 'Complete'
    dataDoc = json.dumps(dataDoc)
    opcConnection.setValue(nodeID, dataDoc)

        


   
# [22DRX001_EC1]/CAD2FAB/Add_Run_Data - BOOL
# [22DRX001_EC1]/CAD2FAB/PanelGUID - STRING
# [22DRX001_EC1]/CAD2FAB/Data_Status - DataSet
# [22DRX001_EC1]/CAD2FAB/
print(__name__)
logging.basicConfig(filename='app.log', level=logging.INFO)
logging.info('Started')
runContinuos = True
#Enter Periodic Loop
 
opc = OPC_Connect()
opc.open()
while runContinuos == True:
    today = datetime.now()

    # Check to See if New EHX File has been Added to Folder
    if checkFolder():
        ehxParse()
    # Build Run Data if Add to Queue request comes in
    if checkQueueRequest(opcConnection = opc):
        buildPanelData(opcConnection= opc)
    print("wait")
    time.sleep(3)

opc.close()

# except:
#     pass
# finally:
#     #opc.close()
#     logging.info('Program Has Stopped')

if __name__ == 'main':
    pass