import numpy as np
from torch.utils.data import Dataset
from torch.utils.data.dataset import T_co


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

            label_dict = {
                "SUPPORTS": 1.0,
                "NOT ENOUGH INFO": 0.5,
                "REFUTES": 0.0

            }

            for item in jsonl:
                self.claim_id.append(item['id'])
                self.label.append(label_dict[item['label']])
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


class WiseDataset(Dataset):
    """

    """

    def __init__(self):
        pass

    def __getitem__(self, index) -> T_co:
        pass