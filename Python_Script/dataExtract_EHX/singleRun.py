from datetime import datetime
import logging
import glob, shutil
import xmlparse
from util.opcuaConnect import OPC_Connect
from util.EC1 import MtrlData, JobData
from util.EC2_3 import RunData
from util.panelData import Panel
from util.machineData import Line


EC1_Yes = False
EC23_Yes = True

panelID = "f46fa82b-0bd5-4b6c-9e7a-cce56b3143fb"

if EC1_Yes:
    panel = Panel(panelID)
    matData = MtrlData(panel)    
    jobdata = JobData(panelID)
    test = jobdata.jdMain()

if EC23_Yes:
    today = datetime.now()
    loggfile = 'app_' + str(today) + '.log'

    logging.basicConfig(filename='app.log', level=logging.INFO)
    logging.info('Started')
    panel = Panel(panelID)

    machine = Line()
    run = RunData(panel, machine)
    run.rdMain()