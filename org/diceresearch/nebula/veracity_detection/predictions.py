import threading

import numpy as np
import pandas as pd
import torch

import settings, orchestrator, databasemanager
from veracity_detection.aggregation import AggregationProcessor


def aggregate(json, type):
    aggregation_processor = AggregationProcessor(json)
    result = aggregation_processor.process(type)
    return result


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
    df2 = df.groupby(['claim'])[['stance_score']].agg({"stance_score": list})
    scores = np.array([np.array(score[0], dtype=np.float32) for score in df2.values])

    # get prediction
    prediction = model.test_model(torch.from_numpy(scores)).numpy()

    df2['wise_score'] = prediction

    # update database
    databasemanager.update_step(settings.results_table_name, settings.results_wiseone_column_name,
                                df2.to_json(orient='index'), identifier)
    databasemanager.update_step(settings.results_table_name, settings.results_wiseone_column_status, settings.completed,
                                identifier)
    databasemanager.increase_the_stage(settings.results_table_name, identifier)

    # go next level
    thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
    thread.start()