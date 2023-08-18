import time
import logging
from  datetime import datetime
import glob, shutil
import EHXBuild.xmlparse
import json
import EHXBuild.xmlparse as EHX
from util import opcuaConnect
from util.EC1 import MtrlData, JobData
from util.EC2_3 import RunData

def checkFolder() -> bool: #Checks to See if a new EHX File has been added to the folder
    folder_path = r'C:\Users\Andrew Murray\Desktop\SampleTestPull Folder'
    xml_files = glob.glob(folder_path + '\\*.EHX')

    if xml_files:
        filePresent = True
    else:
        filePresent = False
    
    return filePresent


logging.basicConfig(filename='app.log', level=logging.INFO)
logging.info('Started')
runContinuos = True
#Enter Periodic Loop

while runContinuos == True:
    today = datetime.now()
    print(checkFolder())

    print("wait" + str(today))
    time.sleep(3)

