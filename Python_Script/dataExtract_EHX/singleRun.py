from datetime import datetime
import logging
import glob, shutil

from util.opcuaConnect import OPC_Connect
from util.EC1 import MtrlData, JobData
from util.EC2_3 import RunData
from util.panelData import Panel
from util.machineData import Line


EC1_Yes = False
EC23_Yes = True

panelID = "ad6b9fa2-42d2-4a36-abf1-010958325561"

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