import json
import threading
from elasticsearch import Elasticsearch

import orchestrator
import settings
from data.results import Evidence

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

    return response.raw


def retrieve(input, identifier):
    """
    Query the elastic search endpoint for each claim in the input
    :param input: claims
    :param identifier: ID
    :return: Evidence for each claim
    """
    try:
        # collect results

        for claim in input:
            text = claim["text"]
            result = do_query(text)
            hits = result['hits']['hits']
            er_result = list()
            for h in hits:
                ev = h['_source']
                evidence_text = ev['text']
                evidence_url = ev['url']
                evidence_score = h['_score']
                er_result.append(Evidence(evidence_text, evidence_url, evidence_score).__dict__)
            claim["evidences"] = er_result


        # update database
        input_json = json.dumps(input)
        update_database(settings.sentences,
                        settings.results_evidenceretrieval_column_status, input_json, identifier)

        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()
    except Exception as e:
        log_exception(e, identifier)