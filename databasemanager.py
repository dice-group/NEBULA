import settings
import sqlite3

def update_step(which_table,which_step,which_result,row_identifier):
    try:
        sqliteConnection = sqlite3.connect(settings.database_name)
        cursor = sqliteConnection.cursor()
        print("Connected to SQLite")
        cursor.execute(f"UPDATE {which_table} SET {which_step} = ? WHERE IDENTIFIER = ?", (which_result, row_identifier))
        sqliteConnection.commit()
        print("Record Updated successfully ")
        cursor.close()

    except sqlite3.Error as error:
        print("Failed to update sqlite table", error)
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print("The SQLite connection is closed")