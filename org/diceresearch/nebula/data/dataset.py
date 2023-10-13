import json
import logging
import random
from collections import Counter

import numpy as np
import pandas as pd
import torch
from imblearn.over_sampling import RandomOverSampler, SMOTE
from torch.utils.data import Dataset
from tqdm import tqdm

label_dict = {
    "SUPPORTS": 1,
    "NOT ENOUGH INFO": 0.5,
    "REFUTES": 0
}

# classification
# label_dict = {
#     "SUPPORTS": 2,
#     "NOT ENOUGH INFO": 1,
#     "REFUTES": 0
# }


class StanceDataset(Dataset):
    """
    Dataset for data of the format:
    {
      "label": "SUPPORTS",
      "id": "91253",
      "scores": [
        {
          "elastic_score": 21.167542,
          "stance_score": 0.1355261854357877
        }
      ]
    }
    """

    def __init__(self, **kwargs):
        """
        Constructor
        :param kwargs:
        """
        jsonl = kwargs.get('jsonl')
        self.class_counts = Counter()
        if jsonl is None:
            self.claim_id = kwargs.get('claim_id')
            self.evidence_ids = kwargs.get('evidence_ids')
            self.stance_scores = kwargs.get('stance_scores')
            self.label = kwargs.get('label')
        else:
            self.claim_id = list()
            self.evidence_ids = list()  # TODO we probably need to add this to keep track
            self.stance_scores = list()
            self.label = list()

            # read all data
            X = np.array([item['stance_score'] for element in jsonl for item in element['scores']])
            num_elements = len(jsonl)
            num_scores_per_element = len(jsonl[0]['scores'])
            X = X.reshape(num_elements, num_scores_per_element)

            resample = kwargs.get('resample')
            if resample:
                y = np.array([item['label'] for item in jsonl])
                X_resampled, y_resampled = resample.fit_resample(X, y)
                p_bar = tqdm(enumerate(X_resampled))
            else:
                p_bar = tqdm(enumerate(jsonl))

            for idx, item in p_bar:
                p_bar.set_description("Processing dataset")

                if resample:
                    claim_id = idx
                    label = label_dict[y_resampled[idx]]
                    scores = torch.tensor(item, dtype=torch.float32)
                else:
                    claim_id = int(item['id'])
                    label = label_dict[item['label']]
                    scores_t = item['scores']
                    df = pd.DataFrame(scores_t)
                    scores = torch.tensor(df.stance_score, dtype=torch.float32)

                self.claim_id.append(claim_id)
                self.label.append(label)

                # count class frequency
                self.class_counts.update([label])

                # get top k scores to use as evidence, ignore if done already
                k = kwargs.get('k')
                if k < len(scores):
                    top_k_values, _ = torch.topk(scores, k=k)
                elif k == len(scores):
                    top_k_values = scores
                else:
                    # TODO should we scale down to the scores we have or zero pad the difference?
                    top_k_values = scores
                self.stance_scores.append(top_k_values)



    def __len__(self):
        return len(self.label)

    def __getitem__(self, index):
        # classification
        # sample = {'claim_id': self.claim_id[index],
        #           'scores': np.asarray(self.stance_scores[index], dtype=np.float32),
        #           'labels': np.longlong(self.label[index])}
        # return sample
        # regression
        sample = {'claim_id': torch.tensor(self.claim_id[index], dtype=torch.int),
                  'scores': torch.tensor(self.stance_scores[index], dtype=torch.float32),
                  'labels': torch.tensor(self.label[index], dtype=torch.float32)}
        return sample

# class WiseDataset(Dataset):
#     """
#
#     """
#
#     def __init__(self):
#         pass
#
#     def __getitem__(self, index) -> T_co:
#         pass