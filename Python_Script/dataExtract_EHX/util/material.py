import dataBaseConnect as dbc
from Parameters import Parameters
from fractions import Fraction
import math

class Material:
    refMatTypes = ["OSB", "DOW", "ZIP", "DENSGLAS","SOUNDBOARD","NEOPOR"]
    refFastener = {
        "SCREWS" : [110, 401],
        "STAPLES" : [120, 402],
        "NAILS" : [130, 403]
    }
    materialTypes : list[str]
    def __init__(self, sheet, parms:Parameters) -> None:
        self.sheet = sheet
        #Width
        if '48' in sheet['size']: 
            self._width = 48
        
        #Length
        if '96' in sheet['size']:
            self._length = 96
        elif '108' in sheet['size']:
            self._length = 96

        #Thickness 
        self._thickness = sheet['actual_thickness']

        #Material Type
        mat : str = sheet['materialdesc']
        for reftype in self.refMatTypes:        
            if reftype in mat:
                self.material = reftype
                break
        #Searches the parameters to determine what fastener should be used with the specified material
        matParmsIndex = parms._tabNames.index('Material')
        for matType in parms._parmList[matParmsIndex]:
            if self.material in matType:
                if str(self._length) in matType:
                    if str(self._width) in matType:
                        if self.getThickFraction() in matType:
                            self.fastener = parms._parmList[matParmsIndex][matType]['value']
                            self.placeNum = self.refFastener[self.fastener][1]
                            self.fastenNum = self.refFastener[self.fastener][0]                            
                            break

        
            


    def getWidth(self, units:str):
        """unit options: inch, mm."""
        if units == 'inch':
            return self.width
        if units == 'mm':
            return self.width * 25.4
        
    def getLength(self, units:str):
        """unit options: inch, mm."""
        if units == 'inch':
            return self.length
        if units == 'mm':
            return self.length * 25.4
        
    def getThickness(self, units:str):
        """unit options: inch, mm, fraction."""
        if units == 'inch':
            return self.thickness
        if units == 'mm':
            return self.thickness * 25.4
    
    def getThickFraction(self):
        val = self._thickness
        if val != 0:
            valdec = math.modf(val)
            dec = ''
            whole = ''
            wholepart = False
            decpart = False
            if valdec[1] > 0: 
                whole = str(int(valdec[1]))
                wholepart = True
            if valdec[0] > 0: 
                dec = str(Fraction(valdec[0]).limit_denominator(16))
                decpart = True
            if wholepart and decpart:    thickness = whole + '-' + dec
            elif wholepart:    thickness = whole
            elif decpart:    thickness = dec
        else:
            thickness = 0
        return thickness
    
    def getMaterial(self) -> str:
        return self.material
    
    def getPlaceType(self) -> int:
        re
        
