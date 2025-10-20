# umair changes
import json
import logging
import orchestrator
import settings
import nltk
from utils.llm_query import get_llm_instance
from utils.database_utils import log_exception, update_database

nltk.download('punkt')
nltk.download('stopwords')

similarity_array = []

stopwords = nltk.corpus.stopwords.words('english')
CustomListofWordstoExclude = ["'s", 'say', 'says', 'said', 's', "n't"]
stopwords.extend(CustomListofWordstoExclude)



def compute_summary_api_call(evdences, claim):
    stanceDetector = get_llm_instance()
    answer = stanceDetector.get_response_from_api_call(evidences=evdences, claim=claim)
    return answer


def do_query(evdences, claim):

    return compute_summary_api_call(evdences, claim)

import tiktoken
def generate(claims, identifier):
    """
    Calculates the cosine similarity between the evidence texts and the respective claim.
    It also updates the result in the database.

    :param claims:
    :param identifier:
    :return:
    """
    try:
        # choose the encoding your model uses
        enc = tiktoken.get_encoding("cl100k_base")  # replace with your model's encoding
        MAX_MODEL_TOKENS = 31000  # slightly below 32768 to leave room for the claim
        # calculate score per evidence in a claim
        for claim in claims:
            claim_text = claim['text']
            evidences = claim['evidences']
            evidence_texts = []
            # divide remaining tokens across evidences
            max_evidence_tokens = MAX_MODEL_TOKENS // len(evidences)
            for evidence in evidences:
                evidence_text = evidence['evidence_text'].replace("\n"," ")
                # continue if text is empty
                if not evidence_text:
                    logging.warning("Skipping. Evidence not found for claim {}".format(claim_text))
                    continue

                # truncate if too long
                evidence_tokens = enc.encode(evidence_text)
                if len(evidence_tokens) > max_evidence_tokens:
                    evidence_tokens = evidence_tokens[:max_evidence_tokens]
                    evidence_text = enc.decode(evidence_tokens)

                evidence_texts.append(evidence_text)
                # compute score between claim and evidence text
            summaries = do_query(evidence_texts, claim_text)
            i = 0
            for evidence in evidences:
                if i < len(summaries):
                    evidence['summary'] = summaries[i]
                else:
                    evidence['summary'] = ""
                # evidence['summary'] = summaries[i]
                i = i+1

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
