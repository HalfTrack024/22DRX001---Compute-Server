

#TODO Check that all operations are linear moving always positive direction
#TODO Ensure that all Operator Confirmation (Except first Plate Load) has images linked

#(panelguid, xpos, optext, opcode_fs, zpos_fs, ypos_fs, ssuppos_fs, opcode_ms, zpos_ms, ypos_ms, ssuppos_ms, imgname, obj_id, loaddate)
#(panelguid, item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8], item[9], item[10], item[11])

def check_opData(items: list):
    orted_list = sorted(items, key=lambda x: x[12])

    for item in items:
        pass
        #Check that if optext contains Operator Confirmation then ensure that imgname is not null / None


