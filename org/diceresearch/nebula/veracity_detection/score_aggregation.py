from abc import ABC, abstractmethod

import numpy as np


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
    """
    Factory of aggregator objects
    """
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
    Computes the aggregation based on the implementation type desired
    """
    def __init__(self, implementation):
        self.aggregator = NumberAggregatorFactory.create_aggregator(implementation)

    def process(self, data):
        return self.aggregator.aggregate(data)