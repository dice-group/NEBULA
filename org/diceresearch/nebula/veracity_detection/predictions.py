import threading

import numpy as np
import pandas as pd
import torch

import settings, orchestrator, databasemanager
from veracity_detection.aggregation import AggregationProcessor

from org.diceresearch.nebula.exception_handling.exception_utils import log_exception


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
    try:
        # load trained model
        model = torch.load(settings.trained_model)

        # parse the stance scores only and feed to model
        df = pd.json_normalize(json['stances'])

        # FIXME this shouldn't be needed, it's already always 10. If it isn't, there's a problem
        df2 = df.groupby(['claim']).apply(lambda x: x.nlargest(10, ['stance_score'])).reset_index(drop=True)
        st_sc = df2.groupby(['claim'])[['stance_score']].agg({"stance_score": list})
        scores = np.array([np.array(score[0], dtype=np.float32) for score in st_sc.values])

        # get prediction
        prediction = model.test_model(torch.from_numpy(scores)).numpy()

        st_sc['wise_score'] = prediction

        # update database
        databasemanager.update_step(settings.results_table_name, settings.results_wiseone_column_name,
                                    st_sc.to_json(orient='index'), identifier)
        databasemanager.update_step(settings.results_table_name, settings.results_wiseone_column_status, settings.completed,
                                    identifier)
        databasemanager.increase_the_stage(settings.results_table_name, identifier)

        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()
    except Exception as e:
        log_exception(e, identifier)