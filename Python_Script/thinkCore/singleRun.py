from datetime import datetime
import logging
import util.General_Help as gHelp
from util.EC1 import Mtrl_Data, JobData
from util.EC2_3 import RunData
from util.panelData import Panel
from util.machineData import Line


EC1_Yes = True
EC23_Yes = True

app_settings = gHelp.get_app_config()

panelID = "84c55d39-9078-4cf1-b665-b56a5a087b9b"
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