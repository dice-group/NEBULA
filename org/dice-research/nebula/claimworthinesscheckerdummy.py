import threading

import databasemanager
import orchestrator
import settings

"""This class is designed to store an incoming text as a single claim. It is used for datasets that consist of 
individual claims rather than large blocks of text."""


def check(text, identifier):
    try:
        dummy_response = "{\"version\":\"dummy\",\"sentences\":\" " + text + " \",\"results\":[{\"text\":\" " + text + "\",\"index\":0,\"score\":1}]}"

        # save in the database
        databasemanager.update_step(settings.results_table_name, settings.results_claimworthiness_column_name,
                                    str(dummy_response), identifier)
        databasemanager.increase_the_stage(settings.results_table_name, identifier)
        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()
    except Exception as e:
        databasemanager.update_step(settings.results_table_name, "STATUS", "error", identifier)
        databasemanager.update_step(settings.results_table_name, "ERROR_BODY", str(e), identifier)
