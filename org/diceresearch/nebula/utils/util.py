import json
import logging
from itertools import product

from sklearn.metrics import f1_score
from tqdm import tqdm

"""
    Use this file to implement static util methods
"""


def trim(text):
    return text.replace("\"", "").replace("\'", "")


def get_optimal_thresholds(thresholds_range, classes, scores, true_labels):
    """
    Gets optimal thresholds to convert continuous scores into 3 discrete classes based on the macro F1 score
    :param thresholds_range:
    :param classes:
    :param scores:
    :param true_labels:
    :return:
    """
    logging.info('Finding best thresholds')
    best_thresholds = None
    best_f1 = -1
    for threshold1, threshold2 in tqdm(product(thresholds_range, repeat=2)):
        if threshold1 < threshold2:
            translated_labels = [translate_to_classes(score, threshold1, threshold2, classes) for score in scores]

            f1 = f1_score(true_labels, translated_labels, average='macro')
            if f1 > best_f1:
                best_f1 = f1
                best_thresholds = (threshold1, threshold2)
                logging.debug('Current best macro F1-score {0} with thresholds {1}'.format(best_f1, best_thresholds))
    return best_thresholds


def translate_to_classes(score, threshold_low, threshold_high, classes):
    """
    Translates to 3 different classes, by considering 2 different thresholds.
    :param classes: Assumes three classes in ascending order
    :param score: Score to be translated
    :param threshold_low: Lower threshold
    :param threshold_high: Higher threshold
    :return: String with the class designation
    """
    if score < threshold_low:
        return classes[0]
    elif score < threshold_high:
        return classes[1]
    else:
        return classes[2]


def read_jsonl_from_file(file):
    """
    Reads a JSONL from file
    :param file: path
    :return: list of JSON objects
    """
    with open(file, 'r') as json_file:
        return [json.loads(line) for line in json_file]


def get_highest_index(arr):
    """
        Retrieves index of the highest number in an array
    :param arr: array
    :return:
    """
    max_value, max_index = max((val, idx) for idx, val in enumerate(arr))
    return max_index


class Tape:
    """

    """
    def __init__(self, r):
        self.r = r
        self.current = 0

    def length(self):
        return len(self.r)

    def inc_and_get(self):
        self.current += 1
        if self.current > self.length()-1:
            self.current =- self.length()
        return self.r[self.current]

    def get_and_inc(self):
        if self.current > self.length()-1:
            self.current =- self.length()
        result = self.r[self.current]
        self.current += 1
        return result

    def get(self, i):
        return self.r[i]