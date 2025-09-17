# umair changes
import json
import logging
import orchestrator
import settings
import nltk
from utils.llm_query import LLMQueryClass
from utils.database_utils import log_exception, update_database

nltk.download('punkt')
nltk.download('stopwords')

similarity_array = []

stopwords = nltk.corpus.stopwords.words('english')
CustomListofWordstoExclude = ["'s", 'say', 'says', 'said', 's', "n't"]
stopwords.extend(CustomListofWordstoExclude)



def caompute_summary_api_call(maintext, claim):
    stanceDetector = LLMQueryClass()
    answer = stanceDetector.get_response_from_api_call(text=maintext, claim=claim)
    return answer


def do_query(maintext, claim):

    return caompute_summary_api_call(maintext, claim)


def generate(claims, identifier):
    """
    Calculates the cosine similarity between the evidence texts and the respective claim.
    It also updates the result in the database.

    :param claims:
    :param identifier:
    :return:
    """
    try:
        # calculate score per evidence in a claim
        for claim in claims:
            claim_text = claim['text']
            evidences = claim['evidences']
            for evidence in evidences:
                evidence_text = evidence['evidence_text']

                # continue if text is empty
                if not evidence_text:
                    logging.warning("Skipping. Evidence not found for claim {}".format(claim_text))
                    continue

                # compute score between claim and evidence text
                summary = do_query(evidence_text, claim_text)
                evidence['summary'] = summary

        # parse to json
        claims_json = json.dumps(claims)

        # update database
        update_database(settings.sentences, settings.results_summary_column_status, claims_json, identifier)

        # go next level
        orchestrator.goNextLevel(identifier)
    except Exception as e:
        log_exception(e, identifier)

# end here

#
# def detect(main_text, claim, identifier):
#     result = do_query(main_text, claim)
#     if result is None:
#         logging.error("Error in retrieving the evidences")
#     else:
#         # save the result in database
#         update_database(settings.results_stancedetection_column_name,
#                         settings.results_stancedetection_column_status, result, identifier)
#
#         # go next level
#         thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
#         thread.start()
