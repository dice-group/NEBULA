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
    logging.info("Orch:" + identifier)
    current = databasemanager.getOne(settings.results_table_name, identifier)
    STAGE_NUMBER = current[1]
    INPUT_TEXT = current[2]
    INPUT_LANG = current[3]
    TRANSLATED_TEXT = current[4]
    CLAIM_CHECK_WORTHINESS_RESULT = current[6]
    EVIDENCE_RETRIEVAL_RESULT = current[8]
    STANCE_DETECTION_RESULT = current[10]

    if current == None:
        logging.info("Could not find this row in database " + identifier)
    current_stage = int(STAGE_NUMBER)
    logging.info("Current stage is : " + str(current_stage))
    next_stage = current_stage + 1
    if next_stage == 1:
        databasemanager.update_step(settings.results_table_name, settings.status, settings.ongoing, identifier)
        databasemanager.update_step(settings.results_table_name, settings.timestamp, datetime.now().isoformat('#'),
                                    identifier)
        # translate
        # language
        if INPUT_LANG != "en":
            # start the translation step
            logging.info("Translation step")
            thread = threading.Thread(target=translator.send_translation_request, args=(INPUT_TEXT, identifier))
            thread.start()
        else:
            # update the stage
            logging.info("Skip the translation")
            databasemanager.update_step(settings.results_table_name, settings.results_translation_column_name,
                                        INPUT_TEXT, identifier)
            databasemanager.increase_the_stage(settings.results_table_name, identifier)
            goNextLevel(identifier)

    elif next_stage == 2:
        #claim
        if settings.module_claimworthiness == "dummy":
            thread = threading.Thread(target=claimworthinesscheckerdummy.check, args=(TRANSLATED_TEXT, identifier))
            thread.start()
        else:
            thread = threading.Thread(target=claimworthinesschecker.check, args=(TRANSLATED_TEXT, identifier))
            thread.start()

    elif next_stage == 3:
        # evidence retrieval
        if not CLAIM_CHECK_WORTHINESS_RESULT:
            logging.error("The claims worthiness response is null or empty")
            databasemanager.update_step(settings.results_table_name, settings.status, settings.error, identifier)
            databasemanager.update_step(settings.results_table_name, settings.error_msg,
                                        "The claims worthiness response is null or empty", identifier)
        else:
            try:
                jsonCheckdClaimsForWorthiness = json.loads(CLAIM_CHECK_WORTHINESS_RESULT)

                thread = threading.Thread(target=evidenceretrieval.retrieve,
                                          args=(jsonCheckdClaimsForWorthiness, identifier))
                thread.start()
            except JSONDecodeError as exp:
                logging.exception(exp)
                databasemanager.update_step(settings.results_table_name, settings.status, settings.error, identifier)
                databasemanager.update_step(settings.results_table_name, settings.error_msg, str(exp.msg), identifier)

    elif next_stage == 4:
        try:
            logging.info("Stance detection")

            # no evidence is found
            if not EVIDENCE_RETRIEVAL_RESULT:
                logging.error("Found no evidence")
                databasemanager.update_step(settings.results_table_name, settings.status, settings.error, identifier)
                databasemanager.update_step(settings.results_table_name, settings.error_msg,
                                            "Found no evidence", identifier)
            else:
                tempjson = json.loads(EVIDENCE_RETRIEVAL_RESULT)
                temp_evidences = tempjson["evidences"]
                logging.info(EVIDENCE_RETRIEVAL_RESULT)

                thread = threading.Thread(target=stancedetection.calculate,
                                          args=(temp_evidences, identifier))
                thread.start()
        except Exception as e:
            logging.exception("Error {0} with json {1}".format(e, EVIDENCE_RETRIEVAL_RESULT))
            databasemanager.update_step(settings.results_table_name, settings.status, settings.error, identifier)
            databasemanager.update_step(settings.results_table_name, settings.error_msg, str(e), identifier)

    elif next_stage == 5:
        logging.info('Query the trained model')
        try:
            if not STANCE_DETECTION_RESULT:
                logging.error("There are no stances scores")
                databasemanager.update_step(settings.results_table_name, settings.status, settings.error, identifier)
                databasemanager.update_step(settings.results_table_name, settings.error_msg,
                                            "There are no stances scores", identifier)
            else:
                tempjson = json.loads(STANCE_DETECTION_RESULT)
                thread = threading.Thread(target=predictions.predict,
                                              args=(tempjson, identifier))
                thread.start()
        except Exception as e:
            logging.exception(e)
            databasemanager.update_step(settings.results_table_name, settings.status, settings.error, identifier)
            databasemanager.update_step(settings.results_table_name, settings.error_msg, str(e), identifier)

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