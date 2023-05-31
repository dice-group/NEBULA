import threading

import databasemanager
import httpmanager
import orchestrator
import settings
import nltk
import json
nltk.download('punkt')
nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

similarity_array = []

stopwords = nltk.corpus.stopwords.words('english')
CustomListofWordstoExclude = ["'s",'say','says','said','s',"n't"]
stopwords.extend(CustomListofWordstoExclude)

def calculatescore(maintext,claim):
    data_text = maintext
    data_title = claim
    X_list = word_tokenize(str(data_title))
    Y_list = word_tokenize(str(data_text))
    # print(X_list.size)
    sw = stopwords
    l1 = [];
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
    #print("similarity: ", cosine)
    return str(cosine)

def doQuery(maintext, claim):
    # Define the endpoint (url), payload (sentence to be scored), api-key (api-key is sent as an extra header)
    #api_endpoint = settings.stancedetection_api

    # Send the POST request to the API and store the api response
    #api_response = httpmanager.sendget(api_endpoint, f"""{maintext}/{claim}""")

    # Print out the JSON payload the API sent back


    return calculatescore(maintext, claim)


def detect(main_text, claim, identifier):
    result = doQuery(main_text, claim)
    if result is None:
        print("error in retrieving the evidences")
    else:
        # save the result in database
        databasemanager.update_step(settings.results_table_name, settings.results_stancedetection_column_name, result,
                                    identifier)

        # go next level
        thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
        thread.start()

def generate_result_tosave(all_results):
    result =  "{\"stances\":["
    counter = 0
    for r in all_results:
        result += r
        counter=counter+1
        if counter < len(all_results):
            result += ","
    result += "]}"
    return result
def generate_one_block_of_result(claim, text, url, elastic_score, stance_score):
    return "{\"claim\":\"" + str(claim) + "\",\"text\":\"" + str(text) + "\",\"url\":\""+str(url)+"\",\"elastic_score\":"+str(elastic_score)+",\"stance_score\":"+str(stance_score)+"}"


def calculate(evidences,identifier):
    allResults = []
    for evidence in evidences:
        result = evidence["result"]
        claim = evidence["query"]  # the text which we search in our documents
        for hit in result["hits"]["hits"]:
            text = hit["_source"]["text"]
            url = hit["_source"]["url"]
            elastic_score = hit["_score"]
            stance_score = doQuery(text, claim)
            allResults.append(generate_one_block_of_result(claim, text, url, elastic_score, stance_score))
    tosave = generate_result_tosave(allResults)

    databasemanager.update_step(settings.results_table_name, settings.results_stancedetection_column_name, tosave,identifier)
    databasemanager.increaseTheStage(settings.results_table_name, identifier)
    # go next level
    thread = threading.Thread(target=orchestrator.goNextLevel, args=(identifier,))
    thread.start()