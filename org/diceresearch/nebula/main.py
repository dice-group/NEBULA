import json
import threading
import uuid
from logging.config import fileConfig

import databasemanager
import orchestrator
from flask import Flask, request, Response, jsonify

import settings
from data.results import ResponseStatus, Provenance
from initiatedatabase import create_database_if_not_exists
from utils.util import trim

app = Flask(__name__)
fileConfig(settings.logging_config)


"""
    The API endpoints are configured here. 
"""

@app.route('/test')
@app.route('/default')
def test():
    """
        Tests if the endpoint is up

        :return: An OK status message
        """
    return jsonify({'Status': 'OK'}), 200


def start_pipeline(text, translated_text, lang):
    """
        Starts the fact-checking process

        :param text: Text to be fact checked
        :param lang: Language the text is in
        :return: ID that can be used to follow up the fact-checking process
    """
    text = trim(text)

    # creates ID and creates record on database
    identifier = str(uuid.uuid4().hex)
    databasemanager.initiate_stage(identifier, text, lang, translated_text)

    # call orchestrator to start the pipeline
    thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
    thread.start()
    return identifier


@app.route('/check', methods=['GET', 'POST'])
def check():
    """
        Checks a text for veracity.
        If the language is not specified, or any other than en is specified, the text will be translated to english first.
        If the text is not specified, it will return an Error.

        :return: ID of the text to be fact checked
    """

    # parse arguments
    if request.method == 'GET':
        args = request.args
    else:
        args = request.json

    # retrieve arguments
    text = args.get('text')
    translated_text = args.get('translation')
    lang = args.get('lang')
    registration_token = args.get('token')

    # Assign not defined if language is not specified
    if not lang:
        lang = "nd"

    # Assign empty string
    if not translated_text:
        translated_text = ''

    # Return BadRequest if text is not specified
    if not text:
        return jsonify({'Error': 'Text is required'}), 400

    # Start pipeline
    id = start_pipeline(text, translated_text, lang)

    # Update the registration token in the database
    if registration_token:
        databasemanager.update_step(settings.results_table_name, settings.results_notificationtoken_column_name,
                                    registration_token, id)

    # return id to check later on
    return jsonify({'ID': id}), 200


@app.route('/status', methods=['GET', 'POST'])
def status():
    """
    Outputs selected fields
    :return:
    """

    # parse arguments
    if request.method == 'GET':
        args = request.args
    else:
        args = request.json

    # validate ID
    id = args.get('id')
    if not id:
        return jsonify({'Error': 'Request ID is required'}), 400

    # fetch result
    result = databasemanager.get_status_as_json(id)

    # check if result is valid
    if not result:
        return jsonify({'Error': 'No record found with id {}'.format(id)}), 400

    # pretty print the result json and add provenance from settings
    first, = result
    j_obj = json.loads(first)
    j_obj['provenance'] = Provenance(settings.knowledge_timestamp, settings.model_timestamp).__dict__
    j_obj = json.dumps(j_obj, indent=3)
    return Response(j_obj, status=200, mimetype='application/json')


@app.route('/rawstatus', methods=['GET', 'POST'])
def raw_status():
    """
    Outputs everything in the result
    :return:
    """

    # parse arguments
    if request.method == 'GET':
        args = request.args

    else:
        args = request.json
    id = args.get('id')

    # validate id
    if not id:
        return jsonify({'Error': 'Request ID is required'}), 400

    # fetch result
    result = databasemanager.get_raw_status_as_json(id)

    # check if result is valid
    if not result:
        return jsonify({'Error': 'No record found with id {}'.format(id)}), 400

    # pretty print the result json and add provenance from settings
    first, = result
    j_obj = json.loads(first)
    j_obj['provenance'] = Provenance(settings.knowledge_timestamp, settings.model_timestamp).__dict__
    j_obj = json.dumps(j_obj, indent=3)
    return Response(j_obj, status=200, mimetype='application/json')


@app.route('/textsearch', methods=['GET', 'POST'])
def textsearch():

    # parse arguments
    if request.method == 'GET':
        args = request.args
    else:
        args = request.json
    text = args.get('text')

    # validate text
    if not text:
        return jsonify({'Error': 'Text is required in this mode'}), 400

    # searches database for the given text
    result = databasemanager.select_basedon_text(text)

    # check if result is valid
    if not result:
        return jsonify({'Error': 'No record found with id {}'.format(id)}), 400

    # returns all results if found
    return Response(ResponseStatus(results=result).get_json(is_pretty=True), status=200, mimetype='application/json')


if __name__ == '__main__':
    create_database_if_not_exists()
    app.run(host='0.0.0.0', port=8080)