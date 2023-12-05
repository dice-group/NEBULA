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
from indicators.main import run_indicator_check_text
from veracity_detection import predictions

from utils import notification


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
    veracity_label = current[20]

    # If the record could not be found
    if current is None:
        logging.error("Could not find this row in database {}".format(identifier))

    if sentences:
        claims = json.loads(sentences)
    # Increase fact checking step
    current_stage = int(stage_number)

    # notification
    REGISTRATION_TOKEN = current[14]
    NOTIFICATION_TITLE = "Your result is ready!"
    NOTIFICATION_BODY = f"Your result with ID {identifier} is now available.",

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
        logging.debug('Query the trained RNN model')
        thread = threading.Thread(target=predictions.predict_rnn, args=(claims, identifier))
        thread.start()

    elif next_stage == 8:
        # run indicators if label is false
        if veracity_label == settings.false_label:
            indicators = run_indicator_check_text(input_text)
            status = settings.completed
            databasemanager.update_step(settings.results_table_name, settings.results_indicator_check,
                                        indicators, identifier)
        else:
            # otherwise show skipped status
            status = settings.skipped

        # update and increase the step
        databasemanager.update_step(settings.results_table_name, settings.results_indicator_check_status,
                                    status, identifier)
        databasemanager.increase_the_stage(settings.results_table_name, identifier)
        goNextLevel(identifier)

    elif next_stage == 9:
        # set status as done and send push notification to device token if existing
        databasemanager.update_step(settings.results_table_name, settings.status, settings.done, identifier)
        if REGISTRATION_TOKEN:
            notification.send_firebase_notification(REGISTRATION_TOKEN, NOTIFICATION_TITLE, NOTIFICATION_BODY)
            databasemanager.delete_from_column(settings.results_table_name,
                                               settings.results_notificationtoken_column_name)
    elif next_stage == 10:
        pass
    else:
        pass



