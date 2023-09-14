import logging

import util.dataBaseConnect as dbc


class Parameters:  # This class is designed to fetch all parameters from parameter table based on sectionName

    def __init__(self, tabs: list, minID, maxID):
        self._tabNames = tabs
        self._parmList: dict = {}
        pgDB = dbc.DB_Connect()
        pgDB.open()
        sql_var1 = minID
        sql_var2 = maxID
        sql_select_query = f"""                            
                            select json_object_agg(struct.psect, struct.varm) as larm
                            from (
                                select 
                                    jsonOBJ.sect psect, 
                                    json_object_agg(description, jsonOBJ.parms) as varm
                                from (
                                    select	
                                        sectionname sect,
                                        description,
                                        json_build_object(
                                                        'value', value, 
                                                        'max', "max", 
                                                        'min', "min", 
                                                        'datatype', "datatype")	as parms
                                    from parameters
                                    where stationid >= '{sql_var1}' and stationid <= '{sql_var2}' ) jsonOBJ
                                group by jsonOBJ.sect
                            ) struct;
                            """
        results = pgDB.query(sql_statement=sql_select_query)

        self._parmList: dict = results[0][0]
        pgDB.close()

    def getParm(self, secName, description):  # This function is used for retrieving variable name from parameter information
        dtype = self._parmList.get(secName)[description]["datatype"]
        dVar = self._parmList.get(secName)[description]["value"]
        match dtype:
            case "string":
                return str(dVar)
            case "bool":
                return bool(int(dVar, base=2))
            case "int":
                return int(dVar)
            case "double":
                return float(dVar)
            case "lreal":
                return float(dVar)
            case _:
                logging.info("Not a valid datatype")
                return None

# if __name__ == "__main__":
#     tabNames = ["Application"]

#     parms = Parameters(tabNames, 10, 19)
#     val = parms.getParm("Application", "Run Level 20 missions (True/false)")
#     print(type(val))
#     print(val)
