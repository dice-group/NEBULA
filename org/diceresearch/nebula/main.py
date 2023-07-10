from flask import Flask, request, Response
import uuid
import databasemanager
import orchestrator
import threading
import json
from datetime import datetime
import settings

from org.diceresearch.nebula.data.results import ResponseStatus, Status, Provenance
from org.diceresearch.nebula.utils.util import trim

app = Flask(__name__)

@app.route('/test')
@app.route('/default')
def test():
    return Response(ResponseStatus(status="OK").get_json(), status=200, mimetype='application/json')


def start_pipeline(text, lang):
    identifier = str(uuid.uuid4().hex)
    databasemanager.initiate_stage(identifier, text, lang)
    # call orchestrator
    thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
    thread.start()
    return identifier


@app.route('/check', methods=['GET', 'POST'])
def check():
    args = request.args
    text = args.get('text')
    lang = args.get('lang')
    # nd is not defined
    if lang is None:
        lang = "nd"
    if text is None:
        return Response(ResponseStatus(status="Error", text="Send the string as [text] argument in query string or body").get_json(), status=400,
                        mimetype='application/json')
    text = trim(text)
    id = start_pipeline(text, lang)

    return Response(ResponseStatus(id=id).get_json(), status=200, mimetype='application/json')


def do_mapping(result):
    tempjson = json.loads(result)
    id = tempjson[0]
    text = tempjson[2]
    lang = tempjson[3]
    veracity_score = float(tempjson[12])
    veracity_label = True if veracity_score > 0.5 else False
    explanation = ""
    status = tempjson[14]
    checkTimestamp = tempjson[17]
    provenance = Provenance(checkTimestamp, "2023-05-30", "2023-05-30")
    result = Status(id, status, text, lang, veracity_label, veracity_score, explanation, provenance)
    return result.get_json(is_pretty=True)


@app.route('/status', methods=['GET', 'POST'])
def status():
    """
    Outputs selected fields
    :return:
    """
    args = request.args
    id = args.get('id')
    result = get_result_from_id(id)
    # clean up result
    mapped_result = do_mapping(result)
    return Response(mapped_result, status=200, mimetype='application/json')

@app.route('/rawstatus', methods=['GET', 'POST'])
def raw_status():
    """
    Outputs everything in the result
    :return:
    """
    args = request.args
    id = args.get('id')
    result = get_result_from_id(id)
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


def get_result_from_id(id):
    if id is None:
        return Response(ResponseStatus(status="Error", text="ID is required").get_json(),
                        status=400, mimetype='application/json')
    result = databasemanager.select_basedon_id(id)
    if result is None or result == "null":
        return Response(ResponseStatus(status="Error", text="Nothing found with this id {}".format(id)).get_json(),
                        status=400, mimetype='application/json')
    return result

if __name__ == '__main__':
    app.run()