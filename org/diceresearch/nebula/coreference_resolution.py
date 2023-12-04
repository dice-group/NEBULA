import threading

import httpmanager
import orchestrator
import settings
from utils.database_utils import update_database, log_exception


def send_coref_request(text, identifier):
    try:
        data = {"text": text}
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"}

        result = httpmanager.send_post(settings.coref_endpoint, data, headers)

        # save the result in database
        update_database(settings.results_translation_column_name,
                        settings.results_translation_column_status, result, identifier)

        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()
    except Exception as e:
        log_exception(e, identifier)