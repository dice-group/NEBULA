import numpy as np
from torch.utils.data import Dataset
from torch.utils.data.dataset import T_co


class StanceDataset(Dataset):
    """

    """

    def __init__(self, jsonl, k):
        """
        Constructor
        :param jsonl:   List with json objects
        :param k:       Top k evidence we want to use to train
        """
        self.claim_id = list()
        self.evidence_ids = list()  # TODO do we need to add this
        self.stance_scores = list()
        self.label = list()

        label_dict = {
            "SUPPORTS": 1.0,
            "REFUTES": -1.0,
            "NOT ENOUGH INFO": 0.0
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
        return np.asarray(self.stance_scores[index], dtype=np.float32), np.float32(self.label[index])


class WiseDataset(Dataset):
    """

    """

    def __init__(self):
        pass

    def __getitem__(self, index) -> T_co:
        pass