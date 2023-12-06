import json
import threading

import numpy as np
import pandas as pd
import torch

from database import databasemanager
import settings, orchestrator
from utils.database_utils import update_database, log_exception
from veracity_detection.aggregation import AggregationProcessor



def aggregate(json, type):
    aggregation_processor = AggregationProcessor(json)
    result = aggregation_processor.process(type)
    return result


def predict(claims, identifier):
    """

    :param claims:
    :param identifier:
    :return:
    """
    try:
        # load trained model
        model = torch.load(settings.trained_model)

        # parse the stance scores only and feed to model
        # loads nested json, groups by claim index, and aggregates the stance scores in a list
        df = pd.json_normalize(claims, 'evidences', ['index']).groupby('index')[['index', 'stance_score']]\
            .agg({'index': 'first', 'stance_score': list})
        claim_indices = df.index
        stance_scores = np.vstack(df.stance_score.to_numpy()).astype(np.float32)

        # get and set prediction
        prediction = model.test_model(torch.from_numpy(stance_scores)).squeeze(1)
        for i, _ in enumerate(claim_indices):
            claims[i]['wise_score'] = prediction[i].item()

        # update database
        claims_json = json.dumps(claims)
        update_database(settings.sentences, settings.results_wiseone_column_status, claims_json, identifier)

        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()
    except Exception as e:
        log_exception(e, identifier)


def predict_rnn(json, identifier):
    """

    :param json:
    :param identifier:
    :return:
    """
    try:
        # load trained model
        model = torch.load(settings.rnn_model)

        # parse the stance scores only and feed to model
        df = pd.json_normalize(json['wise_check'])
        scores = df # FIXME
        # get prediction
        prediction = model.test_model(torch.from_numpy(scores)).numpy()

        # update database
        update_database(settings.results_table_name, settings.results_wise_final_column_name,
                        settings.results_wise_final_column_status, prediction, identifier)

        # get label
        veracity_label = ''
        databasemanager.update_step(settings.results_table_name, settings.results_veracity_label,
                                    veracity_label, id)

        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()
    except Exception as e:
        log_exception(e, identifier)