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

from flasgger import Swagger 

app = Flask(__name__)
fileConfig(settings.logging_config)


app.config['SWAGGER'] = {
    'title': 'NEBULA API',
    'uiversion': 3,
    'description': 'API for the NEBULA fact-checking system.'
}

swagger = Swagger(app)


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
    return ResponseStatus(status="OK").__dict__


def start_pipeline(text, lang):
    """
        Starts the fact-checking process

        :param text: Text to be fact checked
        :param lang: Language the text is in
        :return: ID that can be used to follow up the fact-checking process
    """
    text = trim(text)
    identifier = str(uuid.uuid4().hex)
    databasemanager.initiate_stage(identifier, text, lang)

    # call orchestrator
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

    text = args.get('text')
    lang = args.get('lang')

    # Assign not defined if language is not specified
    if not lang:
        lang = "nd"

    # Return BadRequest if text is not specified
    if not text:
        return Response(ResponseStatus(status="Error",
                                       text="Send the string as [text] argument in query string or body").get_json(),
                        status=400,
                        mimetype='application/json')

    # Start pipeline
    id = start_pipeline(text, lang)

    # return id
    return ResponseStatus(id=id).__dict__


def do_mapping(result):
    """
        Maps the database result to a json
        TODO Temporarily computes the aggregate score, this is to be replaced once the second stage is ready
        :param result:
        :return: Result as a JSON string
    """
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
    id = args.get('id')

    # fetch result
    result = get_result_from_id(id)

    # if id is not valid, return error
    if isinstance(result, Response):
        return result

    # clean up result
    mapped_result = do_mapping(result)
    return Response(mapped_result, status=200, mimetype='application/json')

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

    # fetch result
    result = get_result_from_id(id)

    # if id is not valid, return error
    if isinstance(result, Response):
        return result

    # parse as json string
    result = get_json_with_db_columns(result)
    return Response(result, status=200, mimetype='application/json')


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

    # searches database for the given text
    result = databasemanager.select_basedon_text(text)

    # return error if not found
    if result is None or result == "null":
        return Response(ResponseStatus(status="Error", text="Nothing found with this text {}".format(text)).get_json(),
                    status=400, mimetype='application/json')

    # returns all results if found
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