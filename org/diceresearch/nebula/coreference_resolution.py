import threading

import httpmanager
import orchestrator
import settings
from utils.database_utils import update_database, log_exception


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
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()
    except Exception as e:
        log_exception(e, identifier)