import EHXBuild.drawSTLs as dSTL # Draw STL Files
import EHXBuild.drawThumbnails as dThumb # Draw PNG Images
import EHXBuild.xmlparse as pEHX # Parse Data to System Tables
import EHXBuild.findVolume # Not Used


imageBuild = False
stlBuild = False
xmlparse = True

if imageBuild:
    img = dThumb.GenPreview()
    img.previewMain()

	
if stlBuild:
    stl = dSTL.GenSTL()
    stl.mainSTL()

if xmlparse:
    #get filepath to XML file from user
    #filepath = "Python_Script/dataExtract_EHX/xmlFiles/231769W2.xml"
    filepath = r"Python_Script\dataExtract_EHX\EHXBuild\xmlFiles\RANDEK TEST PANELS copy.EHX"
    fileParse = pEHX.xmlParse(filepath)
    #init the class
    fileParse = pEHX.xmlParse(filepath)
    #parse the data and send to DB
    fileParse.xml_main()