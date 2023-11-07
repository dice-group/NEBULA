import settings
import sqlite3
import logging
import json


def update_step(which_table,which_step,which_result,row_identifier):
    """
    Updates a single value in the database.

    :param which_table: Table name
    :param which_step: Column name
    :param which_result: Column value
    :param row_identifier: ID
    :return:
    """
    try:
        with sqlite3.connect(settings.database_name) as sqliteConnection:
            cursor = sqliteConnection.cursor()
            logging.debug("Connected to SQLite")

            cursor.execute(f"UPDATE {which_table} SET {which_step} = ? WHERE IDENTIFIER = ?", (str(which_result), row_identifier))
            sqliteConnection.commit()
            logging.debug("Record Updated successfully ")

            cursor.close()
    except sqlite3.Error as error:
        logging.error("Failed to update sqlite table", error)


def getOne(which_table, row_identifier):
    """
    Returns a single row based on the id
    :param which_table: Table name
    :param row_identifier: ID
    :return:
    """
    try:
        with sqlite3.connect(settings.database_name) as sqliteConnection:
            cursor = sqliteConnection.cursor()
            logging.debug("Connected to SQLite")
            cursor.execute(f"select * from {which_table}  WHERE IDENTIFIER = ?", (row_identifier,))
            one = cursor.fetchone()
            logging.debug("SELECT done  ")
            cursor.close()
            return one
    except sqlite3.Error as error:
        logging.error("Failed to update sqlite table {}".format(error))


# call after successfully run of a level
def increase_the_stage(which_table, row_identifier):
    """
    Increases the stage a row is in by 1
    :param which_table: Table name
    :param row_identifier: ID
    :return:
    """
    one = getOne(which_table,row_identifier)
    if one == None:
        logging.warning("There are no results for this query")
    else:
        stage = int(one[1])
        stage = stage+1
        try:
            with sqlite3.connect(settings.database_name) as sqliteConnection:
                cursor = sqliteConnection.cursor()
                logging.info("Connected to SQLite")
                cursor.execute(f"UPDATE {which_table} SET STAGE_NUMBER = ? WHERE IDENTIFIER = ?",
                               (stage, row_identifier))
                sqliteConnection.commit()
                logging.info("Record Updated successfully ")
                cursor.close()
        except sqlite3.Error as error:
            logging.error("Failed to update sqlite table", error)


def initiate_stage(identifier,text, lang, translated_text):
    """
    Creates a record when we first submit the text
    :param identifier:  ID
    :param text: Original text
    :param lang: Language
    :param translated_text: Translated text
    :return:
    """
    try:
        with sqlite3.connect(settings.database_name) as conn:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO """ + settings.results_table_name + f""" (IDENTIFIER,STAGE_NUMBER,
                {settings.results_inputtext_column_name}, {settings.results_translation_column_name}, 
                {settings.results_inputlang_column_name}) VALUES (?,?,?,?,?);""",
                (identifier, str(0), text, translated_text, lang))
            conn.commit()
    except sqlite3.Error as error:
        logging.error("Failed to add to sqlite table", error)

def select_basedon_id(identifier):
    try:
        with sqlite3.connect(settings.database_name) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {settings.results_table_name} where IDENTIFIER = '" + identifier + "'")
            record = cursor.fetchone()
            result = json.dumps(record)
            cursor.close()
    except sqlite3.Error as error:
        logging.error("Failed to read data from sqlite table", error)
    return result

def select_basedon_text(text):
    try:
        with sqlite3.connect(settings.database_name) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {settings.results_table_name} where {settings.results_inputtext_column_name} = '" + text + "'")
            record = cursor.fetchall()

            allresults = []
            for row in record:
                row_dic = {}
                for idx, col in enumerate(cursor.description):
                    row_dic[col[0]] = row[idx]
                allresults.append(row_dic)
            finalJson = json.dumps(allresults)
            cursor.close()
    except sqlite3.Error as error:
        logging.error("Failed to read data from sqlite table", error)
    return finalJson