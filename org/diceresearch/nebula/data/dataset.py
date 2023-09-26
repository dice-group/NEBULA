from collections import Counter

import pandas as pd
import torch
from torch.utils.data import Dataset
from tqdm import tqdm

label_dict = {
    "SUPPORTS": 1,
    "NOT ENOUGH INFO": 0.5,
    "REFUTES": 0
}


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

            p_bar = tqdm(jsonl)
            for item in p_bar:
                p_bar.set_description("Processing dataset")
                self.claim_id.append(int(item['id']))
                self.label.append(label_dict[item['label']])

                # One hot encode vectors
                # one_hot_encoded = torch.zeros(3, dtype=torch.float32)
                # one_hot_encoded[label_dict[item['label']]] = 1
                # self.label.append(one_hot_encoded)

                # count class frequency
                self.class_counts.update([item['label']])

                # get top k scores to use as evidence, ignore if done already
                scores_t = item['scores']
                df = pd.DataFrame(scores_t)
                scores = torch.tensor(df.stance_score, dtype=torch.float32)
                k = kwargs.get('k')
                if k < len(scores):
                    top_k_values, _ = torch.topk(scores, k=k)
                elif k == len(scores):
                    top_k_values = scores
                else:
                    # TODO should we scale down to the scores we have or zero pad the difference?
                    top_k_values = scores
                self.stance_scores.append(top_k_values)

            # TODO balance the dataset by oversampling the minority classes
            # classes_dist=list(self.class_counts.values())
            # if classes_dist.count(classes_dist[0]) != len(classes_dist):
            #     self.sampler = RandomOverSampler(sampling_strategy='not majority')
            #     self.sampled_indices, _ = self.sampler.fit_resample(self.stance_scores, self.label)

    def __len__(self):
        return len(self.claim_id)

    def __getitem__(self, index):
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