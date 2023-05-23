import threading
import json
from json import JSONDecodeError
from elasticsearch import Elasticsearch

import databasemanager
import orchestrator
import settings
def doQuery(text):
    try:
        es = Elasticsearch(settings.elasticsearch_api_endpoint)
        # Define the search query
        search_query = {
            "query": {
                "match": {
                    "query": text
                }
            }
        }

        # Execute the search query
        response = es.search(index=settings.elasticsearch_index_name, body=search_query)

        for hit in response["hits"]["hits"]:
            # Access the document fields
            print(hit["_source"])

        return response
    except Exception as ex:
        print(str(ex))
        return None

def retrive(text,identifier):
    result = doQuery(text)
    if result is None:
        print("error in retrieving the evidences")
    else:
        # save the result in database
        databasemanager.update_step(settings.results_table_name, settings.results_evidenceretrival_column_name, result, identifier)

        if(result["hits"]["hits"] == []):
            print("elastic search has no results")

        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()

def bulkRetrive(array_of_text,identifier):
    pass