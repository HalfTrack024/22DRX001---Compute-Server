import dataBaseConnect as dbc
# this class is designed to check positional okayness of the framing units Hammer and Stud Stop on both the Mobile and Fix Sides
class Clear:
    def __init__(self) -> None:
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        #get parameters for stud stop and hammer that are universal
        sql_select_query="""
                        SELECT description, value
                        FROM EC1_parameters
                        WHERE description IN (  'Stud Stop thickness', 
                                                'Stud Stop width', 
                                                'Hammer Units Thickness', 
                                                'Hammer Units Length', 
                                                'Hammer Units Stroke',
                                                'Positions:lrHammerUnitYCenterPosition'
                                                );
                        """
        
        results = pgDB.query(sql_select_query)
        #dbc.printResult(results)
        #assign results of query to variables
        #thickness is in the X direction of elevation, width/length in the Y direction
        self.ss_thickness = float(results[0][1])
        self.ss_width = float(results[1][1])
        self.hu_thickness = float(results[2][1])
        self.hu_length = float(results[3][1])
        self.hu_stroke = float(results[4][1])
        self.hu_Y = float(results[5][1])
        pgDB.close()
        
    def studStopFS(self, elementguid):
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        #query the e1x, panelid and type from the current element
        sql_select_query=f"""
                        SELECT e1x, panelguid, type
                        FROM elements
                        WHERE elementguid = '{elementguid}' 
                        ORDER BY e1x ASC;
                        """
        results = pgDB.query(sql_select_query)
        #if the current element is a rough cutout don't stud stop
        if results[0][2] == 'Sub-Assembly Cutout':
            return False
        #set maximum and minimum values after converting to mm
        MinX = str(round(float(results[0][0]) * 25.4 - self.ss_thickness,1))
        MaxX = str(round(float(results[0][0]) * 25.4,1))
        MinY = str(38.1)
        MaxY = str(round(38.1 + self.ss_width,1))
        #select elements in the bounds of the max and min, in the current panel, excluding the current element and elements with 
        # a description of sheathing,TopPlate,BottomPlate, and VeryTopPlate
        sql_select_query=f"""
                        SELECT e1x
                        FROM elements
                        WHERE panelguid = '{results[0][1]}' and description NOT IN ('Sheathing','TopPlate','BottomPlate','VeryTopPlate')
                        and elementguid != '{elementguid}' and type != 'Sheet'
                        and (({MinX} <= (e1x * 25.4) and (e1x * 25.4) <= {MaxX} and {MinY} <= (e1y * 25.4) and (e1y * 25.4) <= {MaxY}) 
                        or ({MinX} <= (e4x * 25.4) and (e4x * 25.4) <= {MaxX} and {MinY} <= (e4y * 25.4) and (e4y * 25.4) <= {MaxY}));
                        """
        results2 = pgDB.query(sql_select_query)
        pgDB.close()
        #if there aren't any results the SS is clear
        if results2 == []:
            SSF_Clear = True
            return SSF_Clear        

    def hammerFS(self,elementguid):
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        #query the e4x, panelid and type from the current element
        sql_select_query=f"""
                        SELECT e4x, panelguid, type
                        FROM elements
                        WHERE elementguid = '{elementguid}'
                        ORDER BY e4x ASC;
                        """
        results = pgDB.query(sql_select_query)
        #if the current element is a rough cutout don't hammer
        #if the current element is a sub assembly board
        if results[0][2] == "Sub-Assembly Board":
            # convert to mm and set max/min values
            MinX = str(round(float(results[0][0]) * 25.4,1))
            MaxX = str(round(float(results[0][0]) * 25.4 + self.hu_length + self.hu_stroke,1))
            MinY = str(round(38.1 + self.hu_Y,1))
            MaxY = str(round(38.1 + self.hu_Y + self.hu_thickness,1))
            #select elements in the current panel and within the min/max bounds, that aren't sheathing, top plate,
            #bottom plate, or very top plate and aren't the current element
            sql_select_query=f"""
                            SELECT e2x
                            FROM elements
                            WHERE panelguid = '{results[0][1]}' and description NOT IN 
                            ('Sheathing','TopPlate','BottomPlate','VeryTopPlate') and elementguid != '{elementguid}' 
                            and type != 'Sheet'
                            and (({MinX} <= e1x and e1x <= {MaxX} and {MinY} <= e1y and e1y <= {MaxY}) 
                            or ({MinX} <= e4x and e4x <= {MaxX} and {MinY} <= e4y and e4y <= {MaxY}));
                            """
            results = pgDB.query(sql_select_query)
            pgDB.close()
            # if the hammer is clear return true
            if results == []:
                SSM_Clear = True
                return SSM_Clear
        # if the element is a standard stud return true
        elif results[0][2] == "Board" and results[0][3] == "Stud":
            SSM_Clear = True
            return SSM_Clear
        
    def studStopMS(self,elementguid):
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        #query e2x, panelguid, type of the current element
        sql_select_query=f"""
                        SELECT e2x, panelguid, type
                        FROM elements
                        WHERE elementguid = '{elementguid}'
                        ORDER BY e2x ASC;
                        """
        results = pgDB.query(sql_select_query)
        # if the current element is a cutout return false
        if results[0][2] == 'Sub-Assembly Cutout':
            return False
        #query the studheight from the panels table
        sql_select_query=f"""
                        SELECT studheight
                        FROM panel
                        WHERE panelguid = '{results[0][1]}'
                        """
        height = pgDB.query(sql_select_query)
        # set the min and max values for the SS boundries
        MinX = str(round(float(results[0][0]) * 25.4 - self.ss_thickness,1))
        MaxX = str(round(float(results[0][0]) * 25.4,1))
        MinY = str(round(float(height[0][0]) * 25.4 + 38.1 - self.ss_width,1))
        MaxY = str(round(float(height[0][0]) * 25.4 + 38.1,1))
        #select elements within the bounds and panel, that aren't sheathing, topplate, bottom plate, 
        # or very top plate and aren't the current element
        sql_select_query=f"""
                        SELECT e2x
                        FROM elements
                        WHERE panelguid = '{results[0][1]}' and description NOT IN ('Sheathing','TopPlate','BottomPlate','VeryTopPlate')
                        and elementguid != '{elementguid}' and type != 'Sheet'
                        and (({MinX} <= (e2x * 25.4) and (e2x * 25.4) <= {MaxX} and {MinY} <= (e2y * 25.4) and (e2y * 25.4) <= {MaxY}) 
                        or ({MinX} <= (e3x * 25.4) and (e3x * 25.4) <= {MaxX} and {MinY} <= (e3y * 25.4) and (e3y * 25.4) <= {MaxY}));
                        """
        results2 = pgDB.query(sql_select_query)
        pgDB.close()
        #if stud stop is clear return true
        if results2 == []:
            SSF_Clear = True
            return SSF_Clear 
        
    def hammerMS(self,elementguid):
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        # query e3x, panelguid and type from the current element
        sql_select_query=f"""
                        SELECT e3x, panelguid, type
                        FROM elements
                        WHERE elementguid = '{elementguid}'
                        ORDER BY e3x ASC;
                        """
        results = pgDB.query(sql_select_query)
        #query the studheight from the panels table
        sql_select_query=f"""
                        SELECT studheight
                        FROM panel
                        WHERE panelguid = '{results[0][1]}'
                        """
        height = pgDB.query(sqlStatement=sql_select_query)
        if results[0][2] == "Sub-Assembly Board":
            # if the element is a sub assembly obard set the boundries
            MinX = str(round(float(results[0][0]) * 25.4 ,1))
            MaxX = str(round(float(results[0][0]) * 25.4 + self.hu_length + self.hu_stroke,1))
            MinY = str(round(float(height[0][0]) * 25.4 + 38.1 - self.hu_Y - self.hu_thickness,1))
            MaxY = str(round(float(height[0][0]) * 25.4 + 38.1 - self.hu_Y,1))
            # select elements in the current panel and within the bounds that aren't the current element and aren't 
            # sheathing, top plate, bottom plate, or very top plate
            sql_select_query=f"""
                            SELECT e3x
                            FROM elements
                            WHERE panelguid = '{results[0][1]}' and description NOT IN ('Sheathing','TopPlate','BottomPlate','VeryTopPlate')
                            and elementguid != '{elementguid}' and type != 'Sheet'
                            and (({MinX} <= e2x and e2x <= {MaxX} and {MinY} <= e2y and e2y <= {MaxY}) 
                            or ({MinX} <= e3x and e3x <= {MaxX} and {MinY} <= e3y and e3y <= {MaxY}));
                            """
            results = pgDB.query(sqlStatement=sql_select_query)
            pgDB.close()
            #if the hammer is clear return true
            if results == []:
                SSM_Clear = True
                return SSM_Clear
        # if the  current element is a standard stud return true
        elif results[0][2] == "Board" and results[0][3] == "Stud":
            SSM_Clear = True
            return SSM_Clear
        
if __name__ == "__main__":
    board = Clear()