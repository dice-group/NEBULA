# umair changes
import json
import logging
import threading
import orchestrator
import settings
import nltk
from utils.database_utils import log_exception, update_database
from utils.util import translate_to_classes
from database import databasemanager
from utils.llm_query import LLMQueryClass
nltk.download('punkt')
nltk.download('stopwords')
import re

similarity_array = []

stopwords = nltk.corpus.stopwords.words('english')
CustomListofWordstoExclude = ["'s", 'say', 'says', 'said', 's', "n't"]
stopwords.extend(CustomListofWordstoExclude)



def calculate_score_using_api_call(maintext, claim):
    stanceDetector = LLMQueryClass()
    answer = stanceDetector.get_response_from_api_call(summaries=maintext, claim=claim)
    answer = answer.replace("\n", " ")
    score = 0
    if "false" in answer.lower() or "Answer: REFUTES" in answer or ("no evidence that supports the claim".lower() in answer.lower() or ("REFUTE".lower() in answer.lower() and "SUPPORT".lower() not in answer.lower())):
        score = -1
    elif "true" in answer.lower() or "Answer: SUPPORTS" in answer or ("SUPPORT".lower() in answer.lower() and "REFUTE".lower() not in answer.lower()):
        score = 1
    elif "NOT ENOUGH INFO".lower() in answer.lower():
        score = 0
    else:
        score = 0
    logging.info("LLM based Detection Results:"+str(score))
    return str(score)

  
# def do_query(maintext, claim):
#     return calculate_score_using_api_call(maintext, claim)



def calculate(claims, identifier):
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
            list_summaries = []
            for evidence in evidences:
                evidence_text = evidence['summary']
                list_summaries.append(evidence_text)
                # continue if text is empty
                if not evidence_text:
                    logging.warning("Skipping. Evidence not found for claim {}".format(claim_text))
                    continue

            # compute score between claim and evidence text
            # stance_score = do_query(list_summaries, claim_text)
            stanceDetector = LLMQueryClass()
            stance_score = stanceDetector.get_single_claim_classification_response_from_api_call(summaries=list_summaries, claim=claim_text)
            claim['final_llm_classification_score'] = stance_score

        # parse to json
        claims_json = json.dumps(claims)

        # update database
        update_database(settings.sentences, settings.results_stancedetection_column_status, claims_json, identifier)

        # go next level
        orchestrator.goNextLevel(identifier)
    except Exception as e:
        log_exception(e, identifier)



def extract_label(text: str) -> str:
    """
    Extract only the final label (RELIABLE, UNRELIABLE, MIXED)
    from LLM output text.
    """
    # Normalize
    text = text.strip().upper()

    # Look for exact label tokens
    match = re.search(r"\b(RELIABLE|UNRELIABLE|MIXED)\b", text)
    if match:
        return match.group(1)

    # Default fallback if nothing found
    return "UNKNOWN"

def calculate_final_decision(claims, orignal_doc, identifier):
    """
    Calculates the cosine similarity between the evidence texts and the respective claim.
    It also updates the result in the database.

    :param claims:
    :param identifier:
    :return:
    """
    try:
        # calculate score per evidence in a claim
        list_claim_decisions = dict()
        for claim in claims:
            claim_text = claim['text']
            decisions = claim['final_llm_classification_score']
            list_claim_decisions[claim_text] = decisions
        # compute score between claim and list of decisions

        stanceDetector = LLMQueryClass()
        answer = stanceDetector.get_article_verdict(claim_verdicts=list_claim_decisions, article_text=orignal_doc)
        answer = answer.replace("\n", " ")
        answer = extract_label(answer)

        # claim['final_llm_classification_score'] = answer

        # parse to json
        claims_json = json.dumps(claims)

        # update database
        update_database(settings.sentences, settings.results_stancedetection_column_status, claims_json, identifier)

        # veracity_label = translate_to_classes(prediction, settings.low_threshold, settings.high_threshold,
        #                                               settings.final_class_labels)

        databasemanager.update_step(settings.results_table_name, settings.results_veracity_label,
                                            answer, identifier)

        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()
        # go next level
        # orchestrator.goNextLevel(identifier)
    except Exception as e:
        log_exception(e, identifier)





















#
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


#
# def predict_mean(json, identifier):
#     try:
#         # parse the stance scores only and feed to model
#         scores = pd.json_normalize(json)['wise_score'].to_numpy(dtype=np.float32)
#         prediction = aggregate(scores, 'mean')
#
#
#         # update database
#         update_database(settings.results_wise_final_column_name, settings.results_wise_final_column_status,
#                         str(prediction), identifier)
#
#         # translate score to label and save it
#         veracity_label = translate_to_classes(prediction, settings.low_threshold, settings.high_threshold,
#                                               settings.final_class_labels)
#         databasemanager.update_step(settings.results_table_name, settings.results_veracity_label,
#                                     veracity_label, identifier)
#
#         # go next level
#         thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
#         thread.start()
#     except Exception as e:
#         log_exception(e, identifier)
# end here



    # def calculate(claims, identifier):
    #     """
    #     Calculates the cosine similarity between the evidence texts and the respective claim.
    #     It also updates the result in the database.
    #
    #     :param claims:
    #     :param identifier:
    #     :return:
    #     """
    #     try:
    #         # calculate score per evidence in a claim
    #         for claim in claims:
    #             claim_text = claim['text']
    #             evidences = claim['evidences']
    #             list_summaries = []
    #             for evidence in evidences:
    #                 evidence_text = evidence['summary']
    #                 list_summaries.append(evidence_text)
    #                 # continue if text is empty
    #                 if not evidence_text:
    #                     logging.warning("Skipping. Evidence not found for claim {}".format(claim_text))
    #                     continue
    #
    #             # compute score between claim and evidence text
    #             stance_score = do_query(list_summaries, claim_text)
    #             claim['final_llm_classification_score'] = stance_score
    #
    #         # parse to json
    #         claims_json = json.dumps(claims)
    #
    #         # update database
    #         update_database(settings.summaries, settings.results_stancedetection_column_status, claims_json, identifier)
    #
    #         # go next level
    #         orchestrator.goNextLevel(identifier)
    #     except Exception as e:
    #         log_exception(e, identifier)


