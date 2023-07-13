import json
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd


class NumberAggregator(ABC):
    """
    Abstract class for number aggregation
    """
    @abstractmethod
    def aggregate(self, data):
        pass


class MeanAggregator(NumberAggregator):
    """
    Average implementation
    """
    def aggregate(self, data):
        return np.mean(data)


class SumAggregator(NumberAggregator):
    """
    Sum implementation
    """
    def aggregate(self, data):
        return np.sum(data)


class NumberAggregatorFactory:
    @staticmethod
    def create_aggregator(implementation):
        if implementation == 'mean':
            return MeanAggregator()
        elif implementation == 'sum':
            return SumAggregator()
        else:
            raise ValueError('Invalid aggregator implementation')


class AggregationProcessor:
    """

    """
    def __init__(self, json_data):
        df = pd.read_json(json_data, orient='index')['wise_score']
        self.data = df.values

    def process(self, implementation):
        aggregator = NumberAggregatorFactory.create_aggregator(implementation)
        result = aggregator.aggregate(self.data)
        return result