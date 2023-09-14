import psycopg2 as psy

def dropTables():
    #Table query comands
    command = (
        "DROP TABLE IF EXISTS bundle,panel,jobs,elements CASCADE;"
    )
    conn = None
    try:
        # connect to the PostgreSQL server
        conn = psy.connect(
            user="test",
            password="1234",
            host="localhost",
            port="12345",
            database="TestDB"
            )
        cur = conn.cursor()
        # create table one by one
        cur.execute(command)
        # close communication with the PostgreSQL database server
        cur.close()
        # commit the changes
        conn.commit()
        print("Tables Sucessfully Dropped")
    except (Exception, psy.DatabaseError) as error:
            print("An error occurred:\n", error)
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    dropTables()


#Written by Jacob OBrien for BraveCS
#March 2023