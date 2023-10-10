import glob
import logging
import time
from datetime import datetime


def check_folder() -> bool:  # Checks to See if a new EHX File has been added to the folder
    folder_path = r'C:\Users\Andrew Murray\Desktop\SampleTestPull Folder'
    xml_files = glob.glob(folder_path + '\\*.EHX')

    if xml_files:
        filePresent = True
    else:
        filePresent = False

    return filePresent


logging.basicConfig(filename='app.log', level=logging.INFO)
logging.info('Started')
runContinuous = True
# Enter Periodic Loop

while runContinuous:
    today = datetime.now()
    print(check_folder())

    print("wait" + str(today))
    time.sleep(3)
