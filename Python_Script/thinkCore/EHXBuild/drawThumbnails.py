from PIL import Image, ImageDraw  # Requires Python >=3.7, pip install Pillow
# from PIL.ImageDraw import ImageDraw
from util.globals import Parse_Progress
from util import dataBaseConnect as dbc
import os


# import math								#Built in to Python, only needed for safe rounding

class GenPreview:
    def __init__(self, job_id, path) -> None:
        self.draw_progress = Parse_Progress()
        self.path = path
        # get credentials an open the database
        pgDB = dbc.DB_Connect()
        pgDB.open()
        # select the panelguids and bundleids from the database
        sql_select_query = f"""SELECT * 
                            FROM cad2fab.system_panels sp 
                            JOIN cad2fab.system_bundles sb  ON sp.bundleguid  = sb.bundleguid 
                            WHERE sb.jobid = '{job_id}'"""
        self.panelData = []
        result = pgDB.query(sql_select_query)
        self.panelData = result
        # select the panelguid, elementguid, type, and elevation points from the elements table
        self.elementData = []
        sql_select_query = f"""SELECT se.panelguid, jsonb_build_array(se.panelguid, se.elementguid, se."type" , se.e1x, se.e1y, se.e2x, se.e2y, se.e3x, se.e3y, se.e4x, se.e4y)
                            FROM cad2fab.system_elements se
                            inner JOIN cad2fab.system_panels sp ON se.panelguid  = sp.panelguid
                            inner join cad2fab.system_bundles sb on sb.bundleguid = sp.bundleguid
                            WHERE sb.jobid = '{job_id}'"""
        result2 = pgDB.query(sql_select_query)
        # for row in result2:
        #    self.elementData.append([row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10]])

        # self.eley = []
        self.elementData.extend(result2)
        pgDB.close()

    def previewMain(self):
        # loop through all panelData rows, ct is counter, row is data
        path = self.path
        if len(self.panelData) > 0:
            cunt = 0
            for row in self.panelData:
                cunt += 1
                print(str(cunt) + '---' + row[1])
                # get the jobID of the current panel
                pgDB = dbc.DB_Connect()
                jobid = row[11]

                # if output/jobID doesn't exist create the folder then set name = filepath/panelguid.png
                if not os.path.exists(path + f'/{jobid}/'):
                    os.makedirs(path + f'/{jobid}/')
                if not os.path.exists(path + f'/{jobid}/{row[0]}'):
                    os.makedirs(path + f'/{jobid}/{row[0]}')
                if not os.path.exists(path + f'/{jobid}/{row[0]}/Assemblies'):
                    os.makedirs(path + f'/{jobid}/{row[0]}/Assemblies')

                name = (path + f'/{jobid}/{row[0]}/{row[0]}' + '.png')
                panel_data = list(filter(lambda text: row[1] in text, self.elementData))
                self.build_image(name, row, panel_data)
                sqlPanel = row[1]
                pgDB.open()
                sql_assemblies = f"""SELECT distinct assembly_id 
                from cad2fab.system_elements se 
                where panelguid = '{sqlPanel}' and type = 'Sub Assembly' and assembly_id is not null;"""
                assemblies = pgDB.query(sql_assemblies)
                for assembly in assemblies:
                    print("Build Sub")
                    # Get Assembly Data from Elements
                    sql_assembly = f"""select se.panelguid, jsonb_build_array(se.panelguid, se.elementguid, se."type" , se.e1x, se.e1y, se.e2x, se.e2y, se.e3x, se.e3y, se.e4x, se.e4y)
                    	            from cad2fab.system_elements se 
                                    where panelguid = '{sqlPanel}' and assembly_id = '{assembly[0]}' """
                    subElements = pgDB.query(sql_assembly)
                    # Get Assembly Data from Elements
                    sql_Name = f"""select description 
                                from cad2fab.system_elements se
                                where 
                                    panelguid = '{sqlPanel}' and 
                                    assembly_id = '{assembly[0]}' and 
                                    
                                    "size" is Null;"""
                    assName = pgDB.query(sql_Name)
                    name = (path + f'/{jobid}/{row[0]}/' + 'Assemblies/' + assName[0][0] + '-' + str(
                        assembly[0]) + '.png')
                    subs = []
                    #for sub in subElements:
                    #    subs.append([sub[0], sub[1], sub[2], sub[17], sub[18], sub[19], sub[20], sub[21], sub[22], sub[23], sub[24]])
                    subs.extend(subElements)
                    self.build_image(name, row, subs)

    def build_image(self, name, panel, element_data):
        row = panel

        # find the boundaries of each panel
        min_height = 10000
        max_height = 0
        min_width = 10000
        max_width = 0

        for elem_row in element_data:
            elem_row = elem_row[1]
            # if the element is the same panel and is a board or a sheet
            if row[1] == elem_row[0] and ((elem_row[2] == 'Board' or elem_row[2] == 'Sheet') or elem_row[2] == 'Sub-Assembly Board'):
                # find max and min X values of the current panel
                if elem_row[3] > max_width:
                    max_width = elem_row[3]
                if elem_row[5] > max_width:
                    max_width = elem_row[5]
                if elem_row[7] > max_width:
                    max_width = elem_row[7]
                if elem_row[9] > max_width:
                    max_width = elem_row[9]
                if elem_row[3] < min_width:
                    min_width = elem_row[3]
                if elem_row[5] < min_width:
                    min_width = elem_row[5]
                if elem_row[7] < min_width:
                    min_width = elem_row[7]
                if elem_row[9] < min_width:
                    min_width = elem_row[9]
                # find max and min y values of the current panel
                if elem_row[4] > max_height:
                    max_height = elem_row[4]
                if elem_row[6] > max_height:
                    max_height = elem_row[6]
                if elem_row[8] > max_height:
                    max_height = elem_row[8]
                if elem_row[10] > max_height:
                    max_height = elem_row[10]
                if elem_row[4] < min_height:
                    min_height = elem_row[4]
                if elem_row[6] < min_height:
                    min_height = elem_row[6]
                if elem_row[8] < min_height:
                    min_height = elem_row[8]
                if elem_row[10] < min_height:
                    min_height = elem_row[10]

        # get scaling factor for points
        height = max_height - min_height
        width = max_width - min_width
        # check if the max scale is based on width or height
        if 1000 / height <= 1840 / width:
            scale = 1000 / height
        # code for safe scale rounding
        # scale = int(math.floor(1000/height))
        elif 1840 / width < 1000 / height:
            scale = 1840 / width
        # code for safe scale rounding
        # scale = int(math.floor(1840/width))

        # translate the elements such that the starting point is (0,0)
        translateX = min_width
        translateY = min_height
        scaledWidth = int(width * scale) + 80
        if scaledWidth > 1920:
            scaledWidth = 1920
        # Image background (color type, size(px), (R,G,B,Transparency))
        out_image = Image.new('RGBA', (scaledWidth, 1080), (255, 255, 255, 255))
        # Enter draw mode
        draw: ImageDraw = ImageDraw.Draw(out_image)

        for elem_row in element_data:
            elem_row = elem_row[1]
            # if the element is a board or sub assembly board draw it
            if elem_row[0] == row[1] and (elem_row[2] == 'Board' or elem_row[2] == 'Sub-Assembly Board'):
                coordinates = [(int(round((elem_row[3] - translateX) * scale)) + 40,
                                int(round((elem_row[4] - translateY) * scale)) + 40),
                               (int(round((elem_row[5] - translateX) * scale)) + 40,
                                int(round((elem_row[6] - translateY) * scale)) + 40),
                               (int(round((elem_row[7] - translateX) * scale)) + 40,
                                int(round((elem_row[8] - translateY) * scale)) + 40),
                               (int(round((elem_row[9] - translateX) * scale)) + 40,
                                int(round((elem_row[10] - translateY) * scale)) + 40)]
                # draw a polygon connecting the points, fill is Null, outline is (RGBA) and width is px
                draw.polygon(coordinates, fill=(255, 201, 14, 255), outline=(0, 0, 0, 255), width=2)
        # loop through all elements
        for elem_row in element_data:
            elem_row = elem_row[1]
            # if the element belongs to the current panel and is a sheet draw it
            if elem_row[0] == row[1] and elem_row[2] == 'Sheet':
                coordinates = [(int(round((elem_row[3] - translateX) * scale)) + 40,
                                int(round((elem_row[4] - translateY) * scale)) + 40),
                               (int(round((elem_row[5] - translateX) * scale)) + 40,
                                int(round((elem_row[6] - translateY) * scale)) + 40),
                               (int(round((elem_row[7] - translateX) * scale)) + 40,
                                int(round((elem_row[8] - translateY) * scale)) + 40),
                               (int(round((elem_row[9] - translateX) * scale)) + 40,
                                int(round((elem_row[10] - translateY) * scale)) + 40)]
                # draw a polygon connecting the points, fill & outline are (RGBA) and width is px
                draw.polygon(coordinates, fill=(0, 154, 255, 255), outline=(127, 127, 127, 127), width=1)
        # loop through all elements again (drawings are layered, so this is required)
        # Draw Datum Corner
        coordinates = [(10, 75), (5, 70), (10, 75), (15, 80), (10, 75), (10, 10), (75, 10), (70, 15), (75, 10), (70, 5), (75, 10)]
        draw.polygon(coordinates, fill=None, outline=(0, 0, 0, 255), width=2)
        draw.text((8, 80), "Y", align="center")
        draw.text((80, 8), "X", align="center")

        # Flip the image vertically (0,0 is the top left, which is being changed to the bottom left)
        out_image = out_image.transpose(method=Image.FLIP_TOP_BOTTOM)
        # out_image = out_image.transpose(method=Image.FLIP_LEFT_RIGHT)
        # Output PNG image
        self.draw_progress.image_count += 1
        out_image.save(name)

# if __name__ == "__main__":
# 	GenPreview.__init__(GenPreview)
# 	GenPreview.previewMain(GenPreview)

# Written by Jacob OBrien for BraveCS♥
# March 2023
