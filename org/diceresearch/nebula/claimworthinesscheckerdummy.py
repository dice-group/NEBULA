import threading

import orchestrator
import settings

from data.results import Sentence

from utils.database_utils import update_database, log_exception

"""This class is designed to store an incoming text as a single claim. It is used for datasets that consist of 
individual claims rather than large blocks of text."""


def check(text, identifier):
    try:
        # create response with a single claim
        # ID 0 and score 1
        dummy_response = Sentence(0, text, 1).get_json(in_array=True)

        # save in the database
        update_database(settings.sentences,
                        settings.results_claimworthiness_column_status, dummy_response, identifier)

        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()
    except Exception as e:
        log_exception(e, identifier)