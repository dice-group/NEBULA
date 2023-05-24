import json
from json import JSONDecodeError

import claimworthinesschecker
import databasemanager
import evidenceretrival
import settings
import threading

import stancedetection
import translator
def goNextLevel(identifier):
    print("orch:"+identifier)
    current = databasemanager.getOne(settings.results_table_name, identifier)
    STAGE_NUMBER = current[1]
    INPUT_TEXT = current[2]
    INPUT_LANG = current[3]
    TRANSLATED_TEXT = current[4]
    CLAIM_CHECK_WORTHINESS_RESULT = current[6]
    EVIDENCE_RETRIVAL_RESULT = current[8]
    if current==None:
        print("could not find this row in database " + identifier)
    current_stage = int(STAGE_NUMBER)
    print("curront stage is : "+str(current_stage))
    next_stage = current_stage + 1
    if next_stage == 1:
        #translate
        # language
        if INPUT_LANG!="en":
            # start the translation step
            print("translation step")
            thread = threading.Thread(target=translator.sendTranslationRequest, args=(INPUT_TEXT,identifier))
            thread.start()
        else:
            #update the stage
            print("skip the translation")
            #databasemanager.increaseTheStage(settings.results_table_name, identifier)
            databasemanager.update_step(settings.results_table_name, settings.results_translation_column_name, INPUT_TEXT, identifier)
            goNextLevel(identifier)
        pass
    elif next_stage == 2:
        #claim
        thread = threading.Thread(target=claimworthinesschecker.check, args=(TRANSLATED_TEXT, identifier))
        thread.start()
        pass
    elif next_stage == 3:
        #evidence retrival
        if CLAIM_CHECK_WORTHINESS_RESULT==None:
            print("error : the claims worthiness responce is null")
        try:
            textToConvert = str(CLAIM_CHECK_WORTHINESS_RESULT)
            jsonCheckdClaimsForWorthiness = json.loads(textToConvert)
            print(str(jsonCheckdClaimsForWorthiness))
            print(jsonCheckdClaimsForWorthiness["results"])
            print(jsonCheckdClaimsForWorthiness["results"][0])


#        {'version': '2',
#         'sentences': 'Now from January 1st: EU standard chip EPS replaces personal identity card Saturday, 20 Jul 2019 Facebook What has been standard for dogs and cats for years worldwide, will be gradually introduced from January 1st 2021 also for citizens of the European Union. This idea is not completely new, but with the project in the European Union now for the first time in a large style introduced in a community of states. 2022',
#         'results': [{
#                         'text': 'Now from January 1st: EU standard chip EPS replaces personal identity card Saturday, 20 Jul 2019 Facebook What has been standard for dogs and cats for years worldwide, will be gradually introduced from January 1st 2021 also for citizens of the European Union.',
#                         'index': 0, 'score': 0.5979533384}, {
#                         'text': 'This idea is not completely new, but with the project in the European Union now for the first time in a large style introduced in a community of states.',
#                         'index': 1, 'score': 0.7661571161}, {'text': '2022', 'index': 2, 'score': 0.37916248}]}
            maxScore = 0;
            maxIndex = 0
            for rr in jsonCheckdClaimsForWorthiness["results"]:
                    if (maxScore < rr['score']):
                        maxScore = rr['score']
                        maxIndex = rr['index']
            if settings.run_evidence_retrival_bulk_or_single == "single":
                thread = threading.Thread(target=evidenceretrival.retrive, args=(jsonCheckdClaimsForWorthiness["results"][maxIndex]["text"], identifier))
                thread.start()
            else:
                thread = threading.Thread(target=evidenceretrival.bulkRetrive(),
                                          args=(jsonCheckdClaimsForWorthiness, identifier))
                thread.start()
        except JSONDecodeError as exp:
            print(exp.msg)
        pass
    elif next_stage == 4:
        try:
            print("stance detection")
            tempString = str(EVIDENCE_RETRIVAL_RESULT)
            evidences = json.loads(tempString)
            mainText = evidences["result"]["hits"]["hits"][0]["_source"]["text"]
            claim = evidences["query"]
            thread = threading.Thread(target=stancedetection.detect(),
                                  args=(mainText,claim, identifier))
            thread.start()
            #stance detection
        except Exception as e:
            print(e)

        pass
    elif next_stage == 5:
        print("not developed yet")
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