import time
import logging
import glob
import threading
import os
import json
import shutil
from EHXBuild.xmlparse import xmlParse as eHX
import EHXBuild.drawThumbnails as dThumb # Draw PNG Images
from util.opcuaConnect import OPC_Connect
from util.EC1 import Mtrl_Data, JobData
from util.EC2_3 import RunData
from util.panelData import Panel
from util.machineData import Line



# This Program will Run Continuously in the background of the Server PC to monitor if:
# - New EHX File has been loaded
# - A Job Has been added to the queue and need run data built for it

app_config_settings = {}

def check_folder() -> bool:  # Checks to See if a new EHX File has been added to the folder
    #folder_path = r'C:\Users\Andrew Murray\Desktop\SampleTestPull Folder'
    folder_path = app_config_settings.get('Monitor_Folder')
    xml_files = glob.glob(folder_path + '\\*.EHX')

    if xml_files:
        filePresent = True
    else:
        filePresent = False

    return filePresent


def ehx_parse(opc_connection: OPC_Connect):  # Calls the XML Parse to Break down Job data into (Jobs, Bundles, Panels, Headers, Elements)
    nodeID = "ns=2;s=[think_core]/CAD2FAB/Parse_Info/Parse_Active"
    opc_connection.set_value(nodeID, False)
    #folder_path = r"C:\Users\Andrew Murray\Desktop\SampleTestPull Folder"  # Replace with the actual folder path
    folder_path = app_config_settings.get('Monitor_Folder')
    archive_path = app_config_settings.get('Archive_Folder')
    # Use glob to find all XML files in the folder
    xml_files = glob.glob(folder_path + "/*.EHX")

    # Print the list of XML files
    for file in xml_files:
        print(file)
        parse = eHX(file)
        thread = threading.Thread(target=parse.xml_main)
        joiner = " - "
        thread.start()
        delay_count = 0
        while thread.is_alive() or delay_count < 5:
            tags = [
                {"node_id": "ns=2;s=[think_core]/CAD2FAB/Parse_Info/Total_Panel_Count", "value": parse.parse_progress.panels_total},
                {"node_id": "ns=2;s=[think_core]/CAD2FAB/Parse_Info/Interior_Panel_Count", "value": parse.parse_progress.panels_interior},
                {"node_id": "ns=2;s=[think_core]/CAD2FAB/Parse_Info/Exterior_Panel_Count", "value": parse.parse_progress.panels_exterior},
                {"node_id": "ns=2;s=[think_core]/CAD2FAB/Parse_Info/Stud_Type_required", "value": joiner.join(parse.parse_progress.stud_type_required)},
                {"node_id": "ns=2;s=[think_core]/CAD2FAB/Parse_Info/Sheathing_Type_required", "value": joiner.join(parse.parse_progress.sheathing_type_required)}
                # Add more tags as needed
            ]
            if not thread.is_alive():
                delay_count += 1
            opc_connection.set_multi_values(tags)
            time.sleep(2)

        thread.join()
        shutil.move(file, archive_path)

        img = dThumb.GenPreview()
        img.previewMain(app_config_settings.get('ImageDropFolder'))


def check_queue_request(opc_connection: OPC_Connect) -> bool:
    nodeID = "ns=2;s=[think_core]/CAD2FAB/Add_Run_Data"
    val = opc_connection.get_value(node_id=nodeID)
    if val:
        requestRunData = True
    else:
        requestRunData = False

    print('trig val: ' + str(val))

    return requestRunData


def build_panel_data(opc_connection: OPC_Connect):
    nodeID = "ns=2;s=[think_core]/CAD2FAB/PanelGUID"
    panelID = opc_connection.get_value(node_id=nodeID)
    # Build EC1 Run Data for:
    # - Stud Picker (SF3)
    # - Framer (FM3)

    # Build Panel Definition
    panel = Panel(panelID)
    # Build Machine Definition
    machine = Line()
    # Material Definition (SF3)
    matData = Mtrl_Data(panel)
    thread1 = threading.Thread(target=matData.md_main)  # sf3Status = matData.md_main()
    # Framer Definition (FM3)
    job_data = JobData(panel, machine)
    thread2 = threading.Thread(target=job_data.jd_main)  # fm3Status = job_data.jd_main()
    # EC2 and EC3 RunData Definition
    run_data = RunData(panel, machine)
    thread3 = threading.Thread(target=run_data.rd_main)  # rbcStatus: list = run_data.rd_main()
    joiner = " - "
    # Start all threads simultaneously
    thread1.start()  # Build Jobs Material Data for Stud Picker
    thread2.start()  # Build Job Data for Framing Station
    thread3.start()  # Build Run Data for Robotic Cells EC2/3
    opc_connection.open()
    delay_count = 0
    while thread2.is_alive() or delay_count < 5:
        tags = [
            {"node_id": "ns=2;s=[think_core]/CAD2FAB/EC1/FM3_Status", "value": job_data.build_progress.fm3_status},  # Framer Status
            {"node_id": "ns=2;s=[think_core]/CAD2FAB/EC1/SF3_Status", "value": matData.build_progress.sf3_status},  # StudFeeder Status
            {"node_id": "ns=2;s=[think_core]/CAD2FAB/EC1/Stud_Type", "value": job_data.build_progress.auto_stud_type},
            # Framer 2x4 or 2x6 stud type
            {"node_id": "ns=2;s=[think_core]/CAD2FAB/EC1/Auto_Stud_Count", "value": job_data.build_progress.auto_stud_count},
            # Framer Num of Auto Studs for Job
            {"node_id": "ns=2;s=[think_core]/CAD2FAB/EC1/Num_of_Assemblies", "value": job_data.build_progress.sub_assembly_count},
            # Framer Num of Sub Assemblies
            {"node_id": "ns=2;s=[think_core]/CAD2FAB/EC2/Status", "value": run_data.build_rbc_progress.ec2_status},  # EC2 Status
            {"node_id": "ns=2;s=[think_core]/CAD2FAB/EC3/Status", "value": run_data.build_rbc_progress.ec3_status},  # EC3 Status
            {"node_id": "ns=2;s=[think_core]/CAD2FAB/EC2/Operations", "value": joiner.join(run_data.build_rbc_progress.ec2_operations)},
            # EC2 Operation List
            {"node_id": "ns=2;s=[think_core]/CAD2FAB/EC3/Operations", "value": joiner.join(run_data.build_rbc_progress.ec3_operations)},
            # EC3 Operations List
            {"node_id": "ns=2;s=[think_core]/CAD2FAB/EC2/Material Count", "value": run_data.build_rbc_progress.material_count},
            {"node_id": "ns=2;s=[think_core]/CAD2FAB/EC2/Material Required", "value": joiner.join(run_data.build_rbc_progress.materials_required)},
            {"node_id": "ns=2;s=[think_core]/CAD2FAB/EC2/Fasteners Required", "value": joiner.join(run_data.build_rbc_progress.fasteners_required)},
            {"node_id": "ns=2;s=[think_core]/CAD2FAB/EC3/Material Count", "value": run_data.build_rbc_progress.material_count},
            {"node_id": "ns=2;s=[think_core]/CAD2FAB/EC3/Material Required", "value": joiner.join(run_data.build_rbc_progress.materials_required)},
            {"node_id": "ns=2;s=[think_core]/CAD2FAB/EC3/Fasteners Required", "value": joiner.join(run_data.build_rbc_progress.fasteners_required)},
            # EC3 Operations List
        ]
        if not thread2.is_alive():
            delay_count += 1
        opc_connection.set_multi_values(tags)
        time.sleep(0.5)
    thread1.join()
    thread2.join()
    thread3.join()
    nodeID = "ns=2;s=[think_core]/CAD2FAB/Add_Run_Data"
    opc_connection.set_value(nodeID, False)


def run():
    opc = OPC_Connect()
    active_directory = os.getcwd()
    config_Path = active_directory + r'\appConfig.json'
    # Open the JSON file
    with open(config_Path) as json_file:
        # Load the JSON data into a dictionary
        global app_config_settings
        app_config_settings = json.load(json_file)
    try:
        logging.basicConfig(filename='app.log', level=logging.INFO)
        logging.info('Started')
        runContinuous = True
        opc.open()
        # Enter Periodic Loop
        while runContinuous:


            # Check to See if New EHX File has been Added to Folder
            if check_folder():
                ehx_parse(opc_connection=opc)
            # Build Run Data if Add to Queue request comes in
            if check_queue_request(opc_connection=opc):
                build_panel_data(opc_connection=opc)
            print("IDLE")
            time.sleep(1)

            current_dir = os.getcwd()
            print("Current directory:", current_dir)

    finally:
        opc.close()
