import dataBaseConnect as dbc

# this class is designed to check positional okayness of the framing units Hammer and Stud Stop on both the Mobile and Fix Sides
class Clear:

    def __init__(self) -> None:
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        #get parameters for stud stop and hammer that are universal 
        sql_var= " "
        sql_select_query="""
                        SELECT description, value
                        FROM parameters
                        WHERE description IN (  'Stud Stop thickness', 
                                                'Stud Stop width', 
                                                'Hammer Units Thickness', 
                                                'Hammer Units Length', 
                                                'Hammer Units Stroke'
                                                );
                        """
        
        results = pgDB.query(sqlStatement=sql_select_query)
        dbc.printResult(results)
        #assign results of query to variables
        self.ss_thickness = float(results[0][1])
        self.ss_width = float(results[1][1])
        self.hu_thickness = float(results[2][1])
        self.hu_length = float(results[3][1])
        self.hu_stroke = float(results[4][1])
        pgDB.close()
        
    def studStopFS(elementGuid):
        sql_Var = elementGuid
        sql_select_query=f"""
                        SELECT type, definition, e1x, 
                        FROM elements
                        WHERE elementguid = '{sql_Var}' 
                        """
        #query definition of element
        
        #query location above position
        
        # if response from query is empty then 
        #   return true

        # else 
        #   return false

        return False

    def hammerFS(elementPOS):
        
        return False
    
    def studStopMS(elementPOS):

        return False

    def hammerMS(elementPOS):
        
        return False


if __name__ == "__main__":
    board = Clear()

    