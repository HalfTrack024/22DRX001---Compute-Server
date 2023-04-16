import xmltodict as dc #requires python >= V3.4
import psycopg2 as psy #requires python >= V3.6

def dicXML(filepath):
	#open the xml file
	with open(filepath, 'r') as f:
		set = f.read()
	#global variable data is accessable outside of this function
	global data
	data = dc.parse(set)

def insertJob(records,credentials):
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
		sql_insert_query="""
							INSERT INTO jobs(serial,jobid,loaddate)
							VALUES (%s,%s,NOW())
							ON CONFLICT (serial,jobid)
							DO UPDATE SET loaddate = NOW();
							"""
		result = cursor.executemany(sql_insert_query, records)
		connection.commit()
		print(cursor.rowcount, "Records inserted successfully into jobs table")

	except(Exception, psy.Error) as Error:
		print("Failed to insert record to table: {}".format(Error))

	finally:
		#Close DB Connection
		if connection:
			cursor.close()
			connection.close()
			print("SQL connection closed")

def insertBundle(records,credentials):
	#Connect to Database
	try:
		connection = psy.connect(
			user=credentials[0],
			password=credentials[1],
			host=credentials[2],
			port=credentials[3],
			database=credentials[4]
		)
		cursor = connection.cursor()
		#Query used for inserting data to the database
		sql_insert_query="""
							INSERT INTO bundle(bundleguid,jobid,level_description,label,type)
							VALUES (%s,%s,%s,%s,%s)
							ON CONFLICT (bundleguid)
							DO UPDATE SET jobid = EXCLUDED.jobid, level_description = EXCLUDED.level_description,
							label = EXCLUDED.label, type = EXCLUDED.type;
							"""
		result = cursor.executemany(sql_insert_query, records)
		connection.commit()
		print(cursor.rowcount, "Records inserted successfully into bundles table")

	except(Exception, psy.Error) as Error:
		print("Failed to insert record to table: {}".format(Error))

	finally:
		#Close DB Connection
		if connection:
			cursor.close()
			connection.close()
			print("SQL connection closed")

def insertPanel(records,credentials):
	#Connect to the Database
	try:
		connection = psy.connect(
			user=credentials[0],
			password=credentials[1],
			host=credentials[2],
			port=credentials[3],
			database=credentials[4]
		)
		cursor = connection.cursor()
		#Query used for writing data to the database
		sql_insert_query="""
							INSERT INTO panel(bundleguid, panelguid, label, height, thickness,
							studspacing, studheight, walllength, category, boardfeet)
							VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
							ON CONFLICT (panelguid)
							DO UPDATE SET bundleguid = EXCLUDED.bundleguid, label = EXCLUDED.label,
							height = EXCLUDED.height,
							thickness = EXCLUDED.thickness, studspacing = EXCLUDED.studspacing,
							studheight = EXCLUDED.studheight, walllength = EXCLUDED.walllength,
							category = EXCLUDED.category, boardfeet = EXCLUDED.boardfeet;
							"""
		result = cursor.executemany(sql_insert_query, records)
		connection.commit()
		print(cursor.rowcount, "Records inserted successfully into panels table")

	except(Exception, psy.Error) as Error:
		print("Failed to insert record to table: {}".format(Error))

	finally:
		#Close DB Connection
		if connection:
			cursor.close()
			connection.close()
			print("SQL connection closed")

def insertElements(records,credentials):
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
		#Query used for writing data to the database
		sql_insert_query="""
							INSERT INTO elements(panelguid,elementguid,type,familymember,description,
												size,actual_thickness,actual_width,materialsid,b1x,b1y,b2x,
												b2y,b3x,b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y)
							VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
							ON CONFLICT (elementguid)
							DO UPDATE SET panelguid = EXCLUDED.panelguid, type = EXCLUDED.type,
							familymember = EXCLUDED.familymember, description = EXCLUDED.description,
							size = EXCLUDED.size,actual_thickness = EXCLUDED.actual_thickness,
							actual_width = EXCLUDED.actual_width,materialsid = EXCLUDED.materialsid,
							b1x = EXCLUDED.b1x,b1y = EXCLUDED.b1y,b2x = EXCLUDED.b2x,b2y = EXCLUDED.b2y,
							b3x = EXCLUDED.b3x,b3y = EXCLUDED.b3y,b4x = EXCLUDED.b4x,b4y = EXCLUDED.b4y,
							e1x = EXCLUDED.e1x,e1y = EXCLUDED.e1y,e2x = EXCLUDED.e2x,e2y = EXCLUDED.e2y,
							e3x = EXCLUDED.e3x,e3y = EXCLUDED.e3y,e4x = EXCLUDED.e4x,e4y = EXCLUDED.e4y;
							"""
		result = cursor.executemany(sql_insert_query, records)
		connection.commit()
		print(cursor.rowcount, "Records inserted successfully into elements table")

	except(Exception, psy.Error) as Error:
		print("Failed to insert record to table: {}".format(Error))

	finally:
		#Close DB Connection
		if connection:
			cursor.close()
			connection.close()
			print("SQL connection closed")
	

