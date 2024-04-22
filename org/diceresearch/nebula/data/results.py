import json

"""
    This file contains the result formats the service components output.
"""


class Evidence:
    """
    Evidence as retrieved by the evidence retrieval and the stance detection modules.

    Example:
    {
        "text": "This is an evidence for claim 0.",
        "url": "www.evidenceclaim0.com",
        "elastic_score": 0.2,
        "stance_score": 1
    }

    """
    def __init__(self, evidence_text, url, elastic_score, stance_score=None):
        """
        Constructor.
        :param evidence_text: Evidence text. Provided by the ER module.
        :param url: Evidence URL. Provided by the ER module.
        :param elastic_score: Elastic Search score. Provided by the ER module.
        :param stance_score: Stance score Provided by the SD module.
        """
        self.evidence_text = evidence_text
        self.url = url
        self.elastic_score = elastic_score
        self.stance_score = stance_score


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


class Sentence(Result):
    """
        Sentences with claim index, claim text, score and found evidences.

        Example:
        {
            "index": 0,
            "text": "This is an example.",
            "score": 0,
            "wise_score": 1,
            "evidences": [
				{
                    "text": "This is an evidence for claim 0.",
                    "url": "www.evidenceclaim0.com",
                    "elastic_score": 0.2,
                    "stance_score": 1
                }
            ]
        }
    """
    def __init__(self, index: int, text: str, score: float, wise_score=None, evidences=None):
        """
        Constructor.
        :param index: Claim index. Provided by the CC module.
        :param text: Claim text. Provided by the CC module.
        :param score: Claim score. Provided by the CC module.
        :param wise_score: Wise score. Provided by the first module of WISE.
        :param evidences: Evidences. Provided by the ER, SD and VD modules.
        """
        self.index = index
        self.text = text
        self.score = score
        self.wise_score = wise_score
        self.evidences = evidences


class Provenance(object):
    """
        Provenance information
    """
    def __init__(self, knowledge_date, model_date, final_model_date):
        """
        Constructor.
        :param knowledge_date: Knowledge base last modified date
        :param model_date: WISE's first step model last trained date
        :param final_model_date: WISE final step model last trained date
        """
        self.knowledge_date = knowledge_date
        self.model_date = model_date
        self.final_model_date = final_model_date


class ResponseStatus(Result):
    """
        Dynamic status response. It expects only keyword arguments.
        ResponseStatus(status="Error") will produce a ResponseStatus object with an attribute status with
        the value "error", which in turn would produce a JSON of the form: {"status": "Error"}
    """
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            self.__dict__[key] = value
