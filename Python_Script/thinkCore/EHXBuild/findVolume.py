import os

from stl import mesh

#define data list
data = []

#get a list of all files in the directory
files = os.listdir()
#loop through files
for file in files:
    #if the file is an stl file
    if file[-4:] == '.stl':
        stl = mesh.Mesh.from_file(file)
        #calculate the volume in mm^3
        volume, cog, inertia = stl.get_mass_properties()
        #convert to mL and add units
        tmp = str(round(volume/1000,2))
        tmp = tmp + ' mL'
        data.append(file)
        data.append(tmp)

#clear terminal
os.system('cls')

#print the data
c = 0
while len(data) > c:
    print(data[c])
    print(data[c + 1])
    print('\n')
    c+=2
