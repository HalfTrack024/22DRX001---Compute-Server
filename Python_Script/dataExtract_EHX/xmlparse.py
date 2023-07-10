import xmltodict as dc #requires python >= V3.4
from util import dataBaseConnect as dbc

class xmlParse():
	def __init__(self,filepath):
		#open the xml file
		with open(filepath, 'r') as f:
			set = f.read()
		#variable data is accessable outside of this function
		self.data = dc.parse(set)
		self.credentials = dbc.getCred()

		xmlParse.data = self.data
		xmlParse.credentials = self.credentials

		#self.xmlMain()
	

	def appendElement(self, element, elemtype, subctr):
		if subctr == None:
			self.elementIN.append(
			(element['PanelGuid'],element['BoardGuid'],elemtype,
			element['FamilyMember'],element['FamilyMemberName'],
			element['Material']['Size'],element['Material']['ActualThickness'],
			element['Material']['ActualWidth'],element['Material']['Description'],
			element['Material']['SpeciesGrade'],
			element['BottomView']['Point'][0]['X'],element['BottomView']['Point'][0]['Y'],
			element['BottomView']['Point'][1]['X'],element['BottomView']['Point'][1]['Y'],
			element['BottomView']['Point'][2]['X'],element['BottomView']['Point'][2]['Y'],
			element['BottomView']['Point'][3]['X'],element['BottomView']['Point'][3]['Y'],
			element['ElevationView']['Point'][0]['X'],element['ElevationView']['Point'][0]['Y'],
			element['ElevationView']['Point'][1]['X'],element['ElevationView']['Point'][1]['Y'],
			element['ElevationView']['Point'][2]['X'],element['ElevationView']['Point'][2]['Y'],
			element['ElevationView']['Point'][3]['X'],element['ElevationView']['Point'][3]['Y'],None),
		)
		elif subctr != None and elemtype != 'Sub Assembly':
			self.elementIN.append(
			(element['PanelGuid'],element['BoardGuid'],elemtype,
			element['FamilyMember'],element['FamilyMemberName'],
			element['Material']['Size'],element['Material']['ActualThickness'],
			element['Material']['ActualWidth'],element['Material']['Description'],
			element['Material']['SpeciesGrade'],
			element['BottomView']['Point'][0]['X'],element['BottomView']['Point'][0]['Y'],
			element['BottomView']['Point'][1]['X'],element['BottomView']['Point'][1]['Y'],
			element['BottomView']['Point'][2]['X'],element['BottomView']['Point'][2]['Y'],
			element['BottomView']['Point'][3]['X'],element['BottomView']['Point'][3]['Y'],
			element['ElevationView']['Point'][0]['X'],element['ElevationView']['Point'][0]['Y'],
			element['ElevationView']['Point'][1]['X'],element['ElevationView']['Point'][1]['Y'],
			element['ElevationView']['Point'][2]['X'],element['ElevationView']['Point'][2]['Y'],
			element['ElevationView']['Point'][3]['X'],element['ElevationView']['Point'][3]['Y'],str(subctr)),
		)
		elif elemtype == 'Sub Assembly':
			self.elementIN.append(
				(element['PanelGuid'],element['SubAssemblyGuid'],elemtype,
					element['FamilyMember'],element['FamilyMemberName'],
					None,None,element['Width'],None,None,None,None,None,None,None,None,
					None,None,None,None,None,None,None,None,None,None,str(subctr)),
			)


	def insertJob(self):
		pgDB = dbc.DB_Connect(xmlParse.credentials)
		pgDB.open()
		sql_serial_query = 'SELECT serial FROM cad2fab.system_jobs ORDER BY serial DESC'
		serial = pgDB.query(sql_serial_query)
		if len(serial) != 0:
			serial = int(serial[0][0]) + 1
		else:
			serial = 1
		#how to generate the serial number?
		jobIN = [(serial,self.data['MITEK_SHOPNET_MARKUP_LANGUAGE_FILE']['Job']['JobID']),]
		#Header List
		self.sCadFilepath = str(self.data['MITEK_SHOPNET_MARKUP_LANGUAGE_FILE']['Job']['JobID'])
		#Query used for inserting the data
		sql_insert_query="""
							INSERT INTO cad2fab.system_jobs(serial,jobid,loaddate)
							VALUES (%s,%s,NOW())
							ON CONFLICT (serial,jobid)
							DO UPDATE SET loaddate = NOW();
							"""
		pgDB.querymany(sql_insert_query,jobIN)
		pgDB.close()


	def insertBundle(self):
		#List to insert to bundles table
		bundleIN = []
		#Loop through all levels in the job
		jobdata = xmlParse.data['MITEK_SHOPNET_MARKUP_LANGUAGE_FILE']["Job"]
		leveldata = jobdata["Level"]
		if type(leveldata) == dict:
			data = []
			data.append(leveldata)
		else:
			data = leveldata
		for level in data:
			#Loop through all bundles in the level
			for bundle in level["Bundle"]:
				#Data to import to the database
				bundleIN.append((bundle['BundleGuid'],bundle['JobID'],level['Description'],bundle['Label'],bundle['Type']),)
		pgDB = dbc.DB_Connect(xmlParse.credentials)
		pgDB.open()
		#Query used for inserting data to the database
		sql_insert_query="""
							INSERT INTO cad2fab.system_bundles(bundleguid,jobid,level_description,label,type)
							VALUES (%s,%s,%s,%s,%s)
							ON CONFLICT (bundleguid)
							DO UPDATE SET jobid = EXCLUDED.jobid, level_description = EXCLUDED.level_description,
							label = EXCLUDED.label, type = EXCLUDED.type;
							"""
		pgDB.querymany(sql_insert_query,bundleIN)
		pgDB.close()


	def insertPanel(self):
		c = 0
		#List column data for panels table
		panelIN = []
		HeaderInfo = []
		#Loop through all the levels in the job
		jobdata = xmlParse.data['MITEK_SHOPNET_MARKUP_LANGUAGE_FILE']["Job"]
		leveldata = jobdata["Level"]
		if type(leveldata) == dict:
			data = []
			data.append(leveldata)
		else:
			data = leveldata
		for level in data:
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
							
							HeaderInfo.append((self.sCadFilepath,bundle['Panel']['BundleGuid'],bundle['Panel']['PanelGuid'],round(float(bundle['Panel']['Height'])*25.4),round(float(bundle['Panel']['WallLength'])*25.4),round(float(bundle['Panel']['Thickness'])*25.4),1),)
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
					
					HeaderInfo.append((self.sCadFilepath,panel['BundleGuid'],panel['PanelGuid'],round(float(panel['Height'])*25.4),round(float(panel['WallLength'])*25.4),round(float(panel['Thickness'])*25.4),1),)

		#Insert the panel data to the Database
		pgDB = dbc.DB_Connect(xmlParse.credentials)
		pgDB.open()
		#Query used for writing data to the database
		sql_insert_query="""
							INSERT INTO cad2fab.system_panels(bundleguid, panelguid, label, height, thickness,
							studspacing, studheight, walllength, category, boardfeet)
							VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
							ON CONFLICT (panelguid)
							DO UPDATE SET bundleguid = EXCLUDED.bundleguid, label = EXCLUDED.label,
							height = EXCLUDED.height,
							thickness = EXCLUDED.thickness, studspacing = EXCLUDED.studspacing,
							studheight = EXCLUDED.studheight, walllength = EXCLUDED.walllength,
							category = EXCLUDED.category, boardfeet = EXCLUDED.boardfeet;
							"""
		pgDB.querymany(sql_insert_query, panelIN)
		sql_insert_query_2="""
								INSERT INTO cad2fab.system_headers(scadfilepath,sordername,sitemname,uiitemheight,uiitemlength,uiitemthickness,uiitemid)
								VALUES(%s,%s,%s,%s,%s,%s,%s)
								ON CONFLICT (sitemname)
								DO UPDATE SET uiitemheight = EXCLUDED.uiitemheight, uiitemlength = EXCLUDED.uiitemlength,
								uiitemthickness = EXCLUDED.uiitemthickness
							"""
		pgDB.querymany(sql_insert_query_2, HeaderInfo)
		pgDB.close()
			

	def insertElements(self):
		#Counter for strings
		c2 = 0
		#List of data for elements table
		self.elementIN = []
		#loop through all the levels in the job
		jobdata = xmlParse.data['MITEK_SHOPNET_MARKUP_LANGUAGE_FILE']["Job"]
		leveldata = jobdata["Level"]
		if type(leveldata) == dict:
			data = []
			data.append(leveldata)
		else:
			data = leveldata
		for level in data:
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
								xmlParse.appendElement(self,board,'Board',None)
						#Add sheets to the list if they exist
						if 'Sheet' in panel.keys():
							#loop through all the sheets in the panel
							for sheet in panel['Sheet']:
								#add the sheet data to the list
								xmlParse.appendElement(self,sheet,'Sheet',None)
						#Add SubAssemblies to the list if they exist and are in a list format
						#SubAssemblies will be in list format if there are >1 in the current panel
						if 'SubAssembly' in panel.keys() and type(panel['SubAssembly']) == list:
							#loop through the SubAssemblies
							subassemblyCT = 1
							for subassembly in panel['SubAssembly']:
								#are there boards in the subassembly?
								if 'Board' in subassembly.keys():
									#loop through all the boards in the subassembly
									for boardsub in subassembly['Board']:
										#when the board isn't the rough opening board add it to the list
										if boardsub['FamilyMemberName'] != 'RoughOpening':
											xmlParse.appendElement(self,boardsub,'Sub-Assembly Board',subassemblyCT)
										else: #add the rough cutout to the list 
											#(only works when there is 1 rough out per subassembly due to element guid creation)
											boardsub['PanelGuid'] = subassembly['PanelGuid']
											boardsub['BoardGuid'] = subassembly['SubAssemblyGuid'] + str(subassemblyCT)
											boardsub['FamilyMember'] = subassembly['FamilyMember']
											boardsub['FamilyMemberName'] = 'Rough cutout'
											boardsub['Material']['Size'] = 0
											boardsub['Material']['ActualThickness'] = 0

											xmlParse.appendElement(self,boardsub,'Sub-Assembly Cutout',subassemblyCT)
								#add subassembly without point data
								xmlParse.appendElement(self,subassembly,'Sub Assembly',subassemblyCT)
								subassemblyCT += 1
						# if there is only one subassembly in the panel
						if 'SubAssembly' in panel.keys() and type(panel['SubAssembly']) == dict:
							#check for a rough opening sub-board
							subassemblyCT = 1
							#loop through all the boards in the subassembly
							for boardsub in panel['SubAssembly']['Board']:
								#Check if the sub board is the rough opening
								if boardsub['FamilyMemberName'] != 'RoughOpening':

									xmlParse.appendElement(self,boardsub,'Sub-Assembly Board',subassemblyCT)
								
								else: #add the rough cutout to the list 
									#(only works when there is 1 rough out per subassembly due to element guid creation)

									boardsub['PanelGuid'] = panel['SubAssembly']['PanelGuid']
									boardsub['BoardGuid'] = panel['SubAssembly']['SubAssemblyGuid']+ str(subassemblyCT)
									boardsub['FamilyMember'] = panel['SubAssembly']['FamilyMember']
									boardsub['FamilyMemberName'] = 'Rough cutout'
									boardsub['Material']['Size'] = 0
									boardsub['Material']['ActualThickness'] = 0

									xmlParse.appendElement(self,boardsub,'Sub-Assembly Cutout',subassemblyCT)

							#add subassembly without point data

							subassembly = {
								'PanelGuid': panel['SubAssembly']['PanelGuid'],
								'SubAssemblyGuid': panel['SubAssembly']['SubAssemblyGuid'],
								'FamilyMember': panel['SubAssembly']['FamilyMember'],
								'FamilyMemberName':panel['SubAssembly']['FamilyMemberName'],
								'Width':panel['SubAssembly']['Width']
							}
							xmlParse.appendElement(self,subassembly,'Sub Assembly',subassemblyCT)

					# if the panel is a string (only 1 panel in the bundle)
					elif type(panel) == str:
						#add the boards to the list if they exist
						if 'Board' in bundle['Panel'].keys() and c2 == 0:
							#loop through all the boards in the panel
							for board in bundle['Panel']['Board']:
								#add the data to the list
								xmlParse.appendElement(self,board,'Board',None)
						#add the sheets to the list if they exist
						if 'Sheet' in bundle['Panel'].keys() and c2 == 0:
							#loop through the sheets in the panel
							for sheet in bundle['Panel']['Sheet']:
								#add the data for the sheets to the list
								xmlParse.appendElement(self,sheet,'Sheet',None)
						#Add Sub Assemblies to the list if they exist, are list type
						if 'SubAssembly' in bundle['Panel'].keys() and type(bundle['Panel']['SubAssembly']) == list and c2 == 0:
							#loop through all the subassemblies
							subassemblyCT = 1
							for subassembly in bundle['Panel']['SubAssembly']:
								#are there boards in the subassembly?
								if 'Board' in subassembly.keys():
									#loop through all the boards in the subassembly
									for boardsub in subassembly['Board']:
										#when the board isn't the rough opening board add it to the list
										if boardsub['FamilyMemberName'] != 'RoughOpening':
											xmlParse.appendElement(self,boardsub,'Sub-Assembly Board',subassemblyCT)
										else: #add the rough cutout to the list 
											#(only works when there is 1 rough out per subassembly due to element guid creation)
											boardsub['PanelGuid'] = subassembly['PanelGuid']
											boardsub['BoardGuid'] = subassembly['SubAssemblyGuid'] + str(subassemblyCT)
											boardsub['FamilyMember'] = subassembly['FamilyMember']
											boardsub['FamilyMemberName'] = 'Rough cutout'
											boardsub['Material']['Size'] = 0
											boardsub['Material']['ActualThickness'] = 0
											boardsub['Material']['MaterialsId']

											xmlParse.appendElement(self,boardsub,'Sub-Assembly Cutout',subassemblyCT)
								
								#add subassembly without point data
								xmlParse.appendElement(self,subassembly,'Sub Assembly',subassemblyCT)
								subassemblyCT += 1
						#Add the subassembly if it exists and is dictionary type
						if 'SubAssembly' in bundle['Panel'].keys() and type(bundle['Panel']['SubAssembly']) == dict and c2 == 0:
							#check if the subassembly has a rough opening in the panel
							subassemblyCT = 1
							#loop through all the boards in the subassembly
							for boardsub in bundle['Panel']['SubAssembly']['Board']:
								for boardsub in panel['SubAssembly']['Board']:
								#Check if the sub board is the rough opening
									if boardsub['FamilyMemberName'] != 'RoughOpening':
										xmlParse.appendElement(self,boardsub,'Sub-Assembly Board',subassemblyCT)
								else: #add the rough cutout to the list 
									#(only works when there is 1 rough out per subassembly due to element guid creation)
									boardsub['PanelGuid'] = panel['SubAssembly']['PanelGuid']
									boardsub['BoardGuid'] = panel['SubAssembly']['SubAssemblyGuid']+ str(subassemblyCT)
									boardsub['FamilyMember'] = panel['SubAssembly']['FamilyMember']
									boardsub['FamilyMemberName'] = 'Rough cutout'
									boardsub['Material']['Size'] = 0
									boardsub['Material']['ActualThickness'] = 0
									boardsub['Material']['MaterialsId']

									xmlParse.appendElement(self,boardsub,'Sub-Assembly Cutout',subassemblyCT)
							#add subassembly without point data
							subassembly = {
								'PanelGuid': panel['SubAssembly']['PanelGuid'],
								'SubAssemblyGuid': panel['SubAssembly']['SubAssemblyGuid'],
								'FamilyMember': panel['SubAssembly']['FamilyMember'],
								'FamilyMemberName':panel['SubAssembly']['FamilyMemberName'],
								'Width':panel['SubAssembly']['Width']
							}
							xmlParse.appendElement(self,subassembly,'Sub Assembly',subassemblyCT)
					c2+=1
					#reset counter after 1 string panel
					if c2 == 29:
						c2 = 0
		#insert the list to the database
		pgDB = dbc.DB_Connect(xmlParse.credentials)
		pgDB.open()
		#Query used for writing data to the database
		sql_insert_query="""
							INSERT INTO cad2fab.system_elements(panelguid,elementguid,type,familymember,description,
												size,actual_thickness,actual_width,materialdesc,species,b1x,b1y,b2x,
												b2y,b3x,b3y,b4x,b4y,e1x,e1y,e2x,e2y,e3x,e3y,e4x,e4y,assembly_id)
							VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
							ON CONFLICT (elementguid)
							DO UPDATE SET panelguid = EXCLUDED.panelguid, type = EXCLUDED.type,
							familymember = EXCLUDED.familymember, description = EXCLUDED.description,
							size = EXCLUDED.size,actual_thickness = EXCLUDED.actual_thickness,
							actual_width = EXCLUDED.actual_width,materialdesc = EXCLUDED.materialdesc,species = EXCLUDED.species,
							b1x = EXCLUDED.b1x,b1y = EXCLUDED.b1y,b2x = EXCLUDED.b2x,b2y = EXCLUDED.b2y,
							b3x = EXCLUDED.b3x,b3y = EXCLUDED.b3y,b4x = EXCLUDED.b4x,b4y = EXCLUDED.b4y,
							e1x = EXCLUDED.e1x,e1y = EXCLUDED.e1y,e2x = EXCLUDED.e2x,e2y = EXCLUDED.e2y,
							e3x = EXCLUDED.e3x,e3y = EXCLUDED.e3y,e4x = EXCLUDED.e4x,e4y = EXCLUDED.e4y,
							assembly_id = EXCLUDED.assembly_id;
							"""
		pgDB.querymany(sql_insert_query,self.elementIN)
		pgDB.close()


	def xmlMain(self):
		self.insertJob(self)
		self.insertBundle(self)
		self.insertPanel(self)
		self.insertElements(self)


if __name__ == "__main__":
	#get filepath to XML file from user
	filepath = "Python_Script/dataExtract_EHX/xmlFiles/231769W2.xml"

	#init the class
	xmlParse(filepath)
	#parse the data and send to DB
	xmlParse.xmlMain(xmlParse)
	

#Written by Jacob OBrien for BraveCS
#March 2023