import sys
from util import dataBaseConnect as dbc
from util import panelData as pd
from util import EC1

#testing jobID: 221415WALLS
print(sys.argv[1])
credentials = dbc.getCred()
pgDB = dbc.DB_Connect(credentials)
pgDB.open()

sql_Var = sys.argv[1] # "221415WALLS"
sql_select_query=f"""SELECT jobid, panelguid
                    FROM bundle, panel
                    WHERE jobid = '{sql_Var}'
                """

results = pgDB.query(sqlStatement=sql_select_query)
dbc.printResult(results)
pgDB.close()

# Itterate through each panel to build table data
for panelGuid in results:
    # Get Panel Data
    pdData = pd.Panel(panelGuid)
    ## Stud Picker Data
    sfData = EC1.MtrlData(pdData)
    ## Framing
    fm3_panel = EC1.JobData(pdData)
    fm3_panel.jdMain()

    #fm3_panel.jobdata.append(linelist)
    ## Robot Cell 1

    ## Robot Cell 2


