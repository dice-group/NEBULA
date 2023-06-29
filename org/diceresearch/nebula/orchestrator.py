import json
import logging
from json import JSONDecodeError

import claimworthinesschecker
import claimworthinesscheckerdummy
import databasemanager
import evidenceretrival
import settings
import threading
from datetime import datetime

import stancedetection
import translator


def goNextLevel(identifier):
    current = databasemanager.getOne(settings.results_table_name, identifier)
    STAGE_NUMBER = current[1]
    INPUT_TEXT = current[2]
    INPUT_LANG = current[3]
    TRANSLATED_TEXT = current[4]
    CLAIM_CHECK_WORTHINESS_RESULT = current[6]
    EVIDENCE_RETRIVAL_RESULT = current[8]
    if current==None:
        logging.error("could not find this row in database " + identifier)
    current_stage = int(STAGE_NUMBER)
    logging.info("curront stage is : "+str(current_stage))
    next_stage = current_stage + 1
    if next_stage == 1:
        databasemanager.update_step(settings.results_table_name, "STATUS", "ongoing", identifier)
        databasemanager.update_step(settings.results_table_name, "CHECK_TIMESTAMP", datetime.now().isoformat('#'), identifier)
        #translate
        # language
        if INPUT_LANG!="en":
            if(settings.skipTranstaltion):
                # update the stage
                logging.info("skip the translation")
                # databasemanager.increaseTheStage(settings.results_table_name, identifier)
                databasemanager.update_step(settings.results_table_name, settings.results_translation_column_name,
                                            INPUT_TEXT, identifier)
                databasemanager.increase_the_stage(settings.results_table_name, identifier)
                goNextLevel(identifier)
            else:
                # start the translation step
                logging.info("translation step")
                thread = threading.Thread(target=translator.send_translation_request, args=(INPUT_TEXT, identifier))
                thread.start()
        else:
            #update the stage
            logging.info("skip the translation")
            #databasemanager.increaseTheStage(settings.results_table_name, identifier)
            databasemanager.update_step(settings.results_table_name, settings.results_translation_column_name, INPUT_TEXT, identifier)
            databasemanager.increase_the_stage(settings.results_table_name, identifier)
            goNextLevel(identifier)
        pass
    elif next_stage == 2:
        #claim
        if settings.module_claimworthiness == "dummy":
            thread = threading.Thread(target=claimworthinesscheckerdummy.check, args=(TRANSLATED_TEXT, identifier))
            thread.start()
        else:
            thread = threading.Thread(target=claimworthinesschecker.check, args=(TRANSLATED_TEXT, identifier))
            thread.start()
        pass
    elif next_stage == 3:
        #evidence retrival
        if CLAIM_CHECK_WORTHINESS_RESULT==None:
            logging.error("error : the claims worthiness response is null")
            databasemanager.update_step(settings.results_table_name, "STATUS", "error", identifier)
            databasemanager.update_step(settings.results_table_name, "ERROR_BODY", "the claims worthiness response is null", identifier)
        try:
            #textToConvert = str(CLAIM_CHECK_WORTHINESS_RESULT)
            jsonCheckdClaimsForWorthiness = json.loads(CLAIM_CHECK_WORTHINESS_RESULT)

#        {'version': '2',
#         'sentences': 'Now from January 1st: EU standard chip EPS replaces personal identity card Saturday, 20 Jul 2019 Facebook What has been standard for dogs and cats for years worldwide, will be gradually introduced from January 1st 2021 also for citizens of the European Union. This idea is not completely new, but with the project in the European Union now for the first time in a large style introduced in a community of states. 2022',
#         'results': [{
#                         'text': 'Now from January 1st: EU standard chip EPS replaces personal identity card Saturday, 20 Jul 2019 Facebook What has been standard for dogs and cats for years worldwide, will be gradually introduced from January 1st 2021 also for citizens of the European Union.',
#                         'index': 0, 'score': 0.5979533384}, {
#                         'text': 'This idea is not completely new, but with the project in the European Union now for the first time in a large style introduced in a community of states.',
#                         'index': 1, 'score': 0.7661571161}, {'text': '2022', 'index': 2, 'score': 0.37916248}]}
#            maxScore = 0;
#            maxIndex = 0
#            for rr in jsonCheckdClaimsForWorthiness["results"]:
#                    if (maxScore < rr['score']):
#                        maxScore = rr['score']
#                        maxIndex = rr['index']
#            if settings.run_evidence_retrival_bulk_or_single == "single":
#                thread = threading.Thread(target=evidenceretrival.retrive, args=(jsonCheckdClaimsForWorthiness["results"][maxIndex]["text"], identifier))
#                thread.start()
#            else:
            thread = threading.Thread(target=evidenceretrival.retrive,
                                          args=(jsonCheckdClaimsForWorthiness, identifier))
            thread.start()
        except JSONDecodeError as exp:
            logging.error(exp.msg)
            databasemanager.update_step(settings.results_table_name, "STATUS", "error", identifier)
            databasemanager.update_step(settings.results_table_name, "ERROR_BODY", str(exp.msg), identifier)
        pass
    elif next_stage == 4:
        try:
            logging.info("stance detection")
            tempjson = json.loads(EVIDENCE_RETRIVAL_RESULT)
            temp_evidences = tempjson["evidences"]

            #mainText = tempjson["result"]["hits"]["hits"][0]["_source"]["text"]

            #tempjson = json.loads(EVIDENCE_RETRIVAL_RESULT)
            #claim = tempjson["query"]
            thread = threading.Thread(target=stancedetection.calculate,
                                      args=(temp_evidences, identifier))
            thread.start()
            #stance detection
        except Exception as e:
            logging.error(str(e))
            databasemanager.update_step(settings.results_table_name, "STATUS", "error", identifier)
            databasemanager.update_step(settings.results_table_name, "ERROR_BODY", str(e), identifier)

        pass
    elif next_stage == 5:
        databasemanager.update_step(settings.results_table_name, "STATUS", "done", identifier)
        logging.info("not developed yet")
        pass
    elif next_stage == 6:
        pass
    elif next_stage == 7:
        pass
    elif next_stage == 8:
        pass
    elif next_stage == 9:
        pass
    else:
        pass