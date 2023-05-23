from flask import Flask, request, Response
import uuid
import databasemanager
import orchestrator
import threading

app = Flask(__name__)


@app.route('/test')
@app.route('/default')
def test():
    return Response("{\"test\": \"ok\"}", status=200, mimetype='application/json')


def startpipeline(text, lang):
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
    id = startpipeline(text, lang)

    return Response("{\"id\": \"" + id + "\"}", status=200, mimetype='application/json')


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
    return Response(result, status=200, mimetype='application/json')


if __name__ == '__main__':
    app.run()
