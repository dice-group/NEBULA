import json
import logging
import threading
from elasticsearch import Elasticsearch

import databasemanager
import orchestrator
import settings
from org.diceresearch.nebula.data.results import EvidenceRetrievalResult, QueryResult


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
            logging.info(hit["_source"])

        return json.dumps(response.raw)
    except Exception as ex:
        logging.exception(ex)
        return None


def retrieve(input, identifier):
    try:
        # collect results
        er_result = EvidenceRetrievalResult()
        for claim in input["results"]:
            text = claim["text"]
            result = do_query(text)
            er_result.add(QueryResult(result, text))
        tosave = er_result.get_json()

        # update database
        databasemanager.update_step(settings.results_table_name, settings.results_evidenceretrieval_column_name, tosave,
                                    identifier)
        databasemanager.update_step(settings.results_table_name, settings.results_evidenceretrieval_column_status,
                                   settings.completed, identifier)
        databasemanager.increase_the_stage(settings.results_table_name, identifier)

        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()
    except Exception as e:
        logging.exception(e)
        databasemanager.update_step(settings.results_table_name, settings.status, settings.error, identifier)
        databasemanager.update_step(settings.results_table_name, settings.error_msg, str(e), identifier)