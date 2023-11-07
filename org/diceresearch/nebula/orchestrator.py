import json
import logging
import threading
from datetime import datetime
from json import JSONDecodeError

import claimworthinesschecker
import claimworthinesscheckerdummy
import databasemanager
import evidenceretrieval
import settings
import stancedetection
import translator
from veracity_detection import predictions


def goNextLevel(identifier):
    """
    Increments and executes next stage
    :param identifier: ID
    :return:
    """
    logging.info("Orch: {}".format(identifier))
    current = databasemanager.getOne(settings.results_table_name, identifier)
    STAGE_NUMBER = current[1]
    INPUT_TEXT = current[2]
    INPUT_LANG = current[3]
    TRANSLATED_TEXT = current[4]
    CLAIM_CHECK_WORTHINESS_RESULT = current[6]
    EVIDENCE_RETRIEVAL_RESULT = current[8]
    STANCE_DETECTION_RESULT = current[10]

    # If the record could not be found
    if current is None:
        logging.info("Could not find this row in database {}".format(identifier))

    # Increase fact checking step
    current_stage = int(STAGE_NUMBER)
    next_stage = current_stage + 1
    logging.info("Current stage is : {}".format(current_stage))

    if next_stage == 1:
        logging.debug("Translation")

        # set status to ongoing and set timestamp
        databasemanager.update_step(settings.results_table_name, settings.status, settings.ongoing, identifier)
        databasemanager.update_step(settings.results_table_name, settings.timestamp, datetime.now().isoformat('#'),
                                    identifier)

        # translate if language differs from english and we were not provided a translation already
        if INPUT_LANG != "en" and not TRANSLATED_TEXT:
            # start the translation step
            logging.info("Translation step")
            thread = threading.Thread(target=translator.send_translation_request, args=(INPUT_TEXT, identifier))
            thread.start()
        else:
            # skip the stage
            logging.info("Skipping translation")
            databasemanager.update_step(settings.results_table_name, settings.results_translation_column_name,
                                        INPUT_TEXT, identifier)
            databasemanager.update_step(settings.results_table_name, settings.results_translation_column_status,
                                        settings.skipped, identifier)
            databasemanager.increase_the_stage(settings.results_table_name, identifier)
            goNextLevel(identifier)

    elif next_stage == 2:
        logging.debug("Claim check")

        if settings.module_claimworthiness == "dummy":
            thread = threading.Thread(target=claimworthinesscheckerdummy.check, args=(TRANSLATED_TEXT, identifier))
            thread.start()
        else:
            thread = threading.Thread(target=claimworthinesschecker.check, args=(TRANSLATED_TEXT, identifier))
            thread.start()

    elif next_stage == 3:
        logging.debug("Evidence retrieval")

        # no claims found
        if CLAIM_CHECK_WORTHINESS_RESULT is None:
            log_exception("The claims worthiness response is null.", identifier)
        else:
            jsonCheckdClaimsForWorthiness = json.loads(CLAIM_CHECK_WORTHINESS_RESULT)
            thread = threading.Thread(target=evidenceretrieval.retrieve, args=(jsonCheckdClaimsForWorthiness, identifier))
            thread.start()

    elif next_stage == 4:
        logging.debug("Stance detection")

        # no evidence is found
        if EVIDENCE_RETRIEVAL_RESULT is None:
            log_exception("The evidence retrieval result is null.", identifier)
        else:
            tempjson = json.loads(EVIDENCE_RETRIEVAL_RESULT)
            temp_evidences = tempjson["evidences"]
            logging.info(EVIDENCE_RETRIEVAL_RESULT)
            thread = threading.Thread(target=stancedetection.calculate, args=(temp_evidences, identifier))
            thread.start()

    elif next_stage == 5:
        logging.info('Query the trained model')

        # no stances found
        if STANCE_DETECTION_RESULT is None:
            log_exception("The stance detection result is null.", identifier)
        else:
            tempjson = json.loads(STANCE_DETECTION_RESULT)
            thread = threading.Thread(target=predictions.predict, args=(tempjson, identifier))
            thread.start()
    elif next_stage == 6:
        databasemanager.update_step(settings.results_table_name, settings.status, settings.done, identifier)
    elif next_stage == 7:
        pass
    elif next_stage == 8:
        pass
    elif next_stage == 9:
        pass
    else:
        pass


def log_exception(exception_msg, identifier):
    """
    Logs exception to logger and to the database record
    :param exception_msg: Exception message
    :param identifier: ID
    :return:
    """
    logging.exception(exception_msg)
    databasemanager.update_step(settings.results_table_name, settings.status, settings.error, identifier)
    databasemanager.update_step(settings.results_table_name, settings.error_msg, exception_msg, identifier)