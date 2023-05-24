import threading

import databasemanager
import httpmanager
import orchestrator
import settings


# <maintext>/<claim>


def doQuery(maintext, claim):
    # Define the endpoint (url), payload (sentence to be scored), api-key (api-key is sent as an extra header)
    api_endpoint = settings.stancedetection_api

    # Send the POST request to the API and store the api response
    api_response = httpmanager.sendget(api_endpoint, f"""{maintext}/{claim}""")

    # Print out the JSON payload the API sent back
    print(str(api_response))

    return api_response


def detect(main_text , claim, identifier):
    result = doQuery(main_text, claim)
    if result is None:
        print("error in retrieving the evidences")
    else:
        # save the result in database
        databasemanager.update_step(settings.results_table_name, settings.results_stancedetection_column_name, result,
                                    identifier)

        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()
