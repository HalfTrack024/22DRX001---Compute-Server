import util.dataBaseConnect as dbc
from util.Parameters import Parameters


# this class is designed to check positional okayness of the framing units Hammer and Stud Stop on both the Mobile and Fix Sides
class Clear:
    def __init__(self, connect) -> None:
        parmData = Parameters([], 1, 2)

        # dbc.printResult(results)
        # assign results of query to variables
        # thickness is in the X direction of elevation, width/length in the Y direction
        self.ss_thickness = round(parmData.getParm('Positions', 'Stud Stop thickness') / 25.4, 2)
        self.ss_width = round(parmData.getParm('Positions', 'Stud Stop width') / 25.4, 2)
        self.hu_thickness = round(parmData.getParm('Positions', 'Hammer Units Thickness') / 25.4, 2)
        self.hu_length = round(parmData.getParm('Positions', 'Hammer Units Length') / 25.4, 2)
        self.hu_stroke = round(parmData.getParm('Positions', 'Hammer Units Stroke') / 25.4, 2)
        self.hu_Y = round(parmData.getParm('Positions', 'Positions:lrHammerUnitYCenterPosition') / 25.4, 2)

        self.pgDB = connect

    def studStopFS(self, elementguid):
        # self.pgDB.open()
        # query the e1x, panelid and type from the current element
        sql_select_query = f"""
                        SELECT e1x, panelguid, type
                        FROM cad2fab.system_elements
                        WHERE elementguid = '{elementguid}' 
                        ORDER BY e1x ASC;
                        """
        results = self.pgDB.query(sql_select_query)
        # if the current element is a rough cutout don't stud stop
        if results[0][2] == 'Sub-Assembly Cutout':
            return False
        # set maximum and minimum values after converting to mm
        MinX = str(round(float(results[0][0]) - self.ss_thickness, 3))
        MaxX = str(round(float(results[0][0]), 3))
        MinY = str(1.5)
        MaxY = str(round(1.5 + self.ss_width, 3))
        # select elements in the bounds of the max and min, in the current panel, excluding the current element and elements with
        # a description of sheathing,TopPlate,BottomPlate, and VeryTopPlate
        sql_select_query = f"""
                        SELECT e1x
                        FROM cad2fab.system_elements
                        WHERE panelguid = '{results[0][1]}' and description NOT IN ('Sheathing','TopPlate','BottomPlate','VeryTopPlate','Nog')
                        and elementguid != '{elementguid}' and type != 'Sheet'
                        and (({MinX} <= (e1x) and (e1x) <= {MaxX} and (e1y) <= {MaxY}) 
                        or ({MinX} <= (e4x) and (e4x) <= {MaxX} and (e4y) <= {MaxY}));
                        """
        results2 = self.pgDB.query(sql_select_query)
        # self.pgDB.close()
        # if there aren't any results the SS is clear
        if results2 == []:
            SSF_Clear = True
        else:
            SSF_Clear = False

        return SSF_Clear

    def hammerFS(self, elementguid):
        # self.pgDB.open()
        # query the e4x, panelid and type from the current element
        sql_select_query = f"""
                        SELECT e4x, panelguid, type, description
                        FROM cad2fab.system_elements
                        WHERE elementguid = '{elementguid}'
                        ORDER BY e4x ASC;
                        """
        results = self.pgDB.query(sql_select_query)
        # if the current element is a rough cutout don't hammer
        # if the current element is a sub assembly board
        if results[0][2] == "Sub-Assembly Board":
            # convert to mm and set max/min values
            MinX = str(round(float(results[0][0]), 3))
            MaxX = str(round(float(results[0][0]) + self.hu_length + self.hu_stroke, 3))
            MinY = str(round(1.5 + self.hu_Y, 3))
            MaxY = str(round(1.5 + self.hu_Y + self.hu_thickness, 3))
            # select elements in the current panel and within the min/max bounds, that aren't sheathing, top plate,
            # bottom plate, or very top plate and aren't the current element
            sql_select_query = f"""
                            SELECT *
                            FROM cad2fab.system_elements
                            WHERE panelguid = '{results[0][1]}' and description NOT IN 
                            ('Sheathing','TopPlate','BottomPlate','VeryTopPlate','Nog') and elementguid != '{elementguid}' 
                            and type != 'Sheet'
                            and (({MinX} <= e1x and e1x <= {MaxX} and e1y <= {MaxY}) 
                            or ({MinX} <= e4x and e4x <= {MaxX} and e4y <= {MaxY}));
                            """
            results = self.pgDB.query(sql_select_query)
            # self.pgDB.close()
            # if the hammer is clear return true
            if results == []:
                SSM_Clear = True
            else:
                SSM_Clear = False
        # if the element is a standard stud return true
        elif results[0][2] == "Board" and results[0][3] == "Stud":
            SSM_Clear = True
        else:
            SSM_Clear = False

        return SSM_Clear

    def studStopMS(self, elementguid):
        # self.pgDB.open()
        # query e2x, panelguid, type of the current element
        sql_select_query = f"""
                        SELECT e2x, panelguid, type
                        FROM cad2fab.system_elements
                        WHERE elementguid = '{elementguid}'
                        ORDER BY e2x ASC;
                        """
        results = self.pgDB.query(sql_select_query)
        # if the current element is a cutout return false
        if results[0][2] == 'Sub-Assembly Cutout':
            return False
        # query the studheight from the panels table
        sql_select_query = f"""
                        SELECT studheight
                        FROM cad2fab.system_panels
                        WHERE panelguid = '{results[0][1]}'
                        """
        height = self.pgDB.query(sql_select_query)
        # set the min and max values for the SS boundries
        MinX = str(round(float(results[0][0]) - self.ss_thickness, 3))
        MaxX = str(round(float(results[0][0]), 3))
        MinY = str(round(float(height[0][0]) + 1.5 - self.ss_width, 3))
        MaxY = str(round(float(height[0][0]) + 1.5, 3))
        # select elements within the bounds and panel, that aren't sheathing, topplate, bottom plate,
        # or very top plate and aren't the current element
        sql_select_query = f"""
                        SELECT e2x
                        FROM cad2fab.system_elements
                        WHERE panelguid = '{results[0][1]}' and description NOT IN ('Sheathing','TopPlate','BottomPlate','VeryTopPlate','Nog')
                        and elementguid != '{elementguid}' and type != 'Sheet'
                        and (({MinX} <= (e2x) and (e2x) <= {MaxX} and (e2y) <= {MaxY}) 
                        or ({MinX} <= (e3x) and (e3x) <= {MaxX} and (e3y) <= {MaxY}));
                        """
        results2 = self.pgDB.query(sql_select_query)
        # self.pgDB.close()
        # if stud stop is clear return true
        if results2 == []:
            SSF_Clear = True
        else:
            SSF_Clear = False

        return SSF_Clear

    def hammerMS(self, elementguid):
        # self.pgDB.open()
        # query e3x, panelguid and type from the current element
        sql_select_query = f"""
                        SELECT e3x, panelguid, type, description
                        FROM cad2fab.system_elements
                        WHERE elementguid = '{elementguid}'
                        ORDER BY e3x ASC;
                        """
        results = self.pgDB.query(sql_select_query)
        # query the studheight from the panels table
        sql_select_query = f"""
                        SELECT studheight
                        FROM cad2fab.system_panels
                        WHERE panelguid = '{results[0][1]}'
                        """
        height = self.pgDB.query(sql_statement=sql_select_query)
        if results[0][2] == "Sub-Assembly Board":
            # if the element is a sub assembly obard set the boundries
            MinX = str(round(float(results[0][0]), 3))
            MaxX = str(round(float(results[0][0]) + self.hu_length + self.hu_stroke, 3))
            MinY = str(round(float(height[0][0]) + 1.5 - self.hu_Y - self.hu_thickness, 3))
            MaxY = str(round(float(height[0][0]) + 1.5, 3))
            # select elements in the current panel and within the bounds that aren't the current element and aren't 
            # sheathing, top plate, bottom plate, or very top plate
            sql_select_query = f"""
                            SELECT *
                            FROM cad2fab.system_elements
                            WHERE panelguid = '{results[0][1]}' and description NOT IN ('Sheathing','TopPlate','BottomPlate','VeryTopPlate','Nog')
                            and elementguid != '{elementguid}' and type != 'Sheet'
                            and (({MinX} <= e2x and e2x <= {MaxX} and e2y <= {MaxY}) 
                            or ({MinX} <= e3x and e3x <= {MaxX} and e3y <= {MaxY}));
                            """
            results = self.pgDB.query(sql_statement=sql_select_query)
            # self.pgDB.close()
            # if the hammer is clear return true
            if results == []:
                SSM_Clear = True
            else:
                SSM_Clear = False

        # if the  current element is a standard stud return true
        elif results[0][2] == "Board" and results[0][3] == "Stud":
            SSM_Clear = True
        else:
            SSM_Clear = False

        return SSM_Clear

# if __name__ == "__main__":
#     board = Clear()
#     #Elementtemp = board.studStopMS('1efbe9e1-83e9-4dad-8c50-664bfc5e292a')
#     #print (Elementtemp)
