from datetime import datetime
import logging
import util.General_Help as gHelp
from util.EC1 import Mtrl_Data, JobData
from util.EC2_3 import RunData
from util.panelData import Panel
from util.machineData import Line


EC1_Yes = False
EC23_Yes = True

app_settings = gHelp.get_app_config()

panelID = "521ab575-d43f-4d63-ae8d-043854fc28e4"
machine = Line(app_settings)
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