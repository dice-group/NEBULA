import threading
import httpmanager
import settings
import databasemanager
import orchestrator
def sendTranslationRequest(textToTranslate, identifier):
    try:
        data = {
            "components": "mbart_mt",
            "query": "\""+textToTranslate+"\"",
            "lang": "de"
            }
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"}

        result = httpmanager.sendpost(settings.translatorEndpoint, data, headers)

        result = result.replace("\""," ")

        # save the result in database
        databasemanager.update_step(settings.results_table_name, settings.results_translation_column_name, result, identifier)
        databasemanager.increaseTheStage(settings.results_table_name, identifier)
        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()
    except Exception as e:
        databasemanager.update_step(settings.results_table_name, "STATUS", "error", identifier)
        databasemanager.update_step(settings.results_table_name, "ERROR_BODY", str(e), identifier)

