from datetime import datetime
import logging
import glob, shutil

from util.opcuaConnect import OPC_Connect
from util.EC1 import MtrlData, JobData
from util.EC2_3 import RunData
from util.panelData import Panel
from util.machineData import Line
from util.global_monitor import Build


build = Build()
EC1_Yes = True
EC23_Yes = True

panelID = "521ab575-d43f-4d63-ae8d-043854fc28e4"
machine = Line()
if EC1_Yes:
    panel = Panel(panelID)
    matData = MtrlData(panel)    
    matData.mdMain()
    jobdata = JobData(panelID, machine)
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