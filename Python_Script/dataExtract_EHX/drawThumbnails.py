from PIL import Image, ImageDraw    		#Requires Python >=3.7, pip install Pillow
from util import dataBaseConnect as dbc
import os
#import math								#Built in to Python, only needed for safe rounding

class GenPreview():
	def __init__(self) -> None:
		#get credentials an open the database
		self.credentials = dbc.getCred()
		pgDB = dbc.DB_Connect(self.credentials)
		pgDB.open()
		#select the panelguids and bundleids from the database
		sql_select_query = 'SELECT * FROM panel'
		self.panelData = []
		result = pgDB.query(sql_select_query)
		for row in result:
			self.panelData.append([row[1], row[0]])
		#select the panelguid, elementguid, type, and elevation points from the elements table
		self.elementData = []
		sql_select_query = 'SELECT * FROM elements'
		result2 = pgDB.query(sql_select_query)
		for row in result2:
			self.elementData.append([row[0],row[1],row[2],row[17],row[18],row[19],
		       						row[20],row[21],row[22],row[23],row[24]])
		pgDB.close()


	def previewMain(self):
		#loop through all panelData rows, ct is counter, row is data
		for row in self.panelData:
			#get the jobID of the current panel
			pgDB = dbc.DB_Connect(self.credentials)
			pgDB.open()
			sql_jobid_query = f"SELECT jobid FROM bundle WHERE bundleguid = '{row[1]}'"
			jobid = pgDB.query(sql_jobid_query)
			pgDB.close()
			
			#if output/jobID doesn't exist create the folder then set name = filepath/panelguid.png
			if not os.path.exists(f'Python_Script/dataExtract_EHX/output/{jobid[0][0]}/'):
				os.makedirs(f'Python_Script/dataExtract_EHX/output/{jobid[0][0]}/')

			name = (f'Python_Script/dataExtract_EHX/output/{jobid[0][0]}/' + row[0] + '.png')

			#find the boundries of each panel
			minheight = 10000
			maxheight = 0
			minwidth = 10000
			maxwidth = 0

			for elemrow in self.elementData:
				#if the element is the same panel and is a board or a sheet
				if row[0] == elemrow[0] and (elemrow[2] == 'Board' or elemrow[2] == 'Sheet'):
					#find max and min X values of the current panel
					if elemrow[3] > maxwidth:
						maxwidth = elemrow[3]
					if elemrow[5] > maxwidth:
						maxwidth = elemrow[5]
					if elemrow[7] > maxwidth:
						maxwidth = elemrow[7]
					if elemrow[9] > maxwidth:
						maxwidth = elemrow[9]
					if elemrow[3] < minwidth:
						minwidth = elemrow[3]
					if elemrow[5] < minwidth:
						minwidth = elemrow[5]
					if elemrow[7] < minwidth:
						minwidth = elemrow[7]
					if elemrow[9] < minwidth:
						minwidth = elemrow[9]
					#find max and min y values of the current panel
					if elemrow[4] > maxheight:
						maxheight = elemrow[4]
					if elemrow[6] > maxheight:
						maxheight = elemrow[6]
					if elemrow[8] > maxheight:
						maxheight = elemrow[8]
					if elemrow[10] > maxheight:
						maxheight = elemrow[10]
					if elemrow[4] < minheight:
						minheight = elemrow[4]
					if elemrow[6] < minheight:
						minheight = elemrow[6]
					if elemrow[8] < minheight:
						minheight = elemrow[8]
					if elemrow[10] < minheight:
						minheight = elemrow[10]

			#get scaling factor for points
			height = maxheight-minheight
			width = maxwidth-minwidth
			#check if the max scale is based on width or height
			if 1000/height <= 1840/width:
				scale = 1000/height
				#code for safe scale rounding
				#scale = int(math.floor(1000/height))
			elif 1840/width < 1000/height:
				scale = 1840/width
				#code for safe scale rounding
				#scale = int(math.floor(1840/width))

			#translate the elements such that the starting point is (0,0)
			translateX = minwidth
			translateY = minheight
			
			#Image background (color type, size(px), (R,G,B,Transparency))
			outimage = Image.new('RGBA',(1920,1080),(255,255,255,255))
			#Enter draw mode
			draw = ImageDraw.Draw(outimage)
			#loop through all elements
			for elemrow in self.elementData:
				# if the element belongs to the current panel and is a sheet draw it
				if elemrow[0] == row[0] and elemrow[2] == 'Sheet':
					coordinates = [(int(round((elemrow[3] - translateX ) * scale)) + 40,
									int(round((elemrow[4] - translateY ) * scale)) + 40),
										(int(round((elemrow[5] - translateX ) * scale)) + 40,
										int(round((elemrow[6] - translateY ) * scale)) + 40),
										(int(round((elemrow[7] - translateX ) * scale)) + 40,
										int(round((elemrow[8] - translateY ) * scale)) + 40),
										(int(round((elemrow[9] - translateX ) * scale)) + 40,
										int(round((elemrow[10] - translateY ) * scale)) + 40)]
					#draw a polygon connecting the points, fill & outline are (RGBA) and width is px
					draw.polygon(coordinates,fill=(0,154,255,255),outline=(127,127,127,127),width=1)
			#loop through all elements again (drawings are layered, so this is required)
			for elemrow in self.elementData:
				#if the element is a board or sub assembly board draw it
				if elemrow[0] == row[0] and (elemrow[2] == 'Board'or elemrow[2] == 'Sub-Assembly Board'):
					coordinates = [(int(round((elemrow[3] - translateX ) * scale)) + 40,
									int(round((elemrow[4] - translateY ) * scale)) + 40),
										(int(round((elemrow[5] - translateX ) * scale)) + 40,
										int(round((elemrow[6] - translateY ) * scale)) + 40),
										(int(round((elemrow[7] - translateX ) * scale)) + 40,
										int(round((elemrow[8] - translateY ) * scale)) + 40),
										(int(round((elemrow[9] - translateX ) * scale)) + 40,
										int(round((elemrow[10] - translateY ) * scale)) + 40)]
					#draw a polygon connecting the points, fill is Null, outline is (RGBA) and width is px
					draw.polygon(coordinates,fill=None,outline=(0,0,0,255),width=2)
			#Flip the image vertically (0,0 is the top left, which is being changed to the bottom left)
			outimage = outimage.transpose(method=Image.FLIP_TOP_BOTTOM)
			outimage = outimage.transpose(method=Image.FLIP_LEFT_RIGHT)
			#Output PNG image
			outimage.save(name)
	
if __name__ == "__main__":
	GenPreview.__init__(GenPreview)
	GenPreview.previewMain(GenPreview)

#Written by Jacob OBrien for BraveCS♥
#March 2023