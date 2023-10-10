import xmltodict as dc  # requires python >= V3.4

from util import dataBaseConnect as dbc
from util.globals import Parse_Progress


def round_data(element_line):
    start = 5
    end = 22
    # elementList [panelguid,elementguid,type,description,size,b1x,b1y,b2x,b2y,b3x,b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,count]
    for i in range(start, end + 1):
        element_line[i] = round(element_line[i], 2)

    return element_line


class xmlParse:
    # app_settings: dict
    def __init__(self, filepath):
        self.parse_progress = Parse_Progress()
        # open the xml file
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            dataset = f.read()
        # variable data is accessible outside of this function
        self.data = dc.parse(dataset)
        #self.credentials = app_settings.get('DB_credentials')
        self.sCadFilepath = str(self.data['MITEK_SHOPNET_MARKUP_LANGUAGE_FILE']['Job']['JobID'])
        # xmlParse.data = self.data
        # xmlParse.credentials = self.credentials
        self.elementIN = []
        self.fastenerIN = []

    def append_element(self, element, elem_type, sub_ctr):
        if sub_ctr is None:
            self.elementIN.append(
                (element['PanelGuid'], element['BoardGuid'], elem_type,
                 element['FamilyMember'], element['FamilyMemberName'],
                 element['Material']['Size'], element['Material']['ActualThickness'],
                 element['Material']['ActualWidth'], element['Material']['Description'],
                 element['Material']['SpeciesGrade'],
                 element['BottomView']['Point'][0]['X'], element['BottomView']['Point'][0]['Y'],
                 element['BottomView']['Point'][1]['X'], element['BottomView']['Point'][1]['Y'],
                 element['BottomView']['Point'][2]['X'], element['BottomView']['Point'][2]['Y'],
                 element['BottomView']['Point'][3]['X'], element['BottomView']['Point'][3]['Y'],
                 element['ElevationView']['Point'][0]['X'], element['ElevationView']['Point'][0]['Y'],
                 element['ElevationView']['Point'][1]['X'], element['ElevationView']['Point'][1]['Y'],
                 element['ElevationView']['Point'][2]['X'], element['ElevationView']['Point'][2]['Y'],
                 element['ElevationView']['Point'][3]['X'], element['ElevationView']['Point'][3]['Y'], None),
            )
        elif sub_ctr is not None and elem_type != 'Sub Assembly' and elem_type != 'Hole':
            self.elementIN.append(
                (element['PanelGuid'], element['BoardGuid'], elem_type,
                 element['FamilyMember'], element['FamilyMemberName'],
                 element['Material']['Size'], element['Material']['ActualThickness'],
                 element['Material']['ActualWidth'], element['Material']['Description'],
                 element['Material']['SpeciesGrade'],
                 element['BottomView']['Point'][0]['X'], element['BottomView']['Point'][0]['Y'],
                 element['BottomView']['Point'][1]['X'], element['BottomView']['Point'][1]['Y'],
                 element['BottomView']['Point'][2]['X'], element['BottomView']['Point'][2]['Y'],
                 element['BottomView']['Point'][3]['X'], element['BottomView']['Point'][3]['Y'],
                 element['ElevationView']['Point'][0]['X'], element['ElevationView']['Point'][0]['Y'],
                 element['ElevationView']['Point'][1]['X'], element['ElevationView']['Point'][1]['Y'],
                 element['ElevationView']['Point'][2]['X'], element['ElevationView']['Point'][2]['Y'],
                 element['ElevationView']['Point'][3]['X'], element['ElevationView']['Point'][3]['Y'], str(sub_ctr)),
            )
        elif elem_type == 'Sub Assembly':
            self.elementIN.append(
                (element['PanelGuid'], element['SubAssemblyGuid'], elem_type,
                 element['FamilyMember'], element['FamilyMemberName'],
                 None, None, element['Width'], None, None, None, None, None, None, None, None,
                 None, None, None, None, None, None, None, None, None, None, str(sub_ctr)),
            )
        elif elem_type == 'Hole':
            self.elementIN.append(
                (element['PanelGuid'], element['BoardGuid'], elem_type,
                 element['FamilyMember'], element['FamilyMemberName'],
                 0, 0, 0, 0, 0, element['XLocation'], element['YLocation'], 0, 0, 0, 0,
                 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, str(sub_ctr))
            )

    def append_fastener(self, sheet):
        self.fastenerIN.append((sheet["PanelGuid"], sheet["BoardGuid"], sheet["TypeOfFastener"], sheet["EdgeSpacing"], sheet["FieldSpacing"], sheet["FastenerEndGap"]))
    def insert_job(self):
        pgDB = dbc.DB_Connect()
        pgDB.open()
        sql_serial_query = 'SELECT serial FROM cad2fab.system_jobs ORDER BY serial DESC'
        serial = pgDB.query(sql_serial_query)
        if len(serial) != 0:
            serial = int(serial[0][0]) + 1
        else:
            serial = 1
        # how to generate the serial number?
        jobIN = [(serial, self.data['MITEK_SHOPNET_MARKUP_LANGUAGE_FILE']['Job']['JobID']), ]
        # Header List
        # Query used for inserting the data
        sql_insert_query = """
        INSERT INTO cad2fab.system_jobs(serial,jobid,loaddate)
        VALUES (%s,%s,NOW())
        ON CONFLICT (jobid)
        DO UPDATE SET loaddate = NOW(), jobid = EXCLUDED.jobid, serial = EXCLUDED.serial;
        """
        pgDB.query_many(sql_insert_query, jobIN)
        pgDB.close()

    def insert_bundle(self):
        # List to insert to bundles table
        bundleIN = []
        # Loop through all levels in the job
        docdata = self.data['MITEK_SHOPNET_MARKUP_LANGUAGE_FILE']["Job"]
        leveled = docdata["Level"]
        if type(leveled) == dict:
            data = [leveled]
        else:
            data = leveled
        for level in data:
            # Loop through all bundles in the level
            for bundle in level["Bundle"]:
                # Data to import to the database
                bundleIN.append(
                    (bundle['BundleGuid'], bundle['JobID'], level['Description'], bundle['Label'], bundle['Type']), )
        pgDB = dbc.DB_Connect()
        pgDB.open()
        # Query used for inserting data to the database
        sql_insert_query = """
        INSERT INTO cad2fab.system_bundles(bundleguid,jobid,level_description,label,type)
        VALUES (%s,%s,%s,%s,%s)
        ON CONFLICT (bundleguid)
        DO UPDATE SET jobid = EXCLUDED.jobid, level_description = EXCLUDED.level_description,
        label = EXCLUDED.label, type = EXCLUDED.type;
        """
        pgDB.query_many(sql_insert_query, bundleIN)
        pgDB.close()

    def insert_panel(self):
        c = 0
        # List column data for panels table
        panelIN = []
        HeaderInfo = []
        # Loop through all the levels in the job
        docdata = self.data['MITEK_SHOPNET_MARKUP_LANGUAGE_FILE']["Job"]
        leveled = docdata["Level"]
        if type(leveled) == dict:
            data = [leveled]
        else:
            data = leveled
        for level in data:
            # Loop through all the bundles in the level
            for bundle in level["Bundle"]:
                # Loop through all the panels in the bundle
                for panel in bundle['Panel']:
                    self.parse_progress.panels_total += 1
                    # Check if the panel is a string
                    # The panel is a string if it is the only panel in a bundle
                    if type(panel) == str:
                        # This would remove very top plates from the panel height
                        height = float(bundle['Panel']['Height'])
                        if height == 97.125 or height == 109.125 or height == 113.125:
                            height = str(height - 1.5)
                        # All params of the panel are a different string, only add one data to the query
                        if c == 0:
                            panelIN.append((bundle['Panel']['BundleGuid'], bundle['Panel']['PanelGuid'],
                                            bundle['Panel']['Label'], height,
                                            bundle['Panel']['Thickness'], bundle['Panel']['StudSpacing'],
                                            bundle['Panel']['StudHeight'], bundle['Panel']['WallLength'],
                                            bundle['Panel']['Category'], bundle['Panel']['BoardFeet']), )

                            HeaderInfo.append((self.sCadFilepath, bundle['Panel']['BundleGuid'],
                                               bundle['Panel']['PanelGuid'], round(float(height) * 25.4),
                                               round(float(bundle['Panel']['WallLength']) * 25.4),
                                               round(float(bundle['Panel']['Thickness']) * 25.4), 1), )
                        c += 1
                        # reset counter at the end of the strings
                        if c == 29:
                            c = 0
                        # Skip to the next loop if the panel was a string
                        continue
                    # Get the data for non-string panels
                    # This would remove very top plates from the panel height
                    height = float(panel['Height'])
                    if height == 97.125 or height == 109.125 or height == 113.125:
                        height = str(height - 1.5)
                    panelIN.append((panel['BundleGuid'], panel['PanelGuid'], panel['Label'],
                                    height, panel['Thickness'], panel['StudSpacing'],
                                    panel['StudHeight'], panel['WallLength'], panel['Category'],
                                    panel['BoardFeet']), )

                    HeaderInfo.append((self.sCadFilepath, panel['BundleGuid'], panel['PanelGuid'],
                                       round(float(height) * 25.4), round(float(panel['WallLength']) * 25.4),
                                       round(float(panel['Thickness']) * 25.4), 1), )

        # Insert the panel data to the Database
        pgDB = dbc.DB_Connect()
        pgDB.open()
        # Query used for writing data to the database
        sql_insert_query = """
        INSERT INTO cad2fab.system_panels(bundleguid, panelguid, label, height, thickness,
        studspacing, studheight, walllength, category, boardfeet)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (panelguid)
        DO UPDATE SET bundleguid = EXCLUDED.bundleguid, label = EXCLUDED.label,
        height = EXCLUDED.height,
        thickness = EXCLUDED.thickness, studspacing = EXCLUDED.studspacing,
        studheight = EXCLUDED.studheight, walllength = EXCLUDED.walllength,
        category = EXCLUDED.category, boardfeet = EXCLUDED.boardfeet;
        """
        pgDB.query_many(sql_insert_query, panelIN)
        sql_insert_query_2 = """
        INSERT INTO cad2fab.system_headers(scadfilepath,sordername,sitemname,uiitemheight,uiitemlength,uiitemthickness,uiitemid)
        VALUES(%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (sitemname)
        DO UPDATE SET uiitemheight = EXCLUDED.uiitemheight, uiitemlength = EXCLUDED.uiitemlength,
        uiitemthickness = EXCLUDED.uiitemthickness
        """
        pgDB.query_many(sql_insert_query_2, HeaderInfo)
        pgDB.close()

    def insert_elements(self):
        # Counter for strings
        c2 = 0
        # List of data for elements table
        # loop through all the levels in the job
        docdata = self.data['MITEK_SHOPNET_MARKUP_LANGUAGE_FILE']["Job"]
        leveled = docdata["Level"]
        if type(leveled) == dict:
            data = [leveled]
        else:
            data = leveled
        for level in data:
            # loop through all the bundles in the level
            for bundle in level["Bundle"]:
                # loop through all the panels in the bundle
                for panel in bundle['Panel']:
                    # check if the panel is a string type
                    if type(panel) != str:
                        # Add boards to the list if they exist
                        if 'Board' in panel.keys():
                            # loop through all the boards in the panel
                            for board in panel['Board']:
                                if board['FamilyMemberName'] != 'TopPlate':
                                    # add the board data to the list
                                    xmlParse.append_element(self, board, 'Board', None)
                                else:
                                    # add the TopPlate data to the list
                                    xmlParse.append_element(self, board, 'Board', None)
                                    # Add Hole Data to list
                                    offset = 17.3  # 439.5
                                    if 'Holes' in board.keys():
                                        holeCnt = 1
                                        subassemblyCT = 1
                                        data = board['Holes']['CircularHoleFeature']
                                        if type(data) == dict:
                                            holes = [data]
                                        else:
                                            holes = data
                                        for hole in holes:
                                            holeSet = {
                                                'PanelGuid': board['PanelGuid'],
                                                'BoardGuid': board['BoardGuid'] + '-' + str(holeCnt),
                                                'FamilyMember': board['FamilyMember'],
                                                'FamilyMemberName': 'Hole',
                                                'XLocation': str(float(hole['XLocation']) + float(board['BottomView']['Point'][0]['X']) + offset),
                                                'YLocation': hole['YLocation']
                                            }
                                            holeCnt += 1
                                            xmlParse.append_element(self, holeSet, 'Hole', subassemblyCT)
                        # Add sheets to the list if they exist
                        if 'Sheet' in panel.keys():
                            self.parse_progress.panels_exterior += 1
                            # loop through all the sheets in the panel
                            for sheet in panel['Sheet']:
                                # add the sheet data to the list
                                xmlParse.append_element(self, sheet, 'Sheet', None)
                                # Add Fastener Data to Fastener Table
                                xmlParse.append_fastener(self, sheet)
                        else:
                            self.parse_progress.panels_interior += 1
                        # Add SubAssemblies to the list if they exist and are in a list format
                        # SubAssemblies will be in list format if there are >1 in the current panel
                        if 'SubAssembly' in panel.keys() and type(panel['SubAssembly']) == list:
                            # loop through the SubAssemblies
                            subassemblyCT = 1
                            for subassembly in panel['SubAssembly']:
                                # are there boards in the subassembly?
                                if 'Board' in subassembly.keys():
                                    # loop through all the boards in the subassembly
                                    for boardsub in subassembly['Board']:
                                        # when the board isn't the rough opening board add it to the list
                                        if boardsub['FamilyMemberName'] != 'RoughOpening':
                                            xmlParse.append_element(self, boardsub, 'Sub-Assembly Board', subassemblyCT)
                                        else:  # add the rough cutout to the list
                                            # (only works when there is 1 rough out per subassembly due to element guid creation)
                                            boardsub['PanelGuid'] = subassembly['PanelGuid']
                                            boardsub['BoardGuid'] = subassembly['SubAssemblyGuid'] + str(subassemblyCT)
                                            boardsub['FamilyMember'] = subassembly['FamilyMember']
                                            boardsub['FamilyMemberName'] = 'Rough cutout'
                                            boardsub['Material']['Size'] = 0
                                            boardsub['Material']['ActualThickness'] = 0

                                            xmlParse.append_element(self, boardsub, 'Sub-Assembly Cutout',
                                                                    subassemblyCT)
                                # add subassembly without point data
                                xmlParse.append_element(self, subassembly, 'Sub Assembly', subassemblyCT)
                                subassemblyCT += 1
                        # if there is only one subassembly in the panel
                        if 'SubAssembly' in panel.keys() and type(panel['SubAssembly']) == dict:
                            # check for a rough opening sub-board
                            subassemblyCT = 1
                            # loop through all the boards in the subassembly
                            for boardsub in panel['SubAssembly']['Board']:
                                # Check if the sub board is the rough opening
                                if boardsub['FamilyMemberName'] != 'RoughOpening':

                                    xmlParse.append_element(self, boardsub, 'Sub-Assembly Board', subassemblyCT)

                                else:  # add the rough cutout to the list
                                    # (only works when there is 1 rough out per subassembly due to element guid creation)

                                    boardsub['PanelGuid'] = panel['SubAssembly']['PanelGuid']
                                    boardsub['BoardGuid'] = panel['SubAssembly']['SubAssemblyGuid'] + str(subassemblyCT)
                                    boardsub['FamilyMember'] = panel['SubAssembly']['FamilyMember']
                                    boardsub['FamilyMemberName'] = 'Rough cutout'
                                    boardsub['Material']['Size'] = 0
                                    boardsub['Material']['ActualThickness'] = 0

                                    xmlParse.append_element(self, boardsub, 'Sub-Assembly Cutout', subassemblyCT)

                            # add subassembly without point data

                            subassembly = {
                                'PanelGuid': panel['SubAssembly']['PanelGuid'],
                                'SubAssemblyGuid': panel['SubAssembly']['SubAssemblyGuid'],
                                'FamilyMember': panel['SubAssembly']['FamilyMember'],
                                'FamilyMemberName': panel['SubAssembly']['FamilyMemberName'],
                                'Width': panel['SubAssembly']['Width']
                            }
                            xmlParse.append_element(self, subassembly, 'Sub Assembly', subassemblyCT)

                    # if the panel is a string (only 1 panel in the bundle)
                    elif type(panel) == str:
                        # add the boards to the list if they exist
                        if 'Board' in bundle['Panel'].keys() and c2 == 0:
                            # loop through all the boards in the panel
                            for board in bundle['Panel']['Board']:
                                # add the data to the list
                                xmlParse.append_element(self, board, 'Board', None)
                        # add the sheets to the list if they exist
                        if 'Sheet' in bundle['Panel'].keys() and c2 == 0:
                            # loop through the sheets in the panel
                            for sheet in bundle['Panel']['Sheet']:
                                # add the data for the sheets to the list
                                xmlParse.append_element(self, sheet, 'Sheet', None)
                                xmlParse.append_fastener(self, sheet)
                        # Add Sub Assemblies to the list if they exist, are list type
                        if 'SubAssembly' in bundle['Panel'].keys() and type(
                                bundle['Panel']['SubAssembly']) == list and c2 == 0:
                            # loop through all the subassemblies
                            subassemblyCT = 1
                            for subassembly in bundle['Panel']['SubAssembly']:
                                # are there boards in the subassembly?
                                if 'Board' in subassembly.keys():
                                    # loop through all the boards in the subassembly
                                    for boardsub in subassembly['Board']:
                                        # when the board isn't the rough opening board add it to the list
                                        if boardsub['FamilyMemberName'] != 'RoughOpening':
                                            xmlParse.append_element(self, boardsub, 'Sub-Assembly Board', subassemblyCT)
                                        else:  # add the rough cutout to the list
                                            # (only works when there is 1 rough out per subassembly due to element guid creation)
                                            boardsub['PanelGuid'] = subassembly['PanelGuid']
                                            boardsub['BoardGuid'] = subassembly['SubAssemblyGuid'] + str(subassemblyCT)
                                            boardsub['FamilyMember'] = subassembly['FamilyMember']
                                            boardsub['FamilyMemberName'] = 'Rough cutout'
                                            boardsub['Material']['Size'] = 0
                                            boardsub['Material']['ActualThickness'] = 0
                                            # boardsub['Material']['MaterialsId']

                                            xmlParse.append_element(self, boardsub, 'Sub-Assembly Cutout',
                                                                    subassemblyCT)

                                # add subassembly without point data
                                xmlParse.append_element(self, subassembly, 'Sub Assembly', subassemblyCT)
                                subassemblyCT += 1
                        # Add the subassembly if it exists and is dictionary type
                        if 'SubAssembly' in bundle['Panel'].keys() and type(
                                bundle['Panel']['SubAssembly']) == dict and c2 == 0:
                            # check if the subassembly has a rough opening in the panel
                            subassemblyCT = 1
                            # loop through all the boards in the subassembly
                            #for boardsub in bundle['Panel']['SubAssembly']['Board']:
                            # TODO Determine double board sub looping
                            for boardsub in panel['SubAssembly']['Board']:
                                # Check if the sub board is the rough opening
                                if boardsub['FamilyMemberName'] != 'RoughOpening':
                                    xmlParse.append_element(self, boardsub, 'Sub-Assembly Board', subassemblyCT)
                                else:  # add the rough cutout to the list
                                    # (only works when there is 1 rough out per subassembly due to element guid creation)
                                    boardsub['PanelGuid'] = panel['SubAssembly']['PanelGuid']
                                    boardsub['BoardGuid'] = panel['SubAssembly']['SubAssemblyGuid'] + str(subassemblyCT)
                                    boardsub['FamilyMember'] = panel['SubAssembly']['FamilyMember']
                                    boardsub['FamilyMemberName'] = 'Rough cutout'
                                    boardsub['Material']['Size'] = 0
                                    boardsub['Material']['ActualThickness'] = 0
                                    # boardsub['Material']['MaterialsId']

                                    xmlParse.append_element(self, boardsub, 'Sub-Assembly Cutout', subassemblyCT)
                            # add subassembly without point data
                            subassembly = {
                                'PanelGuid': panel['SubAssembly']['PanelGuid'],
                                'SubAssemblyGuid': panel['SubAssembly']['SubAssemblyGuid'],
                                'FamilyMember': panel['SubAssembly']['FamilyMember'],
                                'FamilyMemberName': panel['SubAssembly']['FamilyMemberName'],
                                'Width': panel['SubAssembly']['Width']
                            }
                            xmlParse.append_element(self, subassembly, 'Sub Assembly', subassemblyCT)
                    c2 += 1
                    # reset counter after 1 string panel
                    if c2 == 29:
                        c2 = 0

        # insert the list to the database
        pgDB = dbc.DB_Connect()
        pgDB.open()
        print("Insert Elements")
        # Query used for writing data to the database
        sql_insert_query = """
        INSERT INTO cad2fab.system_elements(panelguid,elementguid,type,familymember,description,
                            size,actual_thickness,actual_width,materialdesc,species,b1x,b1y,b2x,
                            b2y,b3x,b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,assembly_id)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (elementguid)
        DO UPDATE SET panelguid = EXCLUDED.panelguid, type = EXCLUDED.type,
        familymember = EXCLUDED.familymember, description = EXCLUDED.description,
        size = EXCLUDED.size,actual_thickness = EXCLUDED.actual_thickness,
        actual_width = EXCLUDED.actual_width,materialdesc = EXCLUDED.materialdesc,species = EXCLUDED.species,
        b1x = EXCLUDED.b1x,b1y = EXCLUDED.b1y,b2x = EXCLUDED.b2x,b2y = EXCLUDED.b2y,
        b3x = EXCLUDED.b3x,b3y = EXCLUDED.b3y,b4x = EXCLUDED.b4x,b4y = EXCLUDED.b4y,
        e1x = EXCLUDED.e1x,e1y = EXCLUDED.e1y,e2x = EXCLUDED.e2x,e2y = EXCLUDED.e2y,
        e3x = EXCLUDED.e3x,e3y = EXCLUDED.e3y,e4x = EXCLUDED.e4x,e4y = EXCLUDED.e4y,
        assembly_id = EXCLUDED.assembly_id;
        """
        pgDB.query_many(sql_insert_query, self.elementIN)

        sql_insert_fasteners = """
        INSERT INTO cad2fab.system_fasteners
        (panelguid, elementguid, fastener_type, edge_spacing, field_spacing, fastener_end_gap)
        VALUES(%s,%s,%s,%s,%s,%s)
        ON CONFLICT (panelguid, elementguid)
        DO UPDATE SET fastener_type = EXCLUDED.fastener_type, edge_spacing = EXCLUDED.edge_spacing, 
        field_spacing = EXCLUDED.field_spacing, fastener_end_gap = EXCLUDED.fastener_end_gap;
        """
        pgDB.query_many(sql_insert_fasteners, self.fastenerIN)
        pgDB.close()

    def xml_main(self):
        self.insert_job()
        self.insert_bundle()
        self.insert_panel()
        self.insert_elements()

# if __name__ == "__main__":
# 	#get filepath to XML file from user
# 	#filepath = "Python_Script/dataExtract_EHX/xmlFiles/231769W2.xml"
# 	filepath = r"Python_Script\dataExtract_EHX\xmlFiles\RANDEK TEST PANELS.EHX"

# 	#init the class
# 	xmlParse(filepath)
# 	#parse the data and send to DB
# 	xmlParse.xmlMain(xmlParse)


# Written by Jacob OBrien for BraveCS
# March 2023
