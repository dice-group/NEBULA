import json
import threading
from elasticsearch import Elasticsearch

import databasemanager
import orchestrator
import settings


def do_query(text):
    try:
        es = Elasticsearch(settings.elasticsearch_api_endpoint)
        # Define the search query
        search_query = {
            "query": {
                "match": {
                    "text": {
                        "query": text
                    }
                }
            }
        }

        # Execute the search query
        response = es.search(index=settings.elasticsearch_index_name, body=search_query)

        for hit in response["hits"]["hits"]:
            # Access the document fields
            print(hit["_source"])

        return json.dumps(response.raw)
    except Exception as ex:
        print(str(ex))
        return None


def generate_result_tosave(all_results):
    result = "{\"evidences\":["
    counter = 0
    for r in all_results:
        result += r
        counter = counter + 1
        if counter < len(all_results):
            result += ","
    result += "]}"
    return result


def generate_one_block_of_result(resultOfQueries, originatlTextForQuery):
    return "{\"result\":" + str(resultOfQueries) + ",\"query\":\"" + str(originatlTextForQuery) + "\"}"


"""def retrive(text,identifier):
    result = doQuery(text)
    if result is None:
        print("error in retrieving the evidences")
    else:
        # save the result in database
        tosave = generateResultTosave(result, text)
        databasemanager.update_step(settings.results_table_name, settings.results_evidenceretrival_column_name, tosave, identifier)

#        if(result["hits"]["hits"] == []):
#            print("elastic search has no results")

        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()

#        {'version': '2',
#         'sentences': 'Now from January 1st: EU standard chip EPS replaces personal identity card Saturday, 20 Jul 2019 Facebook What has been standard for dogs and cats for years worldwide, will be gradually introduced from January 1st 2021 also for citizens of the European Union. This idea is not completely new, but with the project in the European Union now for the first time in a large style introduced in a community of states. 2022',
#         'results': [{
#                         'text': 'Now from January 1st: EU standard chip EPS replaces personal identity card Saturday, 20 Jul 2019 Facebook What has been standard for dogs and cats for years worldwide, will be gradually introduced from January 1st 2021 also for citizens of the European Union.',
#                         'index': 0, 'score': 0.5979533384}, {
#                         'text': 'This idea is not completely new, but with the project in the European Union now for the first time in a large style introduced in a community of states.',
#                         'index': 1, 'score': 0.7661571161}, {'text': '2022', 'index': 2, 'score': 0.37916248}]}

"""


def retrive(input, identifier):
    try:
        allResults = []
        for claim in input["results"]:
            text = claim["text"]
            result = do_query(text)
            allResults.append(generate_one_block_of_result(result, text))
        tosave = generate_result_tosave(allResults)
        databasemanager.update_step(settings.results_table_name, settings.results_evidenceretrival_column_name, tosave,
                                    identifier)
        databasemanager.increase_the_stage(settings.results_table_name, identifier)
        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()
    except Exception as e:
        databasemanager.update_step(settings.results_table_name, "STATUS", "error", identifier)
        databasemanager.update_step(settings.results_table_name, "ERROR_BODY", str(e), identifier)
