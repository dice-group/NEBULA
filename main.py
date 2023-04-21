from flask import Flask, request, Response
import uuid
import sqlite3
import settings
import json
import threading
import translator

app = Flask(__name__)


@app.route('/test')
@app.route('/default')
def test():
    return str("OK!")

def sendEvidenceRetrivalRequest(textToTranslate):
    pass

def startpipeline(text, lang):
    try:
        key = str(uuid.uuid4().hex)
        conn = sqlite3.connect(settings.database_name)
        cur = conn.cursor()
        cur.execute("""INSERT INTO """+settings.results_table_name+""" (IDENTIFIER,STAGE_NUMBER,INPUT_TEXT,INPUT_LANG) VALUES (?,?,?,?);""",(key,str(1),text,lang))
        conn.commit()
        if lang!="en":
            # start the translation step
            thread = threading.Thread(target=translator.sendTranslationRequest, args=(text,key))
            thread.start()
        else:
            #continue to next step
            thread = threading.Thread(target=sendEvidenceRetrivalRequest, args=(text))
            thread.start()
    except sqlite3.Error as error:
        print("Failed to read data from sqlite table", error)
    finally:
        if conn:
            conn.close()
            print("The SQLite connection is closed")
    return key

def retrive(id):
    result = ""
    try:
        conn = sqlite3.connect(settings.database_name)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM RESULTS where IDENTIFIER = '"+id+"'")
        record = cursor.fetchone()
        print("IDENTIFIER: "+ str(record[0]))
        print("STAGE_NUMBER: " + str(record[1]))
        print("INPUT_TEXT: " + str(record[2]))
        print("INPUT_LANG: " + str(record[3]))
        print("TRANSLATED_TEXT: " + str(record[4]))
        print("CLAIM_CHECK_WORTHINESS_RESULT: " + str(record[5]))
        print("EVIDENCE_RETRIVAL_RESULT: " + str(record[6]))
        print("STANCE_DETECTION_RESULT: " + str(record[7]))
        result = json.dumps(record)
        cursor.close()
    except sqlite3.Error as error:
        print("Failed to read data from sqlite table", error)
    finally:
        if conn:
            conn.close()
            print("The SQLite connection is closed")
    return result
@app.route('/check', methods=['GET', 'POST'])
def check():
    args = request.args
    text = args.get('text')
    lang = args.get('lang')
    # nd is not defined
    if lang is None:
        lang = "nd"
    if text is None:
        return Response("{\"error\": \"send the string as [text] argument in query string or body\"}", status=400, mimetype='application/json')
    id = startpipeline(text, lang)

    return Response("{\"id\": \""+id+"\"}", status=200, mimetype='application/json')


@app.route('/status', methods=['GET', 'POST'])
def status():
    args = request.args
    id = args.get('id')
    if id is None:
        return Response("{\"error\": \"id is required\"}", status=400, mimetype='application/json')
    result = retrive(id)
    return Response(result, status=200, mimetype='application/json')

if __name__ == '__main__':
    app.run()
