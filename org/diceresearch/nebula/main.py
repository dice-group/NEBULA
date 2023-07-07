from flask import Flask, request, Response
import uuid
import databasemanager
import orchestrator
import threading
import json
from datetime import datetime
import settings

app = Flask(__name__)

@app.route('/test')
@app.route('/default')
def test():
    return Response("{\"test\": \"ok\"}", status=200, mimetype='application/json')


def start_pipeline(text, lang):
    identifier = str(uuid.uuid4().hex)
    databasemanager.initiate_stage(identifier, text, lang)
    # call orchestrator
    thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
    thread.start()
    return identifier


def trim(text):
    text = text.replace("\"","").replace("\'","");
    return text;


@app.route('/check', methods=['GET', 'POST'])
def check():
    args = request.args
    text = args.get('text')
    lang = args.get('lang')
    # nd is not defined
    if lang is None:
        lang = "nd"
    if text is None:
        return Response("{\"error\": \"send the string as [text] argument in query string or body\"}", status=400,
                        mimetype='application/json')
    text = trim(text)
    id = start_pipeline(text, lang)

    return Response("{\"id\": \"" + id + "\"}", status=200, mimetype='application/json')


def do_mapping(result):
    tempjson = json.loads(result)
    id = tempjson[0]
    status = tempjson[12]
    text = tempjson[2]
    lang = tempjson[3]
    veracity_score = 0.5
    explanation =""
    checkTimestamp = tempjson[15]
    provenance = "{ \"check_timestamp\":\""+str(checkTimestamp)+"\", \"knowledge_date\":\"2023-05-30\",\"model_date\":\"2023-05-30\"}"
    mapped_result = "{\"id\":\""+str(id)+"\",\"status\":\""+str(status)+"\",\"text\":\""+str(text)+"\",\"lang\":\""+str(lang)+"\",\"veracity_label\":\"supported\",\"veracity_score\":"+str(veracity_score)+",\"explanation\":\""+str(explanation)+"\",\"provenance\":"+str(provenance)+"}"
    return mapped_result
#supported
#refuted
#not enough information


@app.route('/status', methods=['GET', 'POST'])
def status():
    args = request.args
    id = args.get('id')
    if id is None:
        return Response("{\"error\": \"id is required\"}", status=400, mimetype='application/json')
    result = databasemanager.select_basedon_id(id)
    if result is None or result == "null":
        result = "{\"error\":\"nothing found with this id : " + id + "\"}"
        return Response(result, status=400, mimetype='application/json')
    mapped_result = do_mapping(result)
    return Response(mapped_result, status=200, mimetype='application/json')

@app.route('/rawstatus', methods=['GET', 'POST'])
def raw_status():
    args = request.args
    id = args.get('id')
    if id is None:
        return Response("{\"error\": \"id is required\"}", status=400, mimetype='application/json')
    result = databasemanager.select_basedon_id(id)
    if result is None or result == "null":
        result = "{\"error\":\"nothing found with this id : " + id + "\"}"
        return Response(result, status=400, mimetype='application/json')
    return Response(result, status=200, mimetype='application/json')

@app.route('/textsearch', methods=['GET', 'POST'])
def textsearch():
    args = request.args
    text = args.get('text')
    result = databasemanager.select_basedon_text(text)
    if result is None or result == "null":
        result = "{\"error\":\"nothing found with this text : " + text + "\"}"
        return Response(result, status=400, mimetype='application/json')
    return Response("{\"results\": "+result+"}", status=200, mimetype='application/json')


if __name__ == '__main__':
    app.run()