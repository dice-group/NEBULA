import json

"""
    This file contains all the result formats the service components output.
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
    def __init__(self, check_timestamp, knowledge_date, model_date):
        """
        Constructor.
        :param check_timestamp: Start timestamp of the request
        :param knowledge_date: Knowledge base last modified date
        :param model_date: WISE models last trained date
        """
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


class RawStatus:
    """

    """
    def __init__(self, input_text, lang, translated_text, coref_text, request_status,
                 translation_status, coref_status, claim_check_status, evidence_retrieval_status,
                 stance_detection_status, wise_one_status, wise_two_status,
                 sentences, wise_score, veracity_label):
        self.input_text = input_text
        self.lang = lang
        self.translated_text = translated_text
        self.coref_text = coref_text
        self.request_status = request_status
        self.translation_status = translation_status
        self.coref_status = coref_status
        self.claim_check_status = claim_check_status
        self.evidence_retrieval_status = evidence_retrieval_status
        self.stance_detection_status = stance_detection_status
        self.wise_one_status = wise_one_status
        self.wise_two_status = wise_two_status
        self.sentences = [Sentence(**s) for s in sentences]
        self.wise_score = wise_score
        self.veracity_label = veracity_label
#  my_object = RawStatus(**data)  transforms a json into the object

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