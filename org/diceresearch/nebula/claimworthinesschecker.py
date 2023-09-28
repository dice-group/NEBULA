import json
import logging
import threading

import pandas as pd

import databasemanager
import httpmanager
import orchestrator
import settings


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

        # save in the database
        databasemanager.update_step(settings.results_table_name, settings.results_claimworthiness_column_name,
                                    results.to_json(orient='records'), identifier)
        databasemanager.update_step(settings.results_table_name, settings.results_claimworthiness_column_status,
                                    settings.completed, identifier)
        databasemanager.increase_the_stage(settings.results_table_name, identifier)
        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()
    except Exception as e:
        logging.exception(e)
        databasemanager.update_step(settings.results_table_name, settings.status, settings.error, identifier)
        databasemanager.update_step(settings.results_table_name, settings.error_msg, str(e), identifier)