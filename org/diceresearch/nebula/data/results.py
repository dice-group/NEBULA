import json


class Result(object):
    def __init__(self):
        pass

    def get_json(self):
        return json.dumps(self.__dict__, default=vars)


class ClaimCheckResult(Result):
    """

    """

    def __init__(self, version: str, text: str, sentences: list):
        super().__init__()
        self.version = version
        self.sentences = text
        self.results = sentences


class Sentence(object):
    def __init__(self, text: str, index: int, score: float):
        self.text = text
        self.index = index
        self.score = score


class QueryResult(object):
    def __init__(self, result: str, query: str):
        self.result = result
        self.query = query


class EvidenceRetrievalResult(Result):
    def __init__(self):
        super().__init__()
        self.evidences = list()

    def add(self, query_result: QueryResult):
        self.evidences.append(query_result)


class Stance(object):
    def __init__(self, claim: str, text: str, url: str, elastic_score: float, stance_score: float):
        self.claim = claim
        self.text = text
        self.url = url
        self.elastic_score = elastic_score
        self.stance_score = stance_score


class StanceDetectionResult(Result):
    def __init__(self):
        super().__init__()
        self.stances = list()

    def add_stance(self, stance: Stance):
        self.stances.append(stance)

    def add(self, claim: str, text: str, url: str, elastic_score: float, stance_score: float):
        self.stances.append(Stance(claim, text, url, elastic_score, stance_score))

# TODO move this to unit test cases
# k = ClaimCheckResult("dummy","Some text", [Sentence("Random text", 0, 1)])
# print(k.get_json())