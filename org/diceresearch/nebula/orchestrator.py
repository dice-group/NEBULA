import json
import logging
import threading
from datetime import datetime

import claimworthinesschecker
import claimworthinesscheckerdummy
import coreference_resolution
import databasemanager
import evidenceretrieval
import settings
import stancedetection
import translator
from utils.database_utils import log_exception
from veracity_detection import predictions


def goNextLevel(identifier):
    """
    Increments and executes next stage
    :param identifier: ID
    :return:
    """
    current = databasemanager.getOne(settings.results_table_name, identifier)

    stage_number = current[1]
    input_lang = current[2]
    input_text = current[3]
    translated_text = current[4]
    coref_text = current[5]
    sentences = current[14]

    # If the record could not be found
    if current is None:
        logging.error("Could not find this row in database {}".format(identifier))

    if sentences:
        claims = json.loads(sentences)
    # Increase fact checking step
    current_stage = int(stage_number)
    next_stage = current_stage + 1
    logging.info("Current stage is : {}".format(current_stage))

    if next_stage == 1:
        logging.info("Orch: {}".format(identifier))
        logging.debug("Translation")

        # set status to ongoing and set timestamp
        databasemanager.update_step(settings.results_table_name, settings.status, settings.ongoing, identifier)
        databasemanager.update_step(settings.results_table_name, settings.timestamp, datetime.now().isoformat('#'),
                                    identifier)

        # translate if language differs from english and we were not provided a translation already
        if input_lang != "en" and not translated_text:
            # start the translation step
            logging.debug("Translation step")
            thread = threading.Thread(target=translator.send_translation_request, args=(input_text, identifier))
            thread.start()
        else:
            # skip the stage
            logging.debug("Skipping translation")
            databasemanager.update_step(settings.results_table_name, settings.results_translation_column_name,
                                        input_text, identifier)
            databasemanager.update_step(settings.results_table_name, settings.results_translation_column_status,
                                        settings.skipped, identifier)
            databasemanager.increase_the_stage(settings.results_table_name, identifier)
            goNextLevel(identifier)

    elif next_stage == 2:
        logging.debug("Coreference resolution")

        # no claims found
        if translated_text is None:
            log_exception("The translation response is null.", identifier)
        else:
            thread = threading.Thread(target=coreference_resolution.send_coref_request,
                                      args=(translated_text, identifier))
            thread.start()

    elif next_stage == 3:
        logging.debug("Claim check")

        if settings.module_claimworthiness == "dummy":
            thread = threading.Thread(target=claimworthinesscheckerdummy.check, args=(coref_text, identifier))
            thread.start()
        else:
            thread = threading.Thread(target=claimworthinesschecker.check, args=(coref_text, identifier))
            thread.start()

    elif next_stage == 4:
        logging.debug("Evidence retrieval")
        thread = threading.Thread(target=evidenceretrieval.retrieve, args=(claims, identifier))
        thread.start()

    elif next_stage == 5:
        logging.debug("Stance detection")
        thread = threading.Thread(target=stancedetection.calculate, args=(claims, identifier))
        thread.start()

    elif next_stage == 6:
        logging.debug('Query the trained model')
        thread = threading.Thread(target=predictions.predict, args=(claims, identifier))
        thread.start()

    elif next_stage == 7:
        # Final WISE
        # if WISE_RESULT is None:
        #     log_exception("The first wise result is null.", identifier)
        # else:
        #     tempjson = json.loads(WISE_RESULT)
        #     thread = threading.Thread(target=predictions.predict_rnn, args=(tempjson, identifier))
        #     thread.start()
        databasemanager.update_step(settings.results_table_name, settings.status, settings.done, identifier)
    elif next_stage == 8:
        pass
    elif next_stage == 9:
        pass
    elif next_stage == 10:
        pass
    else:
        pass