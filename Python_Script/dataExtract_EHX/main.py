from datetime import datetime
import logging
import glob, shutil
import xmlparse
from util.opcuaConnect import OPC_Connect
from util.EC1 import MtrlData, JobData
from util.EC2_3 import RunData
from util.panelData import Panel
from util.machineData import Line

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
        xmlparse(file)

def checkQueueRequest(opcConnection : OPC_Connect) -> bool:    
    nodeID = "ns=2;s=[default]/PythonComTag"
    val = opcConnection.getValue(nodeID= nodeID)
    if val:
        requestRunData = True
    else:
        requestRunData = False

    opcConnection.setValue(nodeID, 32)
    return requestRunData

def buildPanelData(opcConnection : OPC_Connect):
    nodeID = "ns=2;s=[default]/PythonComTag"
    panelList = opcConnection.getValue(nodeID= nodeID)
    # Build EC1 Run Data for:
    # - Stud Picker (SF3)
    # - Framer (FM3)
    for panelID in panelList:
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
        


   
# [22DRX001_EC1]/CAD2FAB/Add_Run_Data - BOOL
# [22DRX001_EC1]/CAD2FAB/PanelGUID - STRING
# [22DRX001_EC1]/CAD2FAB/Data_Status - ARRAY OF BYTE
# [22DRX001_EC1]/CAD2FAB/

logging.basicConfig(filename='app.log', level=logging.INFO)
logging.info('Started')
runContinuos = True
#Enter Periodic Loop
 
try:
    opc = OPC_Connect()
    opc.open()
    while runContinuos == True:
        today = datetime.now()

        # Check to See if New EHX File has been Added to Folder
        if checkFolder():
            ehxParse()
        # If 
        if checkQueueRequest(opcConnectoin = opc):
            buildPanelData(opcConnection= opc)

except:
    pass
finally:
    opc.close()
    logging.info('Program Has Stopped')

