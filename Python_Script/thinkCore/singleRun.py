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

panelIDs = ["b1d788b3-5d67-4d35-8ebb-8e198820ee7d",
"7b0e75f1-4d5d-4b52-a12f-92323e81590d",
"145bb017-7fe5-481f-ab5d-cc3e1b099ee1",
"1639c3a4-febf-4f99-80f8-b1fd8c6b9e9a",
"458e5496-c82b-4564-bc56-354be671548c"]

panelID = "26200fc1-01a2-4c2d-9cbd-5e376bae7a05"
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
