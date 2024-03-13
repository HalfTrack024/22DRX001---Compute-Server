import util.dataBaseConnect as dbc


class Panel:
    plateInnerBottom = 0
    plateInnerTop = 0

    def __init__(self, panelguid):
        # Open Database Connection
        pgDB = dbc.DB_Connect()
        pgDB.open()

        sql_var = panelguid
        sql_select_query = f"""
                        SELECT thickness, studheight, walllength, category, sb.jobid 
                        FROM cad2fab.system_panels sp 
                        JOIN cad2fab.system_bundles sb  ON sp.bundleguid  = sb.bundleguid 
                        WHERE panelguid = '{sql_var}';
                        """
        #
        results = pgDB.query(sql_select_query)
        # dbc.printResult(results)
        pgDB.close()
        # assign results of query to variables
        self.job = results[0][4]
        self.guid = panelguid
        self.panelThickness = float(results[0][0])
        self.studHeight = float(results[0][1])
        self.panelLength = float(results[0][2])
        self.category = results[0][3]

        self.plateInnerBottom = 1.5
        self.plateInnerTop = 1.5 + self.studHeight

        # Get and Add Unique layers to
        pgDB.open()
        sql_var = panelguid
        sql_select_query = f"""
                        select distinct b2y "type" , materialdesc 
                        from cad2fab.system_elements
                        where "type" = 'Sheet' and panelguid = '{sql_var}';
                        """
        #
        results = pgDB.query(sql_select_query)
        # dbc.printResult(results)
        pgDB.close()
        self._layerPos = []
        self._layerMat = []
        self._LayerFastener = []
        self._EdgeFastener = []
        self._FieldFastener = []
        for layer in results:
            self._layerPos.append(float(layer[0]))
            self._layerMat.append(layer[1])
            self._LayerFastener.append(0)

    def get_panel(self, panel_guid):
        pass

    def get_layer_count(self):
        return len(self._layerPos)

    def get_layer_material(self, index):
        return self._layerMat[index]

    def update_layer_material(self, material, index):
        self._layerMat[index] = material

    def update_layer_fastener_space(self, edge, field, index):
        if len(self._FieldFastener) < index+1:
            self._FieldFastener.append(field)
            self._EdgeFastener.append(edge)
        else:
            self._FieldFastener[index] = field
            self._EdgeFastener[index] = edge

    def get_edge_spacing(self, index):
        return self._EdgeFastener[index]

    def get_field_spacing(self, index):
        return self._FieldFastener[index]

    def get_layer_position(self, index):
        return self._layerPos[index]

    def get_layer_index(self, pos):
        return self._layerPos.index(pos)

    def update_layer_fastener(self, index, typeval):
        self._LayerFastener[index] = typeval

    def get_layer_fastener(self, index):
        return self._LayerFastener[index]

    @property
    def layer_pos(self):
        return self._layerPos

# if __name__ == "__main__":
#     #get panel details dimensions
#     sql_var= "4a4909bf-f877-4f2f-8692-84d7c6518a2d"

#     #initialize Panel
#     itterPanel = Panel(sql_var)
