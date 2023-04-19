import psycopg2 as psy              #Requires Python >=3.6
import numpy as np					#Requires Python ???
from stl import mesh				#Requires Python ???

def importPanels(credentials):
	#global variable for all panel data
	global panelData
	panelData = []
	
	#connect to the database
	try:
		connection = psy.connect(
			user=credentials[0],
			password=credentials[1],
			host=credentials[2],
			port=credentials[3],
			database=credentials[4]
		)
		cursor = connection.cursor()
		#Query used for inserting the data
		sql_select_query="""
							SELECT * FROM panel
							"""
		cursor.execute(sql_select_query)
		result = cursor.fetchall()
	
		#get PanelGUID and Label
		for row in result:
			panelData.append([row[1]])

	except(Exception, psy.Error) as Error:
		print("Failed to insert record to table: {}".format(Error))

	finally:
		#Close DB Connection
		if connection:
			cursor.close()
			connection.close()
			print("SQL connection closed")

def importElements(credentials):
	#global variable to store element data (boards, sheets, subassemblies)
	global elementData
	elementData = []
	
	#connect to the database
	try:
		connection = psy.connect(
			user=credentials[0],
			password=credentials[1],
			host=credentials[2],
			port=credentials[3],
			database=credentials[4]
		)
		cursor = connection.cursor()
		#Query used for inserting the data
		sql_select_query="""
							SELECT * FROM elements
							"""
		cursor.execute(sql_select_query)
		result = cursor.fetchall()
	
		#get PanelGUID,B1X,B1Y,E1Y,   B2X,B2Y,E1Y,   B3X,B3Y,E4Y,   B4X,B4Y,E4Y,
		#              B1X,B1Y,E2Y,   B2X,B2Y,E2Y,   B3X,B3Y,E3Y,   B4X,B4Y,E3Y

        #need to get 8 X,Y,Z coordinates for each element's verticies
		
		for row in result:
			elementData.append([row[0],row[9],row[10],row[18],row[11],row[12],row[18],row[13],
		       					row[14],row[24],row[15],row[16],row[24],row[9],row[10],row[20],
								row[11],row[12],row[20],row[13],row[14],row[22],row[15],row[16],row[22],row[2]])

	except(Exception, psy.Error) as Error:
		print("Failed to insert record to table: {}".format(Error))

	finally:
		#Close DB Connection
		if connection:
			cursor.close()
			connection.close()
			print("SQL connection closed")
			
#get sql server credentials from user
choice1 = input('Use saved credentials? (y/n):  ')
if str.lower(choice1) == 'y':
	print('Using saved credentials')
	save = open('credentials.txt','r')
	credentials = save.read().splitlines()
	#Get credentials from the user
elif str.lower(choice1) == 'n':
	credentials = []
	credentials.append(input('Type DB Username:  	'))
	credentials.append(input('Type DB Password:  	'))
	credentials.append(input('Type DB Host IP:  	'))
	credentials.append(input('Type DB Port:  		'))
	credentials.append(input('Type DB Name:  		'))
	choice2 = input('Save the credentials?(This overwrites stored credentials) (y/n):  ')
	# Save the credentials
	if str.lower(choice2) == 'y':
		save = open('credentials.txt','w')
		save.write(credentials[0] + '\n' +credentials[1] + '\n' + credentials[2] + '\n' +
					credentials[3] + '\n' + credentials[4])

#import Data from SQL Database
importPanels(credentials)
importElements(credentials)

#loop through panels
for panel in panelData:
	#define verticies array
	points = np.empty([0,3])
	#loop through all elements
	for element in elementData:
		# check if the element is a part of the current panel & isn't null
		if element[0] == panel[0] and element[25] != 'Sub Assembly':
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
	name = 'out/' + str(panel[0]) + '.stl'
	shape.save(name)


#Written by Jacob OBrien for BraveCS♥
#April 2023