import pandas as pd
import torch
from org.diceresearch.nebula import settings


def predict(json):
    """

    :param json:
    :param path:
    :return:
    """

    # load trained model
    model = torch.load(settings.trained_model)

    # parse the stance scores only and feed to model
    df = pd.DataFrame(json)
    scores = torch.tensor(df.stance_score, dtype=torch.float32)
    return model.test_model(scores)