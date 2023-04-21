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
        sql_select_query=f"""
                        SELECT e1x, panelguid
                        FROM elements
                        WHERE elementguid = '{elementguid}' 
                        ORDER BY e1x ASC;
                        """
        results = pgDB.query(sql_select_query)
        MinX = str(float(results[0][0]) - self.ss_thickness)
        MaxX = str(results[0][0])
        MinY = str(38.1)
        MaxY = str(38.1 + self.ss_width)
        sql_select_query=f"""
                        SELECT e1x
                        FROM elements
                        WHERE panelguid = '{results[0][1]}' and ({MinX} <= e1x and e1x <= {MaxX} and {MinY} <= e1y and e1y <= {MaxY}) 
                        or ({MinX} <= e4x and e4x <= {MaxX} and {MinY} <= e4y and e4y <= {MaxY});
                        """
        results = pgDB.query(sql_select_query)
        #print(results)
        if len(results[0]) < 2:
            SSF_Clear = True
            return SSF_Clear
        
        pgDB.close()
    def hammerFS(self,elementguid):
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        sql_select_query=f"""
                        SELECT e4x, panelguid, type, description
                        FROM elements
                        WHERE elementguid = '{elementguid}'
                        ORDER BY e4x ASC;
                        """
        results = pgDB.query(sqlStatement=sql_select_query)
        if results[0][2] == "Sub-Assembly Board":
            MinX = str(results[0] )
            MaxX = str(results[0]+ self.hu_length + self.hu_stroke)
            MinY = str(38.1 + self.hu_Y)
            MaxY = str(38.1 + self.hu_Y + self.hu_thickness)
            sql_select_query=f"""
                            SELECT e2x
                            FROM elements
                            WHERE panelguid = '{results[1]}' and ({MinX} <= e1x and e1x <= {MaxX} and {MinY} <= e1y and e1y <= {MaxY}) 
                            or ({MinX} <= e4x and e4x <= {MaxX} and {MinY} <= e4y and e4y <= {MaxY});
                            """
            results = pgDB.query(sqlStatement=sql_select_query)
            if results == None:
                SSM_Clear = True
            return SSM_Clear
        
        if results[0][2] == "Board" and results[0][3] == "Stud":
            SSM_Clear = True
            return SSM_Clear
        
        pgDB.close()
    def studStopMS(self,elementguid):
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        sql_select_query=f"""
                        SELECT e2x, panelguid
                        FROM elements
                        WHERE elementguid = '{elementguid}'
                        ORDER BY e2x ASC;
                        """
        results = pgDB.query(sql_select_query)
        sql_select_query=f"""
                        SELECT height
                        FROM panel
                        WHERE panelguid = '{results[0][1]}'
                        """
        height = pgDB.query(sql_select_query)
        MinX = str(float(results[0][0]) - self.ss_thickness)
        MaxX = str(results[0][0])
        MinY = str(float(height[0][0]) - 38.1 - self.ss_width)
        MaxY = str(float(height[0][0]) - 38.1)
        sql_select_query=f"""
                        SELECT e2x
                        FROM elements
                        WHERE panelguid = '{results[0][1]}' and ({MinX} <= e2x and e2x <= {MaxX} and {MinY} <= e2y and e2y <= {MaxY}) 
                        or ({MinX} <= e3x and e3x <= {MaxX} and {MinY} <= e3y and e3y <= {MaxY});
                        """
        results = pgDB.query(sql_select_query)
        if len(results[0]) < 2:
            SSM_Clear = True
            return SSM_Clear
        
        pgDB.close()
    def hammerMS(self,elementguid):
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        sql_select_query=f"""
                        SELECT e3x, panelguid, type, description
                        FROM elements
                        WHERE elementguid = '{elementguid}'
                        ORDER BY e3x ASC;
                        """
        results = pgDB.query(sql_select_query)
        sql_select_query=f"""
                        SELECT height
                        FROM panel
                        WHERE panelguid = '{results[0][1]}'
                        """
        height = pgDB.query(sqlStatement=sql_select_query)
        if results[0][2] == "Sub-Assembly Board":
            MinX = str(results[0])
            MaxX = str(results[0]+ self.hu_length + self.hu_stroke)
            MinY = str(height - 38.1 - self.hu_Y - self.hu_thickness)
            MaxY = str(height - 38.1 - self.hu_Y)
            sql_select_query=f"""
                            SELECT e3x
                            FROM elements
                            WHERE panelguid = '{results[1]}' and ({MinX} <= e2x and e2x <= {MaxX} and {MinY} <= e2y and e2y <= {MaxY}) 
                            or ({MinX} <= e3x and e3x <= {MaxX} and {MinY} <= e3y and e3y <= {MaxY});
                            """
            results = pgDB.query(sqlStatement=sql_select_query)
            if results == None:
                SSM_Clear = True
                return SSM_Clear
        
        if results[0][2] == "Board" and results[0][3] == "Stud":
            SSM_Clear = True
            return SSM_Clear
        
        pgDB.close()
if __name__ == "__main__":
    board = Clear()