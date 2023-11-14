import json
import logging
import random
from collections import Counter

import numpy as np
import pandas as pd
import torch
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import Dataset
from tqdm import tqdm


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
        Constructor.
        :param kwargs: Keyword arguments. Either accepts a jsonl file of the format above with the keyword argument
        jsonl and parses the data or takes the data directly with the keyword arguments claim_id, stance_scores, label
        """
        jsonl = kwargs.get('jsonl')
        self.label_dict = kwargs.get('label_dict')
        self.class_counts = Counter()
        if jsonl is None:
            self.claim_id = kwargs.get('claim_id')
            self.stance_scores = kwargs.get('stance_scores')
            self.label = kwargs.get('label')
        else:
            self.claim_id = list()
            self.stance_scores = list()
            self.label = list()


            resample = kwargs.get('resample')
            if resample:
                X = np.array([item['stance_score'] for element in jsonl for item in element['scores']])
                num_elements = len(jsonl)
                num_scores_per_element = len(jsonl[0]['scores'])
                X = X.reshape(num_elements, num_scores_per_element)

                y = np.array([item['label'] for item in jsonl])
                X_resampled, y_resampled = resample.fit_resample(X, y)
                p_bar = tqdm(enumerate(X_resampled))
            else:
                p_bar = tqdm(enumerate(jsonl))

            for idx, item in p_bar:
                p_bar.set_description("Processing dataset")

                if resample:
                    claim_id = idx
                    label = self.label_dict[y_resampled[idx]]
                    scores = torch.tensor(item, dtype=torch.float32)
                else:
                    claim_id = int(item['id'])
                    label = self.label_dict[item['label']]
                    scores_t = item['scores']
                    df = pd.DataFrame(scores_t)
                    scores = torch.tensor(df.stance_score, dtype=torch.float32)

                self.claim_id.append(claim_id)
                self.label.append(label)

                # count class frequency
                self.class_counts.update([label])

                # 0-pad if needed
                k = kwargs.get('k')
                padding_length = k - len(scores)
                if padding_length > 0:
                    scores = np.pad(scores, (padding_length, 0), mode='constant', constant_values=0)
                elif padding_length < 0:
                    top_k = df.nlargest(k, 'elastic_score')
                    scores = torch.tensor(top_k.get('stance_score').values, dtype=torch.float32)
                self.stance_scores.append(scores)
        logging.info(f"Class frequency counts: {self.class_counts}")

    def __len__(self):
        return len(self.label)

    def __getitem__(self, index):
        scores = torch.tensor(self.stance_scores[index], dtype=torch.float32)
        labels = torch.tensor(self.label[index], dtype=torch.float32)
        return scores, labels


class WiseDataset(Dataset):
    """
    Dataset for data of the format
    {
        "article_id": "article_id",
        "endpoint": "http://example-endpoint.org",
        "article_text": "Article text we need to check 1. Article text we need to check 1.",
        "label": 1,
        "nebula_id": "ID",
        "wise_check": {
            "Article text we need to check 1.": {
                "stance_score": [0.12, 0.07, 0.06, 0.07, 0.06, 0.06, 0.05, 0.04, 0.03, 0.01],
                "wise_score": 0.6200786829
            },
            "Article text we need to check 1.": {
                "stance_score": [0.12, 0.09, 0.08, 0.08, 0.08, 0.08, 0.07, 0.07, 0.06, 0.06],
                "wise_score": 0.6385794878
            }
        }
    }
    """

    def __init__(self, **kwargs):
        """
        Constructor.
        :param kwargs: Keyword arguments. Either accepts a jsonl file of the format above with the keyword argument
        jsonl and parses the data or takes the data directly with the keyword arguments claim_id, stance_scores, label
        """
        jsonl = kwargs.get('jsonl')
        self.label_dict = kwargs.get('label_dict')
        self.class_counts = Counter()
        if jsonl is None:
            self.art_id = kwargs.get('art_id')
            self.wise_score = kwargs.get('wise_score')
            self.label = kwargs.get('label')
        else:
            self.art_id = list()
            self.label = list()
            self.wise_score = list()

            # parse all data
            p_bar = tqdm(jsonl)
            for element in p_bar:
                p_bar.set_description("Processing dataset")
                claims = list()
                art_id = element['article_id']
                label = self.label_dict[element['label']]
                self.art_id.append(art_id)
                self.label.append(label)
                # count class frequency
                self.class_counts.update([label])
                for item in element['wise_check']:
                    c_wise_score = element['wise_check'][item]['wise_score']
                    claims.append(c_wise_score)
                self.wise_score.append(claims)

    def __len__(self):
        return len(self.label)

    def __getitem__(self, index):
        scores = torch.tensor(self.wise_score[index], dtype=torch.float32)
        labels = torch.tensor(self.label[index], dtype=torch.float32)
        return scores, labels


def zero_pad_batch(batch):
    # Extract tensors
    sequences, labels = zip(*[(item[0], item[1]) for item in batch])
    # Pad sequences to the maximum length in the batch
    padded_sequences = pad_sequence(sequences, batch_first=True, padding_value=0)
    # Stack labels
    stacked_labels = torch.stack(labels)
    return padded_sequences, stacked_labels