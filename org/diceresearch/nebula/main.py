import json
import threading
import uuid
from logging.config import fileConfig

import databasemanager
import orchestrator
from flask import Flask, request, Response

import settings
from data.results import ResponseStatus, Status, Provenance
from utils.util import trim, translate_to_classes
from veracity_detection import predictions

app = Flask(__name__)
fileConfig(settings.logging_config)

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
    if not text:
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
    ver_score_str = tempjson[12]
    # get veracity score if available
    veracity_score = predictions.aggregate(ver_score_str, 'mean') if ver_score_str is not None else None
    # translate score to classes
    # needs to be changed if we already have the classes and not the score
    veracity_label = translate_to_classes(veracity_score, settings.low_threshold, settings.high_threshold,
                                          settings.class_labels) if veracity_score is not None else None
    explanation = ""
    status = tempjson[14]
    check_timestamp = tempjson[17]
    provenance = Provenance(check_timestamp, settings.knowledge_timestamp, settings.model_timestamp)
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
    if isinstance(result, Response):
        return result
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
    if isinstance(result, Response):
        return result
    result = get_json_with_db_columns(result)
    return Response(result, status=200, mimetype='application/json')

@app.route('/textsearch', methods=['GET', 'POST'])
def textsearch():
    args = request.args
    text = args.get('text')
    result = databasemanager.select_basedon_text(text)
    if result is None or result == "null":
        return Response(ResponseStatus(status="Error", text="Nothing found with this text {}".format(text)).get_json(),
                    status=400, mimetype='application/json')
    return Response(ResponseStatus(results=result).get_json(is_pretty=True), status=200, mimetype='application/json')


def get_result_from_id(id):
    if id is None:
        return Response(ResponseStatus(status="Error", text="ID is required").get_json(),
                        status=400, mimetype='application/json')
    result = databasemanager.select_basedon_id(id)
    if result is None or result == "null":
        return Response(ResponseStatus(status="Error", text="Nothing found with this id {}".format(id)).get_json(),
                        status=400, mimetype='application/json')
    return result


def get_json_with_db_columns(input):
    """
    FIXME just add a select query to databasemanager to get the results like we want
    this doesn't address the nested json strings
    :param result:
    :return:
    """
    result = json.loads(input)
    return ResponseStatus(id=result[0], stage_number=result[1], input_text=result[2], input_lang=result[3],
                              translation=result[4], translation_status=result[5], claim_check=result[6],
                              claim_check_status=result[7], evidence_retrieval=result[8],
                              evidence_retrieval_status=result[9], stance_detection=result[10],
                              stance_detection_status=result[11], wiseone=result[12], wiseone_status=result[13],
                              status=result[14], version=result[15], error_body=result[16],
                              check_timestamp=result[17]).get_json(is_pretty=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=80)