import json
from json import JSONDecodeError

import claimworthinesschecker
import databasemanager
import evidenceretrival
import settings
import threading
import translator
def goNextLevel(identifier):
    print("orch:"+identifier)
    current = databasemanager.getOne(settings.results_table_name, identifier)
    if current==None:
        print("could not find this row in database " + identifier)
    current_stage = int(current[1])
    print("curront stage is : "+str(current_stage))
    next_stage = current_stage + 1
    if next_stage == 1:
        #translate
        # language
        if current[3]!="en":
            # start the translation step
            print("translation step")
            thread = threading.Thread(target=translator.sendTranslationRequest, args=(current[2],identifier))
            thread.start()
        else:
            #update the stage
            print("skip the translation")
            databasemanager.increaseTheStage(settings.results_table_name, identifier)
            goNextLevel(identifier)
        pass
    elif next_stage == 2:
        #claim
        thread = threading.Thread(target=claimworthinesschecker.check, args=(current[4], identifier))
        thread.start()
        pass
    elif next_stage == 3:
        #evidence retrival
        if current[5]==None:
            print("error : the claims worthiness responce is null")
        try:
            jsonCheckdClaimsForWorthiness = json.loads(str(current[5]).replace("\'", "\""))
            print(str(jsonCheckdClaimsForWorthiness))
            print(jsonCheckdClaimsForWorthiness["results"])
            print(jsonCheckdClaimsForWorthiness["results"][0])
        except JSONDecodeError as exp:
            print(exp.msg)

#        {'version': '2',
#         'sentences': 'Now from January 1st: EU standard chip EPS replaces personal identity card Saturday, 20 Jul 2019 Facebook What has been standard for dogs and cats for years worldwide, will be gradually introduced from January 1st 2021 also for citizens of the European Union. This idea is not completely new, but with the project in the European Union now for the first time in a large style introduced in a community of states. 2022',
#         'results': [{
#                         'text': 'Now from January 1st: EU standard chip EPS replaces personal identity card Saturday, 20 Jul 2019 Facebook What has been standard for dogs and cats for years worldwide, will be gradually introduced from January 1st 2021 also for citizens of the European Union.',
#                         'index': 0, 'score': 0.5979533384}, {
#                         'text': 'This idea is not completely new, but with the project in the European Union now for the first time in a large style introduced in a community of states.',
#                         'index': 1, 'score': 0.7661571161}, {'text': '2022', 'index': 2, 'score': 0.37916248}]}
        thread = threading.Thread(target=evidenceretrival.retrive, args=(current[5], identifier))
        thread.start()
        print("not developed yet")
        pass
    elif next_stage == 4:
        #stance detection
        pass
    elif next_stage == 5:
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