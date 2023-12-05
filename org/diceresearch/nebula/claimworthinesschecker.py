import json
import logging
import threading

import pandas as pd

import databasemanager
import httpmanager
import orchestrator
import settings
from data.results import Sentence
from utils.database_utils import update_database, log_exception, update_database_json


def check(text, identifier):
    try:
        # /api/v2/score/text/sentences/<input_text>
        api_key = settings.claimbuster_apikey
        input_claim = text

        # Define the endpoint (url), payload (sentence to be scored), api-key (api-key is sent as an extra header)
        api_endpoint = settings.claimbuster_api_endpoint
        request_headers = {"x-api-key": api_key, "Content-Type":"application/json"}
        payload = {"input_text": input_claim}

        # Send the POST request to the API and store the api response
        api_response = httpmanager.send_post_json(api_endpoint, payload, request_headers)

        # limit the number of claims to the top k
        json_response = json.loads(api_response)
        results = pd.json_normalize(json_response, record_path='results')
        if len(results) > settings.claim_limit:
            results = results.sort_values('score', ascending=False).head(settings.claim_limit)

        # reorder columns
        cols = ['index', 'text', 'score']
        results = results[cols]

        # save in the database
        update_database_json(settings.sentences, settings.results_claimworthiness_column_status,
                        results.to_json(orient='records'), identifier)

        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()
    except Exception as e:
        log_exception(e, identifier)