import threading

import pandas as pd
import torch
from org.diceresearch.nebula import settings, orchestrator


def predict(json, identifier):
    """

    :param json:
    :param path:
    :return:
    """

    # load trained model
    model = torch.load(settings.trained_model)

    # parse the stance scores only and feed to model
    df = pd.json_normalize(json['stances'])
    scores = torch.tensor(df.stance_score, dtype=torch.float32)

    predictions = model.test_model(scores.unsqueeze(0))

    # go next level
    thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
    thread.start()

    return predictions