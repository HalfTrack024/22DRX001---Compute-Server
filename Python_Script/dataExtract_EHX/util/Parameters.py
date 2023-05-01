import dataBaseConnect as dbc



class Parameters: #This class is designed to fetch all parameters from parameter table based on sectionName 

    _parmList = []

    def __init__(self, tabs):
        self._tabNames = tabs
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()
        for tab in self._tabNames:
            sql_var = tab
            sql_select_query=f"""
                                select 
                                    json_object_agg(description, jsonOBJ.parms) as varm
                                from (
                                        select	
                                            description,
                                            json_build_object(
                                                            'value', value, 
                                                            'max', "max", 
                                                            'min', "min", 
                                                            'datatype', "DataType")	as parms
                                        from parameters
                                        where sectionname = '{sql_var}') jsonOBJ;
                                """
            results = pgDB.query(sqlStatement=sql_select_query)
            self._parmList.append(results[0][0])
        pgDB.close()
    
    def getParm(self,secName, description): #This function is used for retrieving variable name from parameter information
        index = self._tabNames.index(secName)
        dtype = self._parmList[index][description]["datatype"]
        dVar = self._parmList[index][description]["value"]
        match dtype:
            case "STRING":
                return str(dVar)
            case "BOOL":
                return bool(dVar)
            case "INT":
                return int(dVar)
            case "DOUBLE":
                return float(dVar)
            case _:
                print("Not a valid datatype")
                return None


if __name__ == "__main__":
    tabNames = ["Stud Inverter speeds","Nail Tool MS","Axis LBH","Axis HSP","Computer Settings",
            "Joint Rules","Studfeeder","Axis Width","Axis GUM","Axis GUF","Axis NPM","Positions",
            "Nail Tool FS","Stud stack positions","Axis NPF","Axis WAN","Axis SPR",
            "Program Settings And Parameters","Device Offsets","Program Settings and Parameters"]
    
    parms = Parameters(tabNames)
    val = parms.getParm("Positions", "Stud Stop width")
    print(type(val))
    print(val)
