# # umair changes
# import json
# import logging
# import threading
# from openai import OpenAI
# import orchestrator
# import settings
# import nltk
# import requests
# from utils.database_utils import log_exception, update_database
#
# nltk.download('punkt')
# nltk.download('stopwords')
#
#
# similarity_array = []
#
# stopwords = nltk.corpus.stopwords.words('english')
# CustomListofWordstoExclude = ["'s", 'say', 'says', 'said', 's', "n't"]
# stopwords.extend(CustomListofWordstoExclude)
#
#
# #https://dice-llm-chat.cs.uni-paderborn.de/ollama/http://tentris-ml.cs.upb.de:8000/api/generate llama3.3:70b
# class LLMStanceDetector:
#     def __init__(self, model: str = "llama-4-scout",
#                  url: str = "https://dice-llm-chat.cs.uni-paderborn.de/api/chat/completions"):
#         self.model = model
#         self.url = url
#
#     def get_response_from_api_call(self, text: str, claim: str):
#         """
#         :param text: String representation of an OWL Class Expression
#         """
#         # print(text)
#         BASE_URL = 'https://dice-llm-chat.cs.uni-paderborn.de/api'
#         API_KEY = "sk-69cb04477beb4330b0ec2ed676688856"
#         MODEL_ID = self.model
#         OPAI_CLIENT = OpenAI(base_url=BASE_URL, api_key=API_KEY)
#         # MODEL_ID = GEMMA3_CONFIG.model_id
#         sys_prompt = (
#             "You are performing stance detection. Given a claim and a textual description, output one of the following stance labels only: SUPPORTS, REFUTES, or NOT ENOUGH INFO.\n"
#             "Return only the stance label, nothing else.\n"
#             "Do not assume claims that are trivially or tautologically true (e.g., X is X) are supported. Only respond `SUPPORTS` if the claim is **meaningfully confirmed** by the description.\n"
#             "\n"
#             # SUPPORTS Example
#             "Given textual description:\n"
#             "Brad Wilk (born September 5, 1968) is an American drummer. He is best known as a member of the rock bands Rage Against the Machine (1991–2000, 2007–2011, 2019–present), Audioslave (2001–2007, 2017), and Prophets of Rage (2016–2019). Wilk started his career as a drummer for Greta in 1990, and helped co-found Rage Against the Machine with Tom Morello and Zack de la Rocha in August 1991.\n"
#             "Claim: Brad Wilk was a drummer for Greta.\n"
#             "Answer: SUPPORTS\n"
#             "\n"
#             # REFUTES Example
#             "Given textual description:\n"
#             "Brad Wilk is known for his significant involvement in the music industry, particularly as a drummer for bands like Rage Against the Machine and Audioslave, but there are no records of him being professionally involved in opera music or performing in operatic settings.\n"
#             "Claim: Brad Wilk was an opera singer.\n"
#             "Answer: REFUTES\n"
#             "\n"
#             # NOT ENOUGH INFO Example
#             "Given textual description:\n"
#             "Brad Wilk has participated in many musical collaborations and various side projects throughout his career, but detailed information about all his collaborations isn't mentioned.\n"
#             "Claim: Brad Wilk played with the band Foo Fighters at some point in his career.\n"
#             "Answer: NOT ENOUGH INFO\n"
#         )
#         prompt = (
#             # Actual Input
#             f"Given textual description:\n{text}\n"
#             f"Claim: {claim}\n"
#             "Answer:"
#         )
#
#         completion = OPAI_CLIENT.chat.completions.create(
#             model=MODEL_ID,
#             messages=[
#                 {"role": "system", "content": sys_prompt},
#                 {
#                     "role": "user",
#                     "content": prompt,
#                 },
#             ],
#         )
#         print(completion.choices[0].message.content)
#         return completion.choices[0].message.content
#
# def calculate_score_using_api_call(maintext, claim):
#     stanceDetector = LLMStanceDetector()
#     answer = stanceDetector.get_response_from_api_call(text=maintext, claim=claim)
#     answer = answer.replace("\n", " ")
#     score = 0
#     if "Answer: REFUTES" in answer or ("no evidence that supports the claim".lower() in answer.lower() or ("REFUTE".lower() in answer.lower() and "SUPPORT".lower() not in answer.lower())):
#         score = -1
#     elif "Answer: SUPPORTS" in answer or ("SUPPORT".lower() in answer.lower() and "REFUTE".lower() not in answer.lower()):
#         score = 1
#     elif "NOT ENOUGH INFO".lower() in answer.lower():
#         score = 0
#     else:
#         score = 0
#     print("Stance Detection Results:"+str(score))
#     return str(score)
#
#
# def do_query(maintext, claim):
#     return calculate_score_using_api_call(maintext, claim)
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
#
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
#             for evidence in evidences:
#                 evidence_text = evidence['evidence_text']
#
#                 # continue if text is empty
#                 if not evidence_text:
#                     logging.warning("Skipping. Evidence not found for claim {}".format(claim_text))
#                     continue
#
#                 # compute score between claim and evidence text
#                 stance_score = do_query(evidence_text, claim_text)
#                 evidence['stance_score'] = stance_score
#
#         # parse to json
#         claims_json = json.dumps(claims)
#
#         # update database
#         update_database(settings.sentences, settings.results_stancedetection_column_status, claims_json, identifier)
#
#         # go next level
#         orchestrator.goNextLevel(identifier)
#     except Exception as e:
#         log_exception(e, identifier)
#
# # end here
