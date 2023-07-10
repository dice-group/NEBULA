import json


class Result(object):
    def __init__(self):
        pass

    def get_json(self):
        return json.dumps(self.__dict__, default=vars)


class ClaimCheckResult(Result):
    """

    """

    def __init__(self, version, text, sentences: list):
        super().__init__()
        self.version = version
        self.sentences = text
        self.results = sentences


class Sentence(object):
    def __init__(self, text, index, score):
        self.text = text
        self.index = index
        self.score = score


class QueryResult(object):
    def __init__(self, result, query):
        self.result = result
        self.query = query


class EvidenceRetrievalResult(Result):
    def __init__(self):
        super().__init__()
        self.evidences = list()

    def add(self, query_result: QueryResult):
        self.evidences.append(query_result)



class StanceDetectionResult(Result):
    def __init__(self):
        super().__init__()

# TODO move this to unit test cases
# k = ClaimCheckResult("dummy","Some text", [Sentence("Random text", 0, 1)])
# print(k.get_json())