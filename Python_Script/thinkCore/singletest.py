import time

from util.opcuaConnect import OPC_Connect

connect = OPC_Connect()

tags = [
    {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC1/FM3_Status", "value": "job_data.build_progress.fm3_status"},  # Framer Status
    {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC1/SF3_Status", "value": "matData.build_progress.sf3_status"},  # StudFeeder Status
    {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC1/Stud_Type", "value": "job_data.build_progress.auto_stud_type"},  # Framer 2x4 or 2x6 stud type
    {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC1/Auto_Stud_Count", "value": 0},
    # Framer Num of Auto Studs for Job
    {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC1/Num_of_Assemblies", "value": 0},
    # Framer Num of Sub Assemblies
    {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC2/Status", "value": "run_data.build_rbc_progress.ec2_status"},  # EC2 Status
    {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC3/Status", "value": "run_data.build_rbc_progress.ec3_status"},  # EC3 Status
    {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC2/Operations", "value": "joiner.join(run_data.build_rbc_progress.ec2_operations)"},
    # EC2 Operation List
    {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC3/Operations", "value": "joiner.join(run_data.build_rbc_progress.ec3_operations)"},
    # EC3 Operations List
    {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC2/Material Count", "value": 24},
    {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC2/Material Required", "value": "joiner.join(run_data.build_rbc_progress.fasteners_required)"},
    # EC3 Operations List
    {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC3/Material Count", "value": 24},
    {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC3/Material Required", "value": str(time.time())}
]

values = {
    "Auto_Stud_Count": 22,  # Replace with your UDT field names and values
    "FM3_Status": "HAHA",
    "Num_of_Assemblies": 32,
    "SF3_Status": "JAJA",
    "Stud_Type": "2x5"
    # Add more fields as necessary
}
connect.open()
count = 0
while count < 100:
    tags = [
        {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC1/FM3_Status", "value": "job_data.build_progress.fm3_status"},  # Framer Status
        {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC1/SF3_Status", "value": "matData.build_progress.sf3_status"},  # StudFeeder Status
        {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC1/Stud_Type", "value": "job_data.build_progress.auto_stud_type"},  # Framer 2x4 or 2x6 stud type
        {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC1/Auto_Stud_Count", "value": 0},
        # Framer Num of Auto Studs for Job
        {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC1/Num_of_Assemblies", "value": 0},
        # Framer Num of Sub Assemblies
        {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC2/Status", "value": "run_data.build_rbc_progress.ec2_status"},  # EC2 Status
        {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC3/Status", "value": "run_data.build_rbc_progress.ec3_status"},  # EC3 Status
        {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC2/Operations", "value": "joiner.join(run_data.build_rbc_progress.ec2_operations)"},
        # EC2 Operation List
        {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC3/Operations", "value": "joiner.join(run_data.build_rbc_progress.ec3_operations)"},
        # EC3 Operations List
        {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC2/Material Count", "value": 24},
        {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC2/Material Required", "value": "joiner.join(run_data.build_rbc_progress.fasteners_required)"},
        # EC3 Operations List
        {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC3/Material Count", "value": 24},
        {"node_id": "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC3/Material Required", "value": str(time.time())}]
    node_id = "ns=2;s=[22DRX001_EC1]/CAD2FAB/EC1"
    connect.set_multi_values(tags)
    time.sleep(0.5)
    print("its going: " + str(count))
    count += 5
connect.close()
