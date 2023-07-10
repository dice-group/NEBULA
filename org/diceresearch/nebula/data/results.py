import json


class Result(object):
    def __init__(self):
        pass

    def get_json(self, is_pretty=False):
        if is_pretty:
            return json.dumps(self.__dict__, default=vars, indent=3)
        else:
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


class Provenance(object):
    """

    """
    def __init__(self, check_timestamp, knowledge_date, model_date):
        self.check_timestamp = check_timestamp
        self.knowledge_date = knowledge_date
        self.model_date = model_date


class ResponseStatus(Result):
    """

    """
    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            self.__dict__[key] = value


class Status(Result):
    """

    """

    def __init__(self, id, status, text, lang, veracity_label, veracity_score, explanation, provenance: Provenance):
        super().__init__()
        self.id = id
        self.status = status
        self.lang = lang
        self.text = text
        self.veracity_label = veracity_label
        self.veracity_score = veracity_score
        self.explanation = explanation
        self.provenance = provenance