if __name__ == "__main__":
	#get filepath to XML file from user
	filepath = input('Type filename or path to file\n(1337.xml or c:/Users/115.xml):  ')

	#get sql server credentials from user
	choice1 = input('Use saved credentials? (y/n):  ')
	if str.lower(choice1) == 'y':
		print('Using saved credentials')
		save = open('Python Script\dataExtract_EHX\credentials.txt','r')
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

	#convert XML file to dictionaries
	dicXML(filepath)


	#List to insert to jobs table
	jobIN = [(10,data['MITEK_SHOPNET_MARKUP_LANGUAGE_FILE']['Job']['JobID']),]
	#Insert jobIN List to jobs table
	insertJob(jobIN,credentials)


	#List to insert to bundles table
	bundleIN = []
	#Loop through all levels in the job
	for level in data['MITEK_SHOPNET_MARKUP_LANGUAGE_FILE']["Job"]["Level"]:
		#Loop through all bundles in the level
		for bundle in level["Bundle"]:
			#Data to import to the database
			bundleIN.append((bundle['BundleGuid'],bundle['JobID'],level['Description'],bundle['Label'],bundle['Type']),)
	#Insert bundleIN list to bundles table
	insertBundle(bundleIN,credentials)

	c = 0
	#List column data for panels table
	panelIN = []
	#Loop through all the levels in the job
	for level in data['MITEK_SHOPNET_MARKUP_LANGUAGE_FILE']["Job"]["Level"]:
		#Loop through all the bundles in the level
		for bundle in level["Bundle"]:
			#Loop through all the panels in the bundle
			for panel in bundle['Panel']:
				#Check if the panel is a string
				#The panel is a string if it is the only panel in a bundle
				if type(panel) == str:
					#All params of the panel are a different string, only add one data to the query
					if c==0:
						panelIN.append((bundle['Panel']['BundleGuid'],bundle['Panel']['PanelGuid'],
										bundle['Panel']['Label'],bundle['Panel']['Height'],
										bundle['Panel']['Thickness'],bundle['Panel']['StudSpacing'],
										bundle['Panel']['StudHeight'],bundle['Panel']['WallLength'],
										bundle['Panel']['Category'],bundle['Panel']['BoardFeet']),)
					c+=1
					#reset counter at the end of the strings
					if c == 29:
						c=0
					#Skip to the next loop if the panel was a string
					continue
				#Get the data for non-string panels
				panelIN.append((panel['BundleGuid'],panel['PanelGuid'],panel['Label'],
								panel['Height'],panel['Thickness'],panel['StudSpacing'],
								panel['StudHeight'],panel['WallLength'],panel['Category'],
								panel['BoardFeet']),)
	#Insert the panel data to the Database
	insertPanel(panelIN,credentials)

	#Counter for strings
	c2 = 0
	#List of data for elements table
	elementIN = []
	#loop through all the levels in the job
	for level in data['MITEK_SHOPNET_MARKUP_LANGUAGE_FILE']["Job"]["Level"]:
		#loop through all the bundles in the level
		for bundle in level["Bundle"]:
			#loop through all the panels in the bundle
			for panel in bundle['Panel']:
				#check if the panel is a string type
				if type(panel) != str:
					#Add boards to the list if they exist
					if 'Board' in panel.keys():
						#loop through all the boards in the panel
						for board in panel['Board']:
							#add the board data to the list
							elementIN.append((board['PanelGuid'],board['BoardGuid'],'Board',
										  board['FamilyMember'],board['FamilyMemberName'],
										  board['Material']['Size'],board['Material']['ActualThickness'],
										  board['Material']['ActualWidth'],board['Material']['MaterialsId'],
										  board['BottomView']['Point'][0]['X'],board['BottomView']['Point'][0]['Y'],
										  board['BottomView']['Point'][1]['X'],board['BottomView']['Point'][1]['Y'],
										  board['BottomView']['Point'][2]['X'],board['BottomView']['Point'][2]['Y'],
										  board['BottomView']['Point'][3]['X'],board['BottomView']['Point'][3]['Y'],
										  board['ElevationView']['Point'][0]['X'],board['ElevationView']['Point'][0]['Y'],
										  board['ElevationView']['Point'][1]['X'],board['ElevationView']['Point'][1]['Y'],
										  board['ElevationView']['Point'][2]['X'],board['ElevationView']['Point'][2]['Y'],
										  board['ElevationView']['Point'][3]['X'],board['ElevationView']['Point'][3]['Y']),)
					#Add sheets to the list if they exist
					if 'Sheet' in panel.keys():
						#loop through all the sheets in the panel
						for sheet in panel['Sheet']:
							#add the sheet data to the list
							elementIN.append((sheet['PanelGuid'],sheet['BoardGuid'],'Sheet',
										  sheet['FamilyMember'],sheet['FamilyMemberName'],
										  sheet['Material']['Size'],sheet['Material']['ActualThickness'],
										  sheet['Material']['ActualWidth'],sheet['Material']['MaterialsId'],
										  sheet['BottomView']['Point'][0]['X'],sheet['BottomView']['Point'][0]['Y'],
										  sheet['BottomView']['Point'][1]['X'],sheet['BottomView']['Point'][1]['Y'],
										  sheet['BottomView']['Point'][2]['X'],sheet['BottomView']['Point'][2]['Y'],
										  sheet['BottomView']['Point'][3]['X'],sheet['BottomView']['Point'][3]['Y'],
										  sheet['ElevationView']['Point'][0]['X'],sheet['ElevationView']['Point'][0]['Y'],
										  sheet['ElevationView']['Point'][1]['X'],sheet['ElevationView']['Point'][1]['Y'],
										  sheet['ElevationView']['Point'][2]['X'],sheet['ElevationView']['Point'][2]['Y'],
										  sheet['ElevationView']['Point'][3]['X'],sheet['ElevationView']['Point'][3]['Y']),)
					#Add SubAssemblies to the list if they exist and are in a list format
					#SubAssemblies will be in list format if there are >1 in the current panel
					if 'SubAssembly' in panel.keys() and type(panel['SubAssembly']) == list:
						#loop through the SubAssemblies
						for subassembly in panel['SubAssembly']:
							#Is there an opening that needs to be cut into the panel?
							roughopening = False
							#are there boards in the subassembly?
							if 'Board' in subassembly.keys():
								#loop through all the boards in the subassembly
								for boardsub in subassembly['Board']:
									#when the board isn't the rough opening board add it to the list
									if boardsub['FamilyMemberName'] != 'RoughOpening':
										elementIN.append((boardsub['PanelGuid'],boardsub['BoardGuid'],'Sub-Assembly Board',
										  boardsub['FamilyMember'],boardsub['FamilyMemberName'],
										  boardsub['Material']['Size'],boardsub['Material']['ActualThickness'],
										  boardsub['Material']['ActualWidth'],boardsub['Material']['MaterialsId'],
										  boardsub['BottomView']['Point'][0]['X'],boardsub['BottomView']['Point'][0]['Y'],
										  boardsub['BottomView']['Point'][1]['X'],boardsub['BottomView']['Point'][1]['Y'],
										  boardsub['BottomView']['Point'][2]['X'],boardsub['BottomView']['Point'][2]['Y'],
										  boardsub['BottomView']['Point'][3]['X'],boardsub['BottomView']['Point'][3]['Y'],
										  boardsub['ElevationView']['Point'][0]['X'],boardsub['ElevationView']['Point'][0]['Y'],
										  boardsub['ElevationView']['Point'][1]['X'],boardsub['ElevationView']['Point'][1]['Y'],
										  boardsub['ElevationView']['Point'][2]['X'],boardsub['ElevationView']['Point'][2]['Y'],
										  boardsub['ElevationView']['Point'][3]['X'],boardsub['ElevationView']['Point'][3]['Y']),)
									else: #add the subassembly to the elements list with the rough opening as its points
										elementIN.append((subassembly['PanelGuid'],subassembly['SubAssemblyGuid'],'Sub Assembly',
														  subassembly['FamilyMember'],subassembly['FamilyMemberName'],
														  None,None,boardsub['Material']['ActualWidth'],None,
														  boardsub['BottomView']['Point'][0]['X'],
														  boardsub['BottomView']['Point'][0]['Y'],
														  boardsub['BottomView']['Point'][1]['X'],
														  boardsub['BottomView']['Point'][1]['Y'],
														  boardsub['BottomView']['Point'][2]['X'],
														  boardsub['BottomView']['Point'][2]['Y'],
														  boardsub['BottomView']['Point'][3]['X'],
														  boardsub['BottomView']['Point'][3]['Y'],
														  boardsub['ElevationView']['Point'][0]['X'],
														  boardsub['ElevationView']['Point'][0]['Y'],
														  boardsub['ElevationView']['Point'][1]['X'],
														  boardsub['ElevationView']['Point'][1]['Y'],
														  boardsub['ElevationView']['Point'][2]['X'],
														  boardsub['ElevationView']['Point'][2]['Y'],
														  boardsub['ElevationView']['Point'][3]['X'],
														  boardsub['ElevationView']['Point'][3]['Y']),)
										#confirm that the subassembly is added to the list
										roughopening = True
							#if the subassembly wasn't added to the list already add it without point data
							if roughopening == False:
								elementIN.append((subassembly['PanelGuid'],subassembly['SubAssemblyGuid'],'Sub Assembly',
												  subassembly['FamilyMember'],subassembly['FamilyMemberName'],
												  None,None,subassembly['Width'],None,None,None,None,None,None,None,None,
												  None,None,None,None,None,None,None,None,None),)
					# if there is only one subassembly in the panel
					if 'SubAssembly' in panel.keys() and type(panel['SubAssembly']) == dict:
						#check for a rough opening sub-board
						roughopening = False
						#loop through all the boards in the subassembly
						for boardsub in panel['SubAssembly']['Board']:
							#Check if the sub board is the rough opening
							if boardsub['FamilyMemberName'] != 'RoughOpening':
								elementIN.append((boardsub['PanelGuid'],boardsub['BoardGuid'],'Sub-Assembly Board',
			  											boardsub['FamilyMember'],boardsub['FamilyMemberName'],
														boardsub['Material']['Size'],boardsub['Material']['ActualThickness'],
														boardsub['Material']['ActualWidth'],boardsub['Material']['MaterialsId'],
														boardsub['BottomView']['Point'][0]['X'],boardsub['BottomView']['Point'][0]['Y'],
														boardsub['BottomView']['Point'][1]['X'],boardsub['BottomView']['Point'][1]['Y'],
														boardsub['BottomView']['Point'][2]['X'],boardsub['BottomView']['Point'][2]['Y'],
														boardsub['BottomView']['Point'][3]['X'],boardsub['BottomView']['Point'][3]['Y'],
														boardsub['ElevationView']['Point'][0]['X'],boardsub['ElevationView']['Point'][0]['Y'],
														boardsub['ElevationView']['Point'][1]['X'],boardsub['ElevationView']['Point'][1]['Y'],
														boardsub['ElevationView']['Point'][2]['X'],boardsub['ElevationView']['Point'][2]['Y'],
														boardsub['ElevationView']['Point'][3]['X'],boardsub['ElevationView']['Point'][3]['Y']),)
							else: #add the subassembly to the database with the rough opening as the points
								elementIN.append((panel['SubAssembly']['PanelGuid'],panel['SubAssembly']['SubAssemblyGuid'],
			  											'Sub Assembly',panel['SubAssembly']['FamilyMember'],
														panel['SubAssembly']['FamilyMemberName'],None,None,
														boardsub['Material']['ActualWidth'],None,
														boardsub['BottomView']['Point'][0]['X'],boardsub['BottomView']['Point'][0]['Y'],
														boardsub['BottomView']['Point'][1]['X'],boardsub['BottomView']['Point'][1]['Y'],
														boardsub['BottomView']['Point'][2]['X'],boardsub['BottomView']['Point'][2]['Y'],
														boardsub['BottomView']['Point'][3]['X'],boardsub['BottomView']['Point'][3]['Y'],
														boardsub['ElevationView']['Point'][0]['X'],boardsub['ElevationView']['Point'][0]['Y'],
														boardsub['ElevationView']['Point'][1]['X'],boardsub['ElevationView']['Point'][1]['Y'],
														boardsub['ElevationView']['Point'][2]['X'],boardsub['ElevationView']['Point'][2]['Y'],
														boardsub['ElevationView']['Point'][3]['X'],boardsub['ElevationView']['Point'][3]['Y']),)
								#confirm that the subassembly was added
								roughopening = True
							#if the sub assembly wasn't added yet add it without point data
							if roughopening == False:
								elementIN.append((panel['SubAssembly']['PanelGuid'],panel['SubAssembly']['SubAssemblyGuid'],
			  											'Sub Assembly',panel['SubAssembly']['FamilyMember'],
														panel['SubAssembly']['FamilyMemberName'],None,None,
														panel['SubAssembly']['Width'],None,None,None,None,None,None,None,None,
														None,None,None,None,None,None,None,None,None),)
				# if the panel is a string (only 1 panel in the bundle)
				elif type(panel) == str:
					#add the boards to the list if they exist
					if 'Board' in bundle['Panel'].keys() and c2 == 0:
						#loop through all the boards in the panel
						for board in bundle['Panel']['Board']:
							#add the data to the list
							elementIN.append((board['PanelGuid'],board['BoardGuid'],'Board',
										  board['FamilyMember'],board['FamilyMemberName'],
										  board['Material']['Size'],board['Material']['ActualThickness'],
										  board['Material']['ActualWidth'],board['Material']['MaterialsId'],
										  board['BottomView']['Point'][0]['X'],board['BottomView']['Point'][0]['Y'],
										  board['BottomView']['Point'][1]['X'],board['BottomView']['Point'][1]['Y'],
										  board['BottomView']['Point'][2]['X'],board['BottomView']['Point'][2]['Y'],
										  board['BottomView']['Point'][3]['X'],board['BottomView']['Point'][3]['Y'],
										  board['ElevationView']['Point'][0]['X'],board['ElevationView']['Point'][0]['Y'],
										  board['ElevationView']['Point'][1]['X'],board['ElevationView']['Point'][1]['Y'],
										  board['ElevationView']['Point'][2]['X'],board['ElevationView']['Point'][2]['Y'],
										  board['ElevationView']['Point'][3]['X'],board['ElevationView']['Point'][3]['Y']),)
					#add the sheets to the list if they exist
					if 'Sheet' in bundle['Panel'].keys() and c2 == 0:
						#loop through the sheets in the panel
						for sheet in bundle['Panel']['Sheet']:
							#add the data for the sheets to the list
							elementIN.append((sheet['PanelGuid'],sheet['BoardGuid'],'Sheet',
										  sheet['FamilyMember'],sheet['FamilyMemberName'],
										  sheet['Material']['Size'],sheet['Material']['ActualThickness'],
										  sheet['Material']['ActualWidth'],sheet['Material']['MaterialsId'],
										  sheet['BottomView']['Point'][0]['X'],sheet['BottomView']['Point'][0]['Y'],
										  sheet['BottomView']['Point'][1]['X'],sheet['BottomView']['Point'][1]['Y'],
										  sheet['BottomView']['Point'][2]['X'],sheet['BottomView']['Point'][2]['Y'],
										  sheet['BottomView']['Point'][3]['X'],sheet['BottomView']['Point'][3]['Y'],
										  sheet['ElevationView']['Point'][0]['X'],sheet['ElevationView']['Point'][0]['Y'],
										  sheet['ElevationView']['Point'][1]['X'],sheet['ElevationView']['Point'][1]['Y'],
										  sheet['ElevationView']['Point'][2]['X'],sheet['ElevationView']['Point'][2]['Y'],
										  sheet['ElevationView']['Point'][3]['X'],sheet['ElevationView']['Point'][3]['Y']),)
					#Add Sub Assemblies to the list if they exist, are list type
					if 'SubAssembly' in bundle['Panel'].keys() and type(bundle['Panel']['SubAssembly']) == list and c2 == 0:
						#loop through all the subassemblies
						for subassembly in bundle['Panel']['SubAssembly']:
							#check if there is a rough opening for the subassemby
							roughopening = False
							#add board to the list if it exists
							if 'Board' in subassembly.keys():
								#loop through all the boards in the subassembly
								for boardsub in subassembly['Board']:
									#Add boards if they aren't the rough opening
									if boardsub['FamilyMemberName'] != 'RoughOpening':
										elementIN.append((boardsub['PanelGuid'],boardsub['BoardGuid'],'Sub-Assembly Board',
										  boardsub['FamilyMember'],boardsub['FamilyMemberName'],
										  boardsub['Material']['Size'],boardsub['Material']['ActualThickness'],
										  boardsub['Material']['ActualWidth'],boardsub['Material']['MaterialsId'],
										  boardsub['BottomView']['Point'][0]['X'],boardsub['BottomView']['Point'][0]['Y'],
										  boardsub['BottomView']['Point'][1]['X'],boardsub['BottomView']['Point'][1]['Y'],
										  boardsub['BottomView']['Point'][2]['X'],boardsub['BottomView']['Point'][2]['Y'],
										  boardsub['BottomView']['Point'][3]['X'],boardsub['BottomView']['Point'][3]['Y'],
										  boardsub['ElevationView']['Point'][0]['X'],boardsub['ElevationView']['Point'][0]['Y'],
										  boardsub['ElevationView']['Point'][1]['X'],boardsub['ElevationView']['Point'][1]['Y'],
										  boardsub['ElevationView']['Point'][2]['X'],boardsub['ElevationView']['Point'][2]['Y'],
										  boardsub['ElevationView']['Point'][3]['X'],boardsub['ElevationView']['Point'][3]['Y']),)
									else: #add the subassembly if it has a rough opening
										elementIN.append((subassembly['PanelGuid'],subassembly['SubAssemblyGuid'],'Sub Assembly',
														  subassembly['FamilyMember'],subassembly['FamilyMemberName'],
														  None,None,boardsub['Material']['ActualWidth'],None,
														  boardsub['BottomView']['Point'][0]['X'],
														  boardsub['BottomView']['Point'][0]['Y'],
														  boardsub['BottomView']['Point'][1]['X'],
														  boardsub['BottomView']['Point'][1]['Y'],
														  boardsub['BottomView']['Point'][2]['X'],
														  boardsub['BottomView']['Point'][2]['Y'],
														  boardsub['BottomView']['Point'][3]['X'],
														  boardsub['BottomView']['Point'][3]['Y'],
														  boardsub['ElevationView']['Point'][0]['X'],
														  boardsub['ElevationView']['Point'][0]['Y'],
														  boardsub['ElevationView']['Point'][1]['X'],
														  boardsub['ElevationView']['Point'][1]['Y'],
														  boardsub['ElevationView']['Point'][2]['X'],
														  boardsub['ElevationView']['Point'][2]['Y'],
														  boardsub['ElevationView']['Point'][3]['X'],
														  boardsub['ElevationView']['Point'][3]['Y']),)
										#confirm if the subassembly was added to the list
										roughopening = True
							#add the subassembly to the list without point data if it wasn't added yet
							if roughopening == False:
								elementIN.append((subassembly['PanelGuid'],subassembly['SubAssemblyGuid'],'Sub Assembly',
												  subassembly['FamilyMember'],subassembly['FamilyMemberName'],
												  None,None,subassembly['Width'],None,None,None,None,None,None,None,None,
												  None,None,None,None,None,None,None,None,None),)
					#Add the subassembly if it exists and is dictionary type
					if 'SubAssembly' in bundle['Panel'].keys() and type(bundle['Panel']['SubAssembly']) == dict and c2 == 0:
						#check if the subassembly has a rough opening in the panel
						roughopening = False
						#loop through all the boards in the subassembly
						for boardsub in bundle['Panel']['SubAssembly']['Board']:
							# if the sub board isn't a rough opening add it to the list
							if boardsub['FamilyMemberName'] != 'RoughOpening':
								elementIN.append((boardsub['PanelGuid'],boardsub['BoardGuid'],'Sub-Assembly Board',
			  											boardsub['FamilyMember'],boardsub['FamilyMemberName'],
														boardsub['Material']['Size'],boardsub['Material']['ActualThickness'],
														boardsub['Material']['ActualWidth'],boardsub['Material']['MaterialsId'],
														boardsub['BottomView']['Point'][0]['X'],boardsub['BottomView']['Point'][0]['Y'],
														boardsub['BottomView']['Point'][1]['X'],boardsub['BottomView']['Point'][1]['Y'],
														boardsub['BottomView']['Point'][2]['X'],boardsub['BottomView']['Point'][2]['Y'],
														boardsub['BottomView']['Point'][3]['X'],boardsub['BottomView']['Point'][3]['Y'],
														boardsub['ElevationView']['Point'][0]['X'],boardsub['ElevationView']['Point'][0]['Y'],
														boardsub['ElevationView']['Point'][1]['X'],boardsub['ElevationView']['Point'][1]['Y'],
														boardsub['ElevationView']['Point'][2]['X'],boardsub['ElevationView']['Point'][2]['Y'],
														boardsub['ElevationView']['Point'][3]['X'],boardsub['ElevationView']['Point'][3]['Y']),)
							else: #Add the subassembly to the list if it has a rough opening
								elementIN.append((bundle['Panel']['SubAssembly']['PanelGuid'],bundle['Panel']['SubAssembly']['SubAssemblyGuid'],
			  											'Sub Assembly',bundle['Panel']['SubAssembly']['FamilyMember'],
														bundle['Panel']['SubAssembly']['FamilyMemberName'],None,None,
														boardsub['Material']['ActualWidth'],None,
														boardsub['BottomView']['Point'][0]['X'],boardsub['BottomView']['Point'][0]['Y'],
														boardsub['BottomView']['Point'][1]['X'],boardsub['BottomView']['Point'][1]['Y'],
														boardsub['BottomView']['Point'][2]['X'],boardsub['BottomView']['Point'][2]['Y'],
														boardsub['BottomView']['Point'][3]['X'],boardsub['BottomView']['Point'][3]['Y'],
														boardsub['ElevationView']['Point'][0]['X'],boardsub['ElevationView']['Point'][0]['Y'],
														boardsub['ElevationView']['Point'][1]['X'],boardsub['ElevationView']['Point'][1]['Y'],
														boardsub['ElevationView']['Point'][2]['X'],boardsub['ElevationView']['Point'][2]['Y'],
														boardsub['ElevationView']['Point'][3]['X'],boardsub['ElevationView']['Point'][3]['Y']),)
								#confirm the subassembly was added to the list
								roughopening = True
							#Add the subassembly to the list if it wasn't already
							if roughopening == False:
								elementIN.append((panel['SubAssembly']['PanelGuid'],panel['SubAssembly']['SubAssemblyGuid'],
			  											'Sub Assembly',panel['SubAssembly']['FamilyMember'],
														panel['SubAssembly']['FamilyMemberName'],None,None,
														panel['SubAssembly']['Width'],None,None,None,None,None,None,None,None,
														None,None,None,None,None,None,None,None,None),)
				c2+=1
				#reset counter after 1 string panel
				if c2 == 29:
					c2 = 0
	#insert the list to the database
	insertElements(elementIN,credentials)



#Written by Jacob OBrien for BraveCS
#March 2023