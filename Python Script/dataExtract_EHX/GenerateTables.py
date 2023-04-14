import psycopg2 as psy

def genTables(credentials):
    #Table query comands
    commands = (
        """
        CREATE TABLE Jobs (
        Serial SMALLSERIAL,
        JobID TEXT,
        LoadDate TIMESTAMP,
        PRIMARY KEY (Serial, JobID)
        );
        ""","""
        CREATE TABLE Bundle (
        BundleGUID VARCHAR (255),
        JobID TEXT,
        Level_Description VARCHAR(255),
        Label VARCHAR (255),
        Type VARCHAR (255),
        PRIMARY KEY (BundleGUID)
        );
        ""","""
        CREATE TABLE Panel (
        BundleGUID VARCHAR (255),
        PanelGUID VARCHAR (255),
        Label VARCHAR (255),
        Height NUMERIC(6,3),
        Thickness NUMERIC(6,3),
        StudSpacing NUMERIC(6,3),
        StudHeight NUMERIC(6,3),
        WallLength NUMERIC(6,3),
        Category VARCHAR (255),
        BoardFeet NUMERIC(6,3),
        PRIMARY KEY (PanelGUID)
        );
        ""","""
        CREATE TABLE Elements (
        PanelGUID VARCHAR (255),
        ElementGUID VARCHAR (255),
        Type VARCHAR (255),
        FamilyMember VARCHAR (255),
        Description VARCHAR (255),
        Size VARCHAR (255),
        Actual_Thickness NUMERIC(6,3),
        Actual_Width NUMERIC(6,3),
        MaterialsID VARCHAR (255),
        B1X NUMERIC(6,3),
        B1Y NUMERIC(6,3),
        B2X NUMERIC(6,3),
        B2Y NUMERIC(6,3),
        B3X NUMERIC(6,3),
        B3Y NUMERIC(6,3),
        B4X NUMERIC(6,3),
        B4Y NUMERIC(6,3),
        E1X NUMERIC(6,3),
        E1Y NUMERIC(6,3),
        E2X NUMERIC(6,3),
        E2Y NUMERIC(6,3),
        E3X NUMERIC(6,3),
        E3Y NUMERIC(6,3),
        E4X NUMERIC(6,3),
        E4Y NUMERIC(6,3),
        PRIMARY KEY (ElementGUID)
        );
        """,
        """
        CREATE TABLE QueueTest (
        PanelGuid CHAR(255),
        Next BOOLEAN,
        LoadDate TIMESTAMP,
        PRIMARY KEY (PanelGuid)
        );
        """
    )
    #Run each of the above commands seperately so they all run even if a table already exists
    for command in commands:
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
		save = open('credentials.txt','r')
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