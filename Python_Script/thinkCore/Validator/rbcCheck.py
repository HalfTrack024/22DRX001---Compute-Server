import json
from jsonschema import validate
import logging


def check_json_schema(run_data: dict) -> bool:
    # Load the schema
    with open(r'C:\Users\Andrew Murray\source\Copia\22DRX001\Python_Script\thinkCore\Validator\rbc_schema.json') as schema_file:
        schema = json.load(schema_file)

    try:
        validate(instance=run_data, schema=schema)
        return True
    except Exception as e:
        return False


def check_boards(board_list) -> bool:
    # Loop through all boards in Data
    status = 0
    # Return if no object was found
    if isinstance(board_list, dict):
        board_list: dict = board_list
    else:
        return False
    # Loop through each board in data
    for index_a, board in enumerate(board_list):
        if not check_board_pick(board.get("BoardPick", False)):
            logging.warning(f"Failed - BoardPicked:: Index: {index_a}")
            status += 1
        if not check_board_place(board.get("BoardPlace", False)):
            logging.warning(f"Failed - BoardPlaced:: Index: {index_a}")
            status += 1
        fasten_list = board.get("Fastening", False)
        for index_b, fasten in enumerate(fasten_list):
            if not check_fastening(fasten):
                logging.warning(f"Failed - Fastening:: Index: {index_b}")
                status += 1
    # Return Results
    if status > 0:
        return False
    else:
        return True


def check_board_pick(pick_data) -> bool:
    # Check info of board pick statements
    status = 0
    if isinstance(pick_data, dict):
        pick_data: dict = pick_data
    else:
        return False
    # Check Keys
    if not len(pick_data) == 9:  # desired number of keys for a pick operation is 9
        status += 1
        logging.warning("Incorrect Amount of Keys in Board Pick")
        # Check Keys

    if not pick_data.get("missionID") == 400:  # desired number of keys for a pick operation is 9
        status += 1
        logging.warning(f"Incorrect missionID - currently: {pick_data.get('missionID')}")

    # Return Results
    if status > 0:
        return False
    else:
        return True


def check_board_place(place_data) -> bool:
    # Check info of board pick statements
    status = 0
    if isinstance(place_data, dict):
        place_data: dict = place_data
    else:
        return False
    # Check Keys
    if not len(place_data) == 9:  # desired number of keys for a pick operation is 9
        status += 1
        logging.warning("Incorrect Amount of Keys in Board Pick")

    # Check valid mission ID
    if not place_data.get("missionID") in [401, 402, 403]:  # desired number of keys for a pick operation is 9
        logging.warning(f"Incorrect missionID - currently: {place_data.get('missionID')}")
        status += 1
    # Check fastener height
    place_corner_y = place_data.get("Info_02")
    fasten_corner_y = place_data.get("Info_06")
    if place_corner_y < 0:
        status += 1
        logging.warning(f"Info 2 is less than 0")
    if fasten_corner_y < 0:
        status += 1
        logging.warning(f"Info 6 is less than 0")

    if (fasten_corner_y - place_corner_y) > 8:
        status += 1
        logging.warning(f"Y-Positions of data not allowed (Info 2, 6)")

    place_corner_x = place_data.get("Info_01")
    fasten_corner_x = place_data.get("Info_05")
    if place_corner_x < -310:
        status += 1
        logging.warning(f"Info 2 is less than -310 (cannot place that far negative)")
    if fasten_corner_x < 0:
        status += 1
        logging.warning(f"Info 6 is less than 0")
    if (abs(place_corner_x) + fasten_corner_x) > 340:
        status += 1
        logging.warning(f"X-Positions of data not allowed (Info 1, 5)")

    # Return Results
    if status > 0:
        return False
    else:
        return True


def check_fastening(fasten_data) -> bool:
    #TODO Check fastener object is dictionary
    #TODO Check valid Mission ID
    #TODO Check total of keys in fasten object
    pass
