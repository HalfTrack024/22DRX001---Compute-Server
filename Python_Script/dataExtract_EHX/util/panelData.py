import util.dataBaseConnect as dbc
import util.framingCheck as fc

class Panel:
    plateInnerBottom = 0
    plateInnerTop = 0
    def __init__(self, panelguid):
        # Open Database Connection
        credentials = dbc.getCred()
        pgDB = dbc.DB_Connect(credentials)
        pgDB.open()

        sql_var= panelguid
        sql_select_query=f"""
                        SELECT thickness, studheight, walllength, category
                        FROM cad2fab.system_panels
                        WHERE panelguid = '{sql_var}';
                        """
        #
        results = pgDB.query(sqlStatement=sql_select_query)
        #dbc.printResult(results)
        pgDB.close()
        #assign results of query to variables
        self.guid = panelguid
        self.panelThickness = float(results[0][0])
        self.studHeight = float(results[0][1])
        self.panelLength = float(results[0][2])
        self.catagory = results[0][3]

        self.plateInnerBottom = 1.5
        self.plateInnerTop  = 1.5 + self.studHeight

        #Get and Add Unique layers to 
        pgDB.open()
        sql_var= panelguid
        sql_select_query=f"""
                        select distinct b1y "type" , materialdesc 
                        from cad2fab.system_elements
                        where "type" = 'Sheet' and panelguid = '{sql_var}';
                        """
        #
        results = pgDB.query(sqlStatement=sql_select_query)
        #dbc.printResult(results)
        pgDB.close()
        self._layerPos = []
        self._layerMat = []
        self._LayerFastener = []
        for layer in results:
            self._layerPos.append(layer[0])
            self._layerMat.append(layer[1])
            self._LayerFastener.append(0)

    def getPanel(self, panelGUID):
        pass
    
    def getLayerCount(self):
        return len(self._layerPos)
    
    def getLayerMaterial(self, index):
        return self._layerMat[index]
    
    def getLayerPosition(self, index):
        return self._layerPos[index]
    
    def getLayerIndex(self, pos):
        return self._layerPos.index(pos)
    
    def updateLayerFastener(self, index, typeval):
        self._LayerFastener[index] = typeval
    
    def getLayerFastener(self, index):
        return self._LayerFastener[index]
    
# if __name__ == "__main__":
#     #get panel details dimensions
#     sql_var= "4a4909bf-f877-4f2f-8692-84d7c6518a2d"

#     #initialize Panel
#     itterPanel = Panel(sql_var)

    
