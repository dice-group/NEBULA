import threading

from database import httpmanager
import orchestrator
import settings
from utils.database_utils import update_database, log_exception
from utils.llm_query import get_llm_instance

def calculate_coref_using_api_call(maintext, identifier):
    stanceDetector = get_llm_instance()
    result = stanceDetector.get_coref_res_from_api_call(maintext)
    # result = answer.replace("\n", " ")
    # save the result in database
    update_database(settings.results_coref_column_name,
                    settings.results_coref_column_status, result, identifier)

    # go next level
    orchestrator.goNextLevel(identifier)

def send_coref_request(text, identifier):
    """
    Sends coreference resolution request
    :param text: Text to perform on
    :param identifier: ID
    :return: Coreferenced input text
    """
    try:

        # input check
        if not text:
            raise ValueError('The coreference input is empty')

        # send request
        data = {"text": text}
        result = httpmanager.send_post(settings.coref_endpoint, data, None)

        # save the result in database
        update_database(settings.results_coref_column_name,
                        settings.results_coref_column_status, result, identifier)

        # go next level
        orchestrator.goNextLevel(identifier)
    except Exception as e:
        log_exception(e, identifier)