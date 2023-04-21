import sqlite3
import settings
# initiate the database
conn = sqlite3.connect(settings.database_name)
print("Opened database successfully")

conn.execute('''CREATE TABLE RESULTS
         (IDENTIFIER           TEXT    NOT NULL,
         STAGE_NUMBER            INTEGER     NOT NULL,
         INPUT_TEXT           TEXT,
         INPUT_LANG           TEXT,
         TRANSLATED_TEXT           TEXT,
         CLAIM_CHECK_WORTHINESS_RESULT TEXT,
         EVIDENCE_RETRIVAL_RESULT TEXT,
         STANCE_DETECTION_RESULT TEXT
         );''')

print("Table created successfully")

conn.close()

