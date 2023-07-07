from collections import Counter

import numpy as np
import torch
from imblearn.over_sampling import RandomOverSampler
from torch.utils.data import Dataset

label_dict = {
    "SUPPORTS": 2,
    "NOT ENOUGH INFO": 1,
    "REFUTES": 0
}

class_counts = Counter()


class MultiOverSamplingSampler:
    def __init__(self, dataset):
        self.dataset = dataset
        self.over_sampler = RandomOverSampler(sampling_strategy='not majority')

    def __iter__(self):
        # Perform oversampling on the underrepresented classes
        over_sampled, _ = self.over_sampler.fit_resample(
            X=self.dataset.stance_scores, y=self.dataset.label
        )
        return iter(over_sampled)

    def __len__(self):
        return len(self.dataset)


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

            for item in jsonl:
                self.claim_id.append(item['id'])
                # self.label.append(label_dict[item['label']])
                one_hot_encoded = torch.zeros(3, dtype=torch.float32)
                one_hot_encoded[label_dict[item['label']]] = 1
                class_counts.update([str(one_hot_encoded)])
                self.label.append(one_hot_encoded)
                scores = item['scores']
                l_scores = list()
                # TODO add limit of k scores, zero pad the ones less than k
                for score in scores:
                    l_scores.append(score['stance_score'])
                self.stance_scores.append(l_scores)

    def __len__(self):
        return len(self.claim_id)

    def __getitem__(self, index):
        sample = {'claim_id': self.claim_id[index],
                  'scores': np.asarray(self.stance_scores[index], dtype=np.float32),
                  'labels': np.float32(self.label[index])}
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
