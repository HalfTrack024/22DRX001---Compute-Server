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
        #thickness is in the X direction of elevation, width/length in the Y direction
        self.ss_thickness = float(results[0][1])
        self.ss_width = float(results[1][1])
        self.hu_thickness = float(results[2][1])
        self.hu_length = float(results[3][1])
        self.hu_stroke = float(results[4][1])
        pgDB.close()
        
    def studStopFS(elementPOS, current_stud, self):
        #elementPOS and current_stud are lists = E1X,E1Y,E2X,E2Y,E3X,E3Y,E4X,E4Y
        #current stud has the X value that we are at, and we use it to check the ss boundries (E4X)
        if elementPOS[1] >= (self.ss_width + 1.5) and current_stud[6] <= elementPOS[0] and elementPOS[6] <= (current_stud[0] - self.ss_thickness):
            return False
        else:
            return True

    def hammerFS(elementPOS, current_stud, self):
        if elementPOS[1] >= (self.hu_length + 1.5) and (current_stud[6] + self.hu_thickness) <= elementPOS[0] and elementPOS[6] <= current_stud[0]:
            return False
        else:
            return True
    
    def studStopMS(elementPOS, self):

        return False

    def hammerMS(elementPOS, self):
        
        return False


if __name__ == "__main__":
    board = Clear()

    