import json
import threading
import uuid
from logging.config import fileConfig

from database import databasemanager
import orchestrator
from flask import Flask, request, Response, jsonify

import settings
from data.results import ResponseStatus, Provenance
from database.initiatedatabase import create_database_if_not_exists, drop_results_table
from utils.util import trim
from utils.llm_query import get_llm_instance

from flasgger import Swagger

app = Flask(__name__)

fileConfig(settings.logging_config)

#app.config['SWAGGER'] = {
#    'title': 'NEBULA API',
#    'uiversion': 3,
#   'description': 'API for the NEBULA fact-checking system.',
#}

swagger_config = {
    "title": 'NEBULA API',
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apidocs/apispec_1.json',  
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/" 
}

swagger = Swagger(app, config=swagger_config)

"""
    The API endpoints are configured here. 
"""

@app.route('/test')
@app.route('/default')
def test():
    """Endpoint to test if the API is up.
      ---
      tags:
        - Test
      responses:
        200:
          description: API is up.
          schema:
            type: object
            properties:
              status:
                type: string
                example: OK
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

        ---
    tags:
      - Fact-Checking
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: CheckInput
          required:
            - text
          properties:
            text:
              type: string
              description: The claim/text to be fact-checked.
              example: "The Eiffel Tower is in Berlin."
            lang:
              type: string
              description: The language of the text (e.g., 'en', 'de'). Defaults to 'nd' (not defined) if omitted.
              example: "en"
    responses:
      200:
        description: Successfully started the fact-checking process.
        schema:
          type: object
          properties:
            id:
              type: string
              description: The unique identifier for this fact-checking request.
              example: "a1b"
            status:
              type: string
              example: "OK"
      400:
        description: Bad Request - The 'text' parameter was not provided in the JSON body.
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
        lang = "en"

    # Assign empty string
    if not translated_text:
        translated_text = ''

    # Return BadRequest if text is not specified
    if not text:
        return jsonify({'Error': 'Text is required'}), 400

    # parse unicode
    # text = bytes(text, 'utf-8').decode('unicode_escape')
    # translated_text = bytes(translated_text, 'utf-8').decode('unicode_escape')

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
    Use the ID obtained from the /check endpoint to output selected fields.
    ---
    tags:
      - Fact-Checking
    parameters:
      - name: id
        in: query
        type: string
        required: true
        description: The unique identifier for the fact-checking request.
    responses:
      200:
        description: The current status and result of the request.
        schema:
          id: StatusOutput
          properties:
            id:
              type: string
            status:
              type: string
              description: "The current stage of the pipeline (e.g., 'Completed', 'In-Progress')."
            text:
              type: string
            lang:
              type: string
            veracity_label:
              type: string
              description: "The final veracity label (e.g., 'True', 'False', 'Uncertain')."
            veracity_score:
              type: number
            explanation:
              type: string
            provenance:
              type: object
      400:
        description: Bad Request - The 'id' parameter was not provided.
      404:
        description: Not Found - No result found for the given ID.
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
    j_obj['provenance'] = Provenance(settings.knowledge_timestamp, settings.model_timestamp,
                                     settings.final_model_timestamp).__dict__
    j_obj = json.dumps(j_obj, indent=3, ensure_ascii=False).encode('utf8')
    return Response(j_obj, status=200, mimetype='application/json')


@app.route('/rawstatus', methods=['GET', 'POST'])
def raw_status():
    """
    Use the ID obtained from the /check endpoint to output everything in the result.
    ---
    tags:
      - Debugging
    parameters:
      - name: id
        in: query
        type: string
        required: true
        description: The unique identifier for the fact-checking request.
    responses:
      200:
        description: The complete, raw database entry for the request.
      400:
        description: Bad Request - The 'id' parameter was not provided.
      404:
        description: Not Found - No result found for the given ID.
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
    j_obj['provenance'] = Provenance(settings.knowledge_timestamp, settings.model_timestamp,
                                     settings.final_model_timestamp).__dict__
    j_obj = json.dumps(j_obj, indent=3, ensure_ascii=False).encode('utf8')
    return Response(j_obj, status=200, mimetype='application/json')


@app.route('/textsearch', methods=['GET', 'POST'])
def textsearch():
    """Search the database for previous fact-checks of a given text.
    ---
    tags:
      - Searching
    parameters:
      - name: text
        in: query
        type: string
        required: true
        description: The text to search for in the database.
    responses:
      200:
        description: A list of results matching the text.
      404:
        description: Not Found - Nothing found with this text.
    """

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
    # drop table for first time
    # drop_results_table()
    stanceDetector = get_llm_instance()
    create_database_if_not_exists()
    # app.run(host='0.0.0.0', port=8080)
    app.run(host='0.0.0.0',port=5001)
