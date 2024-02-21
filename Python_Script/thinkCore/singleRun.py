import logging
import time
from datetime import datetime

import util.General_Help as gHelp
from util.EC1 import Mtrl_Data, JobData
from util.EC2_3 import RunData
from util.machineData import Line
from util.panelData import Panel

EC1_Yes = True
EC23_Yes = True

app_settings = gHelp.get_app_config()


panelID = "9ad2d7b5-b929-4a2f-b3e0-c7990f015be51"
machine = Line(app_settings)

#for panelID in panelIDs:
if EC1_Yes:

    panel = Panel(panelID)
    matData = Mtrl_Data(panel)
    matData.md_main()
    jobdata = JobData(panel, machine)
    test = jobdata.jd_main()

if EC23_Yes:
    today = datetime.now()
    loggfile = 'app_' + str(today) + '.log'

    logging.basicConfig(filename='app.log', level=logging.INFO)
    logging.info('Started')
    panel = Panel(panelID)

    run = RunData(panel, machine)
    run.rd_main()
