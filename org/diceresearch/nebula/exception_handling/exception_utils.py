import logging

from org.diceresearch.nebula import databasemanager, settings


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