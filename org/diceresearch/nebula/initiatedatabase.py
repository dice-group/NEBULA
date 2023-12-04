import sqlite3
import settings



# initiate the database
conn = sqlite3.connect(settings.database_name)
print("Opened database successfully")
try:
    conn.execute(f"""CREATE TABLE {settings.results_table_name}
         (IDENTIFIER           TEXT    NOT NULL,
         STAGE_NUMBER            INTEGER     NOT NULL,
         {settings.results_inputtext_column_name}           TEXT,
         {settings.results_inputlang_column_name}           TEXT,
         {settings.results_translation_column_name}           TEXT,
         {settings.results_translation_column_status}     TEXT,
         {settings.results_coref_column_name}           TEXT,
         {settings.results_coref_column_status}     TEXT,
         {settings.results_claimworthiness_column_name} TEXT,
         {settings.results_claimworthiness_column_status} TEXT,
         {settings.results_evidenceretrieval_column_name} TEXT,
         {settings.results_evidenceretrieval_column_status} TEXT,
         {settings.results_stancedetection_column_name} TEXT,
         {settings.results_stancedetection_column_status} TEXT,
         {settings.results_wiseone_column_name} TEXT,
         {settings.results_wiseone_column_status} TEXT,
         {settings.results_wise_final_column_name} TEXT,
         {settings.results_wise_final_column_status} TEXT,
         STATUS TEXT,
         VERSION TEXT,
         ERROR_BODY TEXT,
         CHECK_TIMESTAMP DATETIME
         );""")
    print("Table created successfully")
except sqlite3.Error as error:
    print("Failed to read data from sqlite table", error)
finally:
    if conn:
        conn.close()
        print("The SQLite connection is closed")



