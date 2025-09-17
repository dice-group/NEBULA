import threading
from database import httpmanager
import settings
import orchestrator

from utils.database_utils import update_database, log_exception


def send_translation_request(textToTranslate, identifier):
    try:
        data = {
            "components": settings.translator,
            "query": "\""+textToTranslate+"\"",
            "lang": "de"
            }
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"}

        result = httpmanager.send_post(settings.translatorEndpoint, data, headers)

        result = result.replace("\"","")

        # save the result in database
        update_database(settings.results_translation_column_name,
                        settings.results_translation_column_status, result, identifier)

        # go next level
        orchestrator.goNextLevel(identifier)
    except Exception as e:
        log_exception(e, identifier)