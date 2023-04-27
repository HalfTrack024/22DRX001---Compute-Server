import psycopg2 as psy

def genTables(credentials):
    #Table query comands
    commands = (
            """
            CREATE TABLE elements (
            panelguid VARCHAR (255),
            elementguid VARCHAR(255) PRIMARY KEY,
            type VARCHAR(255)
            ,familymember VARCHAR(255)
            ,description VARCHAR(255)
            ,size VARCHAR(255)
            ,actual_thickness NUMERIC(6,3)
            ,actual_width NUMERIC(6,3)
            ,materialdesc VARCHAR(255)
            ,b1x NUMERIC(6,3)
            ,b1y NUMERIC(6,3)
            ,b2x NUMERIC(6,3)
            ,b2y NUMERIC(6,3)
            ,b3x NUMERIC(6,3)
            ,b3y NUMERIC(6,3)
            ,b4x NUMERIC(6,3)
            ,b4y NUMERIC(6,3)
            ,e1x NUMERIC(6,3)
            ,e1y NUMERIC(6,3)
            ,e2x NUMERIC(6,3)
            ,e2y NUMERIC(6,3)
            ,e3x NUMERIC(6,3)
            ,e3y NUMERIC(6,3)
            ,e4x NUMERIC(6,3)
            ,e4y NUMERIC(6,3)
            ,assembly_id VARCHAR(255)
            );
            """
    )
    #Run each of the above commands seperately so they all run even if a table already exists
    #for command in commands:
    command = commands
    conn = None
    try:
        # connect to the PostgreSQL server
        conn = psy.connect(
            user=credentials[0],
            password=credentials[1],
            host=credentials[2],
            port=credentials[3],
            database=credentials[4]
            )
        cur = conn.cursor()
        # create table one by one
        cur.execute(command)
        # close communication with the PostgreSQL database server
        cur.close()
        # commit the changes
        conn.commit()
        print("Table Sucessfully Created")
    except (Exception, psy.DatabaseError) as error:
        print("An error occurred:\n", error)
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    #get sql server credentials from user
	choice1 = input('Use saved credentials? (y/n):  ')
	if str.lower(choice1) == 'y':
		print('Using saved credentials')
		save = open('Python_Script\\dataExtract_EHX\\util\\credentials.txt','r')
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
                        
#Generate the tables
genTables(credentials)


#Written by Jacob OBrien for BraveCS
#March 2023