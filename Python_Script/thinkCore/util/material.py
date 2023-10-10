import math
from fractions import Fraction
import util.dataBaseConnect as dBC
from util.Parameters import Parameters


class Material:
    refMatTypes = {
        "OSB": 1,
        "PLYWOOD": 2,
        "NEOPOR": 3,
        "DENSGLAS": 4,
        "R3 ZIP": 5,
        "R6 ZIP": 6,
        "R9 ZIP": 7,
        "SOUNDBOARD": 8
    }
    # refMatTypes = ["OSB", "DOW", "ZIP", "DENSGLAS","NEOPOR","SOUNDBOARD"]
    refFastener = {
        "SCREW": [110, 401],
        "STAPLE": [120, 402],
        "NAIL": [130, 403]
    }

    materialTypes: list[str]

    def __init__(self, sheet, parms: Parameters) -> None:
        self.fastener = None
        self.placeNum = None
        self.fastenNum = None
        self.sheet = sheet
        # Width
        if "48" in sheet["size"]:
            self._width = 48

        # Length
        if "96" in sheet["size"]:
            self._length = 96
        elif "108" in sheet["size"]:
            self._length = 108

        # Thickness
        self._thickness = sheet["actual_thickness"]

        # Material Type
        mat: str = sheet["materialdesc"]
        self.refMatTypes
        for reftype in self.refMatTypes.keys():
            mat = mat.upper()
            if reftype in mat:
                self.material = reftype
                break

        if self.get_sheet_fastener(sheet):
            pass
        else:
            self.get_default_fastener(parms)

    def get_sheet_fastener(self, sheet: dict) -> bool:
        found_fastener = False
        pgDB = dBC.DB_Connect()
        pgDB.open()
        sql_var1 = sheet.get('elementguid')
        sql_determine = f"""
        select fastener_type
        from cad2fab.system_fasteners
        where elementguid = '{sql_var1}'
        """
        result = pgDB.query(sql_determine)
        result = str(result[0][0]).upper()
        for key in self.refFastener.keys():
            if key in result:
                self.fastener = key.title().upper()
                self.placeNum = self.refFastener[self.fastener][1]
                self.fastenNum = self.refFastener[self.fastener][0]
                found_fastener = True
                break
            else:
                found_fastener = False
        return found_fastener

    def get_default_fastener(self, parms):
        # Searches the parameters to determine what fastener should be used with the specified material
        matParms = parms._parmList.get("Material")
        for matType in matParms:
            if self.material in matType:
                if str(self._length) in matType:
                    if str(self._width) in matType:
                        if self.getThickFraction() in matType:
                            self.fastener = matParms.get(matType)["value"]
                            self.placeNum = self.refFastener[self.fastener][1]
                            self.fastenNum = self.refFastener[self.fastener][0]
                            break

    def getWidth(self, units: str):
        """unit options: inch, mm."""
        if units == "inch":
            return self.width
        if units == "mm":
            return self.width * 25.4

    def getLength(self, units: str):
        """unit options: inch, mm."""
        if units == "inch":
            return self.length
        if units == "mm":
            return self.length * 25.4

    def getThickness(self, units: str):
        """unit options: inch, mm, fraction."""
        if units == "inch":
            return self.thickness
        if units == "mm":
            return self.thickness * 25.4

    def getThickFraction(self):
        val = self._thickness
        if val != 0:
            valdec = math.modf(val)
            dec = ""
            whole = ""
            wholepart = False
            decpart = False
            if valdec[1] > 0:
                whole = str(int(valdec[1]))
                wholepart = True
            if valdec[0] > 0:
                dec = str(Fraction(valdec[0]).limit_denominator(16))
                decpart = True
            if wholepart and decpart:
                thickness = whole + "-" + dec
            elif wholepart:
                thickness = whole
            elif decpart:
                thickness = dec
        else:
            thickness = 0
        return thickness

    def getMaterial(self) -> str:
        return self.material

    def getMaterialCode(self):
        return self.refMatTypes[self.material]

    def getPlaceType(self) -> int:
        return self.placeNum

    def getFastenType(self) -> int:
        return self.fastenNum
