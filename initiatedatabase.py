import sqlite3
import settings
# initiate the database
conn = sqlite3.connect(settings.database_name)
print("Opened database successfully")

conn.execute(f"""CREATE TABLE {settings.results_table_name}
         (IDENTIFIER           TEXT    NOT NULL,
         STAGE_NUMBER            INTEGER     NOT NULL,
         INPUT_TEXT           TEXT,
         INPUT_LANG           TEXT,
         {settings.results_translation_column_name}           TEXT,
         {settings.results_translation_column_status}     TEXT,
         {settings.results_claimworthiness_column_name} TEXT,
         {settings.results_claimworthiness_column_status} TEXT,
         {settings.results_evidenceretrival_column_name} TEXT,
         {settings.results_evidenceretrival_column_status} TEXT,
         {settings.results_stancedetection_column_name} TEXT,
         {settings.results_stancedetection_column_status} TEXT,
         STATUS TEXT,
         VERSION TEXT
         );""")

print("Table created successfully")

conn.close()

