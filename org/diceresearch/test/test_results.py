import unittest
from logging.config import fileConfig

fileConfig('test_logging.ini')

class Test(unittest.TestCase):
    """

    """

    def test_json(self):
        # TODO move this to unit test cases
        # k = ClaimCheckResult("dummy","Some text", [Sentence("Random text", 0, 1)])
        # print(k.get_json())
        pass