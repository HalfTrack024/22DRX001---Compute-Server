import logging

# (panelguid, xpos, optext, opcode_fs, zpos_fs, ypos_fs, ssuppos_fs, opcode_ms, zpos_ms, ypos_ms, ssuppos_ms, imgname, obj_id, loaddate)
# (panelguid, item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8], item[9], item[10], item[11])

def check_op_data(items: list):
    status = 0
    count = 0
    sort_by_objID = sorted(items, key=lambda x: x[12])

    if sort_by_objID != items:
        logging.warning(f"Failed Validation Framer- Order by Obj_ID is not sorted")
        status += 1

    sorted_by_xpos = sorted(sort_by_objID, key=lambda x: x[1])

    if sorted_by_xpos != sort_by_objID:
        logging.warning(f"Failed Validation Framer- Order by xpos is not sorted")
        status += 1

    for item in items[1:]:
        if "OperatorConfirmation" in item[2] and item[11] == '':
            logging.warning(f"Failed Validation Framer - Image Required at xpos {item[1]}")
            status += 1
        if item[11] != '' and "OperatorConfirmation" not in item[2]:
            logging.warning(f"Failed Validation Framer - Operator Confirmation Required at xpos {item[1]}")
            status += 1
        if "Auto" in item[2] and "Nailing" not in item[2]:
            count += 1

    # Return Results
    if status > 0:
        return False, count
    else:
        return True, count


def check_stud_feeder(mtrl_data, count):
    status = 0
    if mtrl_data[0] != count:
        status += 1
        logging.warning(f"Failed Validation StudFeeder - Auto Stud Count Incorrect")

    # Return Results
    if status > 0:
        return False, count
    else:
        return True, count