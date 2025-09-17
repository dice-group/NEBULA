import json
import logging
from datetime import datetime

from claim_worthiness_check import dummy_claim_check, claim_buster
from database import databasemanager
from evidence_retrieval import elastic_search
import settings
from exception_handling.exceptions import UnsupportedStage
# from org.diceresearch.nebula.coref_resolution import spacy_coref
from coref_resolution import coreference_resolution
from utils import llm_based_final_classification
from evidence_retrieval import llm_based_summary
from translation import neamt_translator
from indicators.main import run_indicator_check_api
from utils.util import SetEncoder

from utils import notification


def goNextLevel(identifier):
    """
    Increments and executes next stage
    :param identifier: ID
    :return:
    """
    current = databasemanager.getOne(settings.results_table_name, identifier)

    stage_number = current[settings.stage_number]
    input_lang = current[settings.results_inputlang_column_name]
    input_text = current[settings.results_inputtext_column_name]
    translated_text = current[settings.results_translation_column_name]
    coref_text = current[settings.results_coref_column_name]
    sentences = current[settings.sentences]
    veracity_label = current[settings.results_veracity_label]

    # If the record could not be found
    if current is None:
        logging.error("Could not find this row in database {}".format(identifier))

    if sentences:
        claims = json.loads(sentences)

    # notification
    REGISTRATION_TOKEN = current[settings.results_notificationtoken_column_name]
    NOTIFICATION_TITLE = "Your result is ready!"
    NOTIFICATION_BODY = "Your result with ID {} is now available.".format(identifier)

    # Increase fact checking step
    current_stage = int(stage_number)
    next_stage = current_stage + 1
    logging.debug("Current stage is : {}".format(current_stage))

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
            neamt_translator.send_translation_request(input_text, identifier)
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
        # spacy_coref.replace_corefs(translated_text, identifier)
        if settings.coref_llms== "True":
            coreference_resolution.calculate_coref_using_api_call(translated_text, identifier)
        else:
            coreference_resolution.send_coref_request(translated_text, identifier)

    elif next_stage == 3:
        logging.debug("Claim check")

        if settings.module_claimworthiness == "dummy":
            dummy_claim_check.check(coref_text, identifier)
        else:
            claim_buster.check(coref_text, identifier)

    elif next_stage == 4:
        logging.debug("Evidence retrieval")
        elastic_search.retrieve(claims, identifier)

    elif next_stage == 5:
        logging.debug("Summary retrieval")
        llm_based_summary.generate(claims, identifier)

    elif next_stage == 6:
        logging.debug("LLM based single claims classification")
        llm_based_final_classification.calculate(claims, identifier)

    elif next_stage == 7:
        logging.debug("final LLM based classification")
        llm_based_final_classification.calculate_final_decision(claims, coref_text, identifier)

    # elif next_stage == 8:
    #     logging.debug('Query the trained model')
    #     predictions.predict(claims, identifier)
    #
    # elif next_stage == 9:
    #     logging.debug('Query the trained RNN model')
    #     predictions.predict_mean(claims, identifier)

    elif next_stage == 8:
        logging.debug('Run indicator check')
        # run indicators if label is false
        if veracity_label == settings.false_label:
            indicators = run_indicator_check_api(current)
            status = settings.completed
            indicator_json = json.dumps(indicators, cls=SetEncoder)
            databasemanager.update_json_step(settings.results_table_name, settings.results_indicator_check,
                                        indicator_json, identifier)
        else:
            # otherwise show skipped status
            status = settings.skipped

        # update and increase the step
        databasemanager.update_step(settings.results_table_name, settings.results_indicator_check_status,
                                    status, identifier)
        databasemanager.increase_the_stage(settings.results_table_name, identifier)
        goNextLevel(identifier)

    elif next_stage == 9:
        logging.info("Finished processing orch: {}".format(identifier))
        # set status as done and send push notification to device token if existing
        databasemanager.update_step(settings.results_table_name, settings.status, settings.done, identifier)
        if REGISTRATION_TOKEN:
            notification.send_firebase_notification(REGISTRATION_TOKEN, NOTIFICATION_TITLE, NOTIFICATION_BODY)
            databasemanager.delete_from_column(settings.results_table_name,
                                               settings.results_notificationtoken_column_name)
    else:
        raise UnsupportedStage



