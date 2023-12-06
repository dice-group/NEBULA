import logging

from database import databasemanager
import settings


def update_database(column_name, status_column, result, id):
    """


    :param column_name: Column name
    :param status_column: Status column name
    :param result: Result to save
    :param id: ID
    :return:
    """
    databasemanager.update_step(settings.results_table_name, column_name, result, id)
    databasemanager.update_step(settings.results_table_name, status_column, settings.completed, id)
    databasemanager.increase_the_stage(settings.results_table_name, id)

def update_database_json(column_name, status_column, result, id):
    """

    :param table_name: Table name
    :param column_name: Column name
    :param status_column: Status column name
    :param result: Result to save
    :param id: ID
    :return:
    """
    databasemanager.update_json_step(settings.results_table_name, column_name, result, id)
    databasemanager.update_step(settings.results_table_name, status_column, settings.completed, id)
    databasemanager.increase_the_stage(settings.results_table_name, id)

def log_exception(exception_msg, identifier):
    """
    Logs exception to logger and to the database record
    :param exception_msg: Exception message
    :param identifier: ID
    :return:
    """
    logging.exception(exception_msg)
    databasemanager.update_step(settings.results_table_name, settings.status, settings.error, identifier)
    databasemanager.update_step(settings.results_table_name, settings.error_msg, exception_msg.msg, identifier)