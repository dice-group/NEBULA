import json
import unittest
from logging.config import fileConfig

from parameterized import parameterized

from org.diceresearch.nebula.data.results import ClaimCheckResult, Sentence, ResponseStatus, StanceDetectionResult, \
    Stance, EvidenceRetrievalResult, QueryResult

fileConfig('test_logging.ini')

# Define parameters
param_list = list()
k = ClaimCheckResult("dummy", "Some text", [Sentence("Random text", 0, 1)])
er_result = EvidenceRetrievalResult([QueryResult("A query result", "Query 1"), QueryResult("Another query result", "Query 2")])
sd_result = StanceDetectionResult([Stance("Claim", "Evidence", "URL", 0.8, 0.7)])
r1 = ResponseStatus(id=5, message="This is a test message")
r2 = ResponseStatus(status="Error")

param_list.append((k, '{"version": "dummy", "sentences": "Some text", "results": [{"text": "Random text", "index": 0, "score": 1}]}'))
param_list.append((er_result, '{"evidences": [{"result": "A query result", "query": "Query 1"}, {"result": "Another query result", "query": "Query 2"}]}'))
param_list.append((sd_result, '{"stances": [{"claim": "Claim", "text": "Evidence", "url": "URL", "elastic_score": 0.8, "stance_score": 0.7}]}'))
param_list.append((r1, '{"id": 5, "message": "This is a test message"}'))
param_list.append((r2, '{"status": "Error"}'))


class Test(unittest.TestCase):
    """
        Checks if the result objects we create, produce a valid JSON string
    """

    @parameterized.expand(param_list)
    def test_json(self, k, expected):
        actual = k.get_json()
        # check if valid
        json.loads(actual)
        # check if it matches
        self.assertEqual(actual, expected)