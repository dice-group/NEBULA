import threading
import httpmanager
import settings
import databasemanager
import orchestrator
from org.diceresearch.nebula.exception_handling.exception_utils import log_exception


def send_translation_request(textToTranslate, identifier):
    try:
        data = {
            "components": "mbart_mt",
            "query": "\""+textToTranslate+"\"",
            "lang": "de"
            }
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"}

        result = httpmanager.send_post(settings.translatorEndpoint, data, headers)

        result = result.replace("\"","")

        # save the result in database
        databasemanager.update_step(settings.results_table_name, settings.results_translation_column_name, result,
                                    identifier)
        databasemanager.update_step(settings.results_table_name, settings.results_translation_column_status,
                                    settings.completed, identifier)
        databasemanager.update_step(settings.results_table_name, settings.results_translation_column_name, result, identifier)
        databasemanager.increase_the_stage(settings.results_table_name, identifier)
        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()
    except Exception as e:
        log_exception(e, identifier)