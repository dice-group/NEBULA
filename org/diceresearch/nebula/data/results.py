import json

"""
    This file contains all the result formats the service outputs.
"""


class Result(object):
    """
        JSON serializable result
    """

    def get_json(self, is_pretty=False, in_array=False):
        ob = self.__dict__
        if in_array:
            ob = [self.__dict__]
        if is_pretty:
            return json.dumps(ob, default=vars, indent=3)
        else:
            return json.dumps(ob, default=vars)


class ClaimCheckResult(Result):
    """
        Claim check result format
    """

    def __init__(self, version: str, text: str, sentences: list):
        super().__init__()
        self.version = version
        self.sentences = text
        self.results = sentences



class Sentence(Result):
    """
        Sentence with corresponding index in the overall text
    """
    def __init__(self, text: str, index: int, score: float):
        self.text = text
        self.index = index
        self.score = score


class QueryResult(object):
    """
        Query result format
    """
    def __init__(self, result: str, query: str):
        self.result = result
        self.query = query


class EvidenceRetrievalResult(Result):
    """
        Evidence retrieval result format
    """
    def __init__(self, evidences=None):
        if evidences:
            self.evidences=evidences
        else:
            self.evidences = list()

    def add(self, query_result: QueryResult):
        self.evidences.append(query_result)


class Stance(object):
    """
        Single stance result format
    """
    def __init__(self, claim: str, text: str, url: str, elastic_score: float, stance_score: float):
        self.claim = claim
        self.text = text
        self.url = url
        self.elastic_score = elastic_score
        self.stance_score = stance_score


class StanceDetectionResult(Result):
    """
        Stance detection result format
    """
    def __init__(self, stances=None):
        if stances:
            self.stances=stances
        else:
            self.stances = list()

    def add_stance(self, stance: Stance):
        self.stances.append(stance)

    def add(self, claim: str, text: str, url: str, elastic_score: float, stance_score: float):
        self.stances.append(Stance(claim, text, url, elastic_score, stance_score))


class Provenance(object):
    """
        Provenance information
    """
    def __init__(self, check_timestamp, knowledge_date, model_date):
        self.check_timestamp = check_timestamp
        self.knowledge_date = knowledge_date
        self.model_date = model_date


class ResponseStatus(Result):
    """
        Dynamic status response. It expects only keyword arguments.
        ResponseStatus(status="Error") will produce a ResponseStatus object with an attribute status with
        the value "error", which in turn would produce a JSON of the form: {"status": "Error"}
    """
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            self.__dict__[key] = value


class Status(Result):
    """
        Response status for the /status query
    """

    def __init__(self, id, status, text, lang, veracity_label, veracity_score, explanation, provenance: Provenance):
        self.id = id
        self.status = status
        self.lang = lang
        self.text = text
        self.veracity_label = veracity_label
        self.veracity_score = veracity_score
        self.explanation = explanation
        self.provenance = provenance