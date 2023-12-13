import logging
import sqlite3
import settings


def create_database_if_not_exists():
    """
    Creates the database if it doesn't exist already
    :return:
    """
    try:
        with sqlite3.connect(settings.database_name) as conn:
            conn.execute(f"""CREATE TABLE IF NOT EXISTS {settings.results_table_name}
                 (IDENTIFIER           TEXT    NOT NULL,
                 {settings.stage_number}            INTEGER     NOT NULL,
                 {settings.results_inputlang_column_name}           TEXT,
                 {settings.results_inputtext_column_name}           TEXT,
                 {settings.results_translation_column_name}           TEXT,
                 {settings.results_coref_column_name}           TEXT,
                 {settings.status}  TEXT,
                 {settings.results_translation_column_status}     TEXT,
                 {settings.results_coref_column_status}     TEXT,
                 {settings.results_claimworthiness_column_status}     TEXT,
                 {settings.results_evidenceretrieval_column_status}     TEXT,
                 {settings.results_stancedetection_column_status}     TEXT,
                 {settings.results_wiseone_column_status} TEXT,
                 {settings.results_wise_final_column_status} TEXT,
                 {settings.sentences}     TEXT,
                 {settings.results_wise_final_column_name} TEXT,
                 {settings.results_notificationtoken_column_name} TEXT,
                 VERSION TEXT,
                 ERROR_BODY TEXT,
                 CHECK_TIMESTAMP DATETIME,
                 {settings.results_veracity_label} TEXT,
                 {settings.results_indicator_check} TEXT,
                 {settings.results_indicator_check_status} TEXT
                 );""")
    except sqlite3.Error as error:
        logging.error("Failed to read data from sqlite table", error)
