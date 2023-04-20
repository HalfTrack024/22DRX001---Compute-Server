#tmp = 'panelguid, XPos, OpText, OpCode_FS, ZPos_FS, YPos_FS, SsUpPos_FS, OpCode_MS, ZPos_MS, YPos_MS, SsUpPos_MS, ImgName, OBJ_ID, loadDate'
#print(tmp.lower())

OpList = [[1,'ikl',69,0,0,0,69,6,0,0,'img',0],[1,'ikl',69,0,0,0,69,1,0,0,'img',0],
          [0,'ikl',69,5,0,0,69,6,0,0,'img',0],[0,'ikl',69,0,0,0,69,0,0,0,'img',0]]

count = 1

OplistSorted = sorted(OpList,key=lambda var:(var[0],var[3],var[7]))

for OpJob in OplistSorted:
    OpJob[-1] = count
    count += 1

for OpJob in OplistSorted:
    print(OpJob)