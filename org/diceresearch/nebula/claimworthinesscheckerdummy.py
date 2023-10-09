import logging
import threading

import databasemanager
import orchestrator
import settings

from data.results import Sentence

"""This class is designed to store an incoming text as a single claim. It is used for datasets that consist of 
individual claims rather than large blocks of text."""


def check(text, identifier):
    try:
        # create response with a single claim
        dummy_response = Sentence(text, 0, 1).get_json(in_array=True)

        # save in the database
        databasemanager.update_step(settings.results_table_name, settings.results_claimworthiness_column_name,
                                    str(dummy_response), identifier)
        databasemanager.update_step(settings.results_table_name, settings.results_claimworthiness_column_status,
                                    settings.completed, identifier)
        databasemanager.increase_the_stage(settings.results_table_name, identifier)

        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()
    except Exception as e:
        logging.exception(e)
        databasemanager.update_step(settings.results_table_name, settings.status, settings.error, identifier)
        databasemanager.update_step(settings.results_table_name, settings.error_msg, str(e), identifier)