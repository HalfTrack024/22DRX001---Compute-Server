#import EHXBuild.drawSTLs as dSTL # Draw STL Files
import EHXBuild.drawThumbnails as dThumb # Draw PNG Images
import EHXBuild.xmlparse as pEHX # Parse Data to System Tables
#import EHXBuild.findVolume # Not Used
import util.General_Help as gHelp


imageBuild = False
stlBuild = False
xmlparse = True

app_settings = gHelp.get_app_config()

if imageBuild:
    img = dThumb.GenPreview('RANDEK TEST PANELS', app_settings.get('ImageDropFolder'))
    img.previewMain()

	
if stlBuild:
    pass
    #stl = dSTL.GenSTL()
    #stl.mainSTL()

if xmlparse:
    #get filepath to XML file from user
    #filepath = "Python_Script/dataExtract_EHX/xmlFiles/231769W2.xml"
    filepath = r"C:\Users\Andrew Murray\source\Copia\22DRX001\Python_Script\thinkCore\EHXBuild\xmlFiles\DREXEL_DREXEL VTP.ehx"
    fileParse = pEHX.xmlParse(filepath)
    #init the class
    fileParse = pEHX.xmlParse(filepath)
    #parse the data and send to DB
    fileParse.xml_main()