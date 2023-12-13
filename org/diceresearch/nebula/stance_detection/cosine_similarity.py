import json
import logging
import threading

import orchestrator
import settings
import nltk

from utils.database_utils import log_exception, update_database

nltk.download('punkt')
nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize


similarity_array = []

stopwords = nltk.corpus.stopwords.words('english')
CustomListofWordstoExclude = ["'s", 'say', 'says', 'said', 's', "n't"]
stopwords.extend(CustomListofWordstoExclude)


def calculate_score(maintext, claim):
    data_text = maintext
    data_title = claim
    X_list = word_tokenize(str(data_title))
    Y_list = word_tokenize(str(data_text))
    # print(X_list.size)
    sw = stopwords
    l1 = []
    l2 = []
    X_set = {w for w in X_list if not w in sw}
    Y_set = {w for w in Y_list if not w in sw}
    # print(len(X_set))
    # print("############")
    # print(len(Y_set))
    rvector = X_set.union(Y_set)

    # print("rvector size")
    # print(len(rvector))
    for w in rvector:
        if w in X_set:
            l1.append(1)  # create a vector
        else:
            l1.append(0)
        if w in Y_set:
            l2.append(1)
        else:
            l2.append(0)
    c = 0

    # cosine formula
    for i in range(len(rvector)):
        c += l1[i] * l2[i]
    try:
        cosine = c / float((sum(l1) * sum(l2)) ** 0.5)
    except ZeroDivisionError:
        cosine = 0
    # print("similarity: ", cosine)
    return str(cosine)


def do_query(maintext, claim):
    # Define the endpoint (url), payload (sentence to be scored), api-key (api-key is sent as an extra header)
    # api_endpoint = settings.stancedetection_api

    # Send the POST request to the API and store the api response
    # api_response = httpmanager.sendget(api_endpoint, f"""{maintext}/{claim}""")

    # Print out the JSON payload the API sent back

    return calculate_score(maintext, claim)


def detect(main_text, claim, identifier):
    result = do_query(main_text, claim)
    if result is None:
        logging.error("Error in retrieving the evidences")
    else:
        # save the result in database
        update_database(settings.results_stancedetection_column_name,
                        settings.results_stancedetection_column_status, result, identifier)

        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()


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
            for evidence in evidences:
                evidence_text = evidence['evidence_text']

                # continue if text is empty
                if not evidence_text:
                    logging.warning("Skipping. Evidence not found for claim {}".format(claim_text))
                    continue

                # compute score between claim and evidence text
                stance_score = do_query(evidence_text, claim_text)
                evidence['stance_score'] = stance_score

        # parse to json
        claims_json = json.dumps(claims)

        # update database
        update_database(settings.sentences, settings.results_stancedetection_column_status, claims_json, identifier)

        # go next level
        orchestrator.goNextLevel(identifier)
    except Exception as e:
        log_exception(e, identifier)