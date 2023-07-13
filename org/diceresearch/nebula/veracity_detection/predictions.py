import threading

import pandas as pd
import torch

from nebula import settings, orchestrator, databasemanager


def predict(json, identifier):
    """

    :param json:
    :param identifier:
    :return:
    """

    # load trained model
    model = torch.load(settings.trained_model)

    # parse the stance scores only and feed to model
    df = pd.json_normalize(json['stances'])
    scores = torch.tensor(df.stance_score, dtype=torch.float32)

    # get prediction
    prediction = model.test_model(scores.unsqueeze(0)).item()

    # update database
    databasemanager.update_step(settings.results_table_name, settings.results_wiseone_column_name, prediction,
                                identifier)
    databasemanager.update_step(settings.results_table_name, settings.results_wiseone_column_status, settings.completed,
                                identifier)
    databasemanager.increase_the_stage(settings.results_table_name, identifier)

    # go next level
    thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
    thread.start()
