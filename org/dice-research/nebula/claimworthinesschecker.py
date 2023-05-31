import threading

import databasemanager
import httpmanager
import orchestrator
import settings
import utilities


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
        api_response = httpmanager.sendpostjson(api_endpoint, payload, request_headers)
        # Print out the JSON payload the API sent back
        print(str(api_response))

        # save in the database
        databasemanager.update_step(settings.results_table_name, settings.results_claimworthiness_column_name,
                                    str(api_response), identifier)
        databasemanager.increaseTheStage(settings.results_table_name, identifier)
        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()
    except Exception as e:
        databasemanager.update_step(settings.results_table_name, "STATUS", "error", identifier)
        databasemanager.update_step(settings.results_table_name, "ERROR_BODY", str(e), identifier)
