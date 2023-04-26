import numpy as np					#Requires Python ???
from stl import mesh				#Requires Python ???
from util import dataBaseConnect as dbc

class GenSTL():
	def __init__(self) -> None:
		#get credentials and open the database
		self.credentials = dbc.getCred()
		pgDB = dbc.DB_Connect(self.credentials)
		pgDB.open()
		#select all rows/columns from panel table
		sql_select_query="SELECT * FROM panel"
		results = pgDB.query(sql_select_query)
		self.panelData = []
		for row in results:
			self.panelData.append([row[1]])
		#select all data from elements table
		self.elementData = []
		sql_select_query="SELECT * FROM elements"
		results2 = pgDB.query(sql_select_query)
		#get PanelGUID,B1X,B1Y,E1Y,   B2X,B2Y,E1Y,   B3X,B3Y,E4Y,   B4X,B4Y,E4Y,
		#              B1X,B1Y,E2Y,   B2X,B2Y,E2Y,   B3X,B3Y,E3Y,   B4X,B4Y,E3Y

        #need to get 8 X,Y,Z coordinates for each element's verticies
		for row in results2:
			self.elementData.append([row[0],row[9],row[10],row[18],row[11],row[12],row[18],
			    					row[13],row[14],row[24],row[15],row[16],row[24],row[9],
									row[10],row[20],row[11],row[12],row[20],row[13],row[14],
									row[22],row[15],row[16],row[22],row[2]])
		pgDB.close()
	

	def mainSTL(self):
		#loop through panels
		for panel in self.panelData:
			#define verticies array
			points = np.empty([0,3])
			#loop through all elements
			for element in self.elementData:
				# check if the element is a part of the current panel & isn't null
				if element[0] == panel[0] and element[25] != 'Sub-Assembly Cutout' and element[25] != 'Sub Assembly':
					# append the 8 verticies from the sql query to the verticies array
					points = np.append(points,[[float(element[1]),float(element[2]),float(element[3])],
						[float(element[4]),float(element[5]),float(element[6])],
						[float(element[7]),float(element[8]),float(element[9])],
						[float(element[10]),float(element[11]),float(element[12])],
						[float(element[13]),float(element[14]),float(element[15])],
						[float(element[16]),float(element[17]),float(element[18])],
						[float(element[19]),float(element[20]),float(element[21])],
						[float(element[22]),float(element[23]),float(element[24])]], axis=0)

			#define faces array
			faces = np.empty([0,3])
			i = 0
			#loop through each element in the panel
			while i < (len(points))/8:
				#add the reference for each vertex to create a triangle (2 triangles per face, counter-clockwise defined)
				faces = np.append(faces,[[(0+i*8),(1+i*8),(2+i*8)],[(2+i*8),(3+i*8),(0+i*8)],
					[(5+i*8),(1+i*8),(0+i*8)],[(0+i*8),(4+i*8),(5+i*8)],
					[(4+i*8),(0+i*8),(3+i*8)],[(3+i*8),(7+i*8),(4+i*8)],
					[(7+i*8),(3+i*8),(2+i*8)],[(2+i*8),(6+i*8),(7+i*8)],
					[(6+i*8),(2+i*8),(1+i*8)],[(1+i*8),(5+i*8),(6+i*8)],
					[(6+i*8),(5+i*8),(4+i*8)],[(4+i*8),(7+i*8),(6+i*8)]], axis=0)
				i+=1

			#generate the mesh using the verticies and faces
			shape = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
			for i, f in enumerate(faces):
				for j in range(3):
					shape.vectors[i][j] = points[int(f[j]),]
			
			#make the filename & directory
			name = 'Python_Script/dataExtract_EHX/out/' + str(panel[0]) + '.stl'
			shape.save(name)

if __name__ == '__main__':
	GenSTL.__init__(GenSTL)
	GenSTL.mainSTL(GenSTL)

#Written by Jacob OBrien for BraveCS♥
#April 2023