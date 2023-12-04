import json
import threading
from elasticsearch import Elasticsearch

import orchestrator
import settings
from data.results import EvidenceRetrievalResult, QueryResult

from utils.database_utils import update_database, log_exception


def do_query(text):
    """
    Query the Elastic Search endpoint
    :param text: Text to search for
    :return:
    """
    es = Elasticsearch(settings.elasticsearch_api_endpoint, timeout=30, max_retries=2, retry_on_timeout=True)
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

    return json.dumps(response.raw)


def retrieve(input, identifier):
    """
    Query the elastic search endpoint for each claim in the input
    :param input: claims
    :param identifier: ID
    :return: Evidence for each claim
    """
    try:
        # collect results
        er_result = EvidenceRetrievalResult()
        for claim in input:
            text = claim["text"]
            result = do_query(text)
            er_result.add(QueryResult(result, text))

        # if no scores are found
        if er_result.is_empty():
            raise ValueError('No evidence has been found.')

        tosave = er_result.get_json()

        # update database
        update_database(settings.results_evidenceretrieval_column_name,
                        settings.results_evidenceretrieval_column_status, tosave, identifier)

        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()
    except Exception as e:
        log_exception(e, identifier)