import settings
import sqlite3
import logging
import json


def __init__():
    logging.setLevel(logging.DEBUG)

def update_step(which_table,which_step,which_result,row_identifier):
    try:
        sqliteConnection = sqlite3.connect(settings.database_name)
        cursor = sqliteConnection.cursor()
        logging.info("Connected to SQLite")
        print("Connected to SQLite")
        cursor.execute(f"UPDATE {which_table} SET {which_step} = ? WHERE IDENTIFIER = ?", (which_result, row_identifier))
        sqliteConnection.commit()
        logging.info("Record Updated successfully ")
        print("Record Updated successfully ")
        cursor.close()
        #increase the stage
        increaseTheStage(which_table, row_identifier)
    except sqlite3.Error as error:
        logging.error("Failed to update sqlite table", error)
        print("Failed to update sqlite table"+ str(error))
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            logging.info("The SQLite connection is closed")
            print("The SQLite connection is closed")
def getOne(which_table, row_identifier):
    try:
        sqliteconnection = sqlite3.connect(settings.database_name)
        cursor = sqliteconnection.cursor()
        logging.info("Connected to SQLite")
        print("Connected to SQLite")
        cursor.execute(f"select * from {which_table}  WHERE IDENTIFIER = ?", (row_identifier,))
        one = cursor.fetchone()
        logging.info("SELECT done  ")
        cursor.close()
        return one

    except sqlite3.Error as error:
        logging.error("Failed to update sqlite table", error)
        print("Failed to update sqlite table"+str( error))
    finally:
        if sqliteconnection:
            sqliteconnection.close()
            logging.info("The SQLite connection is closed")

# don't use this method until you just want to skip a level
# this method will call in a update phase for each level
def increaseTheStage(which_table,row_identifier):
    one = getOne(which_table,row_identifier)
    if one == None:
        logging.warning("There are no results for this query")
        print("There are no results for this query")
    else:
        stage = int(one[1])
        stage = stage+1
        try:
            sqliteConnection = sqlite3.connect(settings.database_name)
            cursor = sqliteConnection.cursor()
            logging.info("Connected to SQLite")
            print("Connected to SQLite")
            cursor.execute(f"UPDATE {which_table} SET STAGE_NUMBER = ? WHERE IDENTIFIER = ?",
                           (stage, row_identifier))
            sqliteConnection.commit()
            logging.info("Record Updated successfully ")
            print("Record Updated successfully ")
            cursor.close()

        except sqlite3.Error as error:
            logging.error("Failed to update sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                logging.info("The SQLite connection is closed")

def initiate_stage(identifier,text,lang):
    try:
        conn = sqlite3.connect(settings.database_name)
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO """ + settings.results_table_name + """ (IDENTIFIER,STAGE_NUMBER,INPUT_TEXT,INPUT_LANG) VALUES (?,?,?,?);""",
            (identifier, str(0), text, lang))
        conn.commit()
    except sqlite3.Error as error:
        print()
    finally:
        if conn:
            conn.close()
            print("The SQLite connection is closed")

def select_basedon_id(identifier):
    try:
        conn = sqlite3.connect(settings.database_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM RESULTS where IDENTIFIER = '" + identifier + "'")
        record = cursor.fetchone()
        """print("IDENTIFIER: " + str(record[0]))
        print("STAGE_NUMBER: " + str(record[1]))
        print("INPUT_TEXT: " + str(record[2]))
        print("INPUT_LANG: " + str(record[3]))
        print("TRANSLATED_TEXT: " + str(record[4]))
        print("CLAIM_CHECK_WORTHINESS_RESULT: " + str(record[5]))
        print("EVIDENCE_RETRIVAL_RESULT: " + str(record[6]))
        print("STANCE_DETECTION_RESULT: " + str(record[7]))"""
        result = json.dumps(record)
        cursor.close()
    except sqlite3.Error as error:
        print("Failed to read data from sqlite table", error)
    finally:
        if conn:
            conn.close()
            print("The SQLite connection is closed")
    return result