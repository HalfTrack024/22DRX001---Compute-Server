#tmp = 'panelguid, XPos, OpText, OpCode_FS, ZPos_FS, YPos_FS, SsUpPos_FS, OpCode_MS, ZPos_MS, YPos_MS, SsUpPos_MS, ImgName, OBJ_ID, loadDate'
#print(tmp.lower())
from fractions import Fraction
import math

val = 1.437
intval = int(1.737)
valdec = math.modf(val)

dec = ''
whole = ''
wholepart = False
decpart = False
if valdec[1] > 0: 
    whole = str(int(valdec[1]))
    wholepart = True
if valdec[0] > 0: 
    dec = str(Fraction(0.).limit_denominator(16))
    decpart = True
if wholepart and decpart:    thickness = whole + '-' + dec
elif wholepart:    thickness = whole
elif decpart:    thickness = dec

