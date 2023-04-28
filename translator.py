import threading
import httpmanager
import settings
import databasemanager
import orchestrator
def sendTranslationRequest(textToTranslate, identifier):
    data = {
        "components": "no_ner, no_el, mbart_mt",
        "query": "\""+textToTranslate+"\""
        }
    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"}

    result = httpmanager.sendpost(settings.translatorEndpoint,data,headers)

    # save the result in database
    databasemanager.update_step(settings.results_table_name, settings.results_translation_column_name, result, identifier)

    # go next level
    thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
    thread.start()

