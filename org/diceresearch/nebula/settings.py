from dotenv import load_dotenv
import os
import logging

# Load environment variables from .env file
load_dotenv()

database_name = "db20230530.db"
results_table_name="RESULTS"
results_inputtext_column_name = "INPUT_TEXT"
results_inputlang_column_name = "INPUT_LANG"
results_translation_column_name = "TRANSLATED_TEXT"
results_translation_column_status = "TRANSLATED_TEXT_STATUS"
results_claimworthiness_column_name = "CLAIM_CHECK_WORTHINESS_RESULT"
results_claimworthiness_column_status = "CLAIM_CHECK_WORTHINESS_RESULT_STATUS"
results_evidenceretrival_column_name = "EVIDENCE_RETRIVAL_RESULT"
results_evidenceretrival_column_status = "EVIDENCE_RETRIVAL_RESULT_STATUS"
results_stancedetection_column_name = "STANCE_DETECTION_RESULT"
results_stancedetection_column_status = "STANCE_DETECTION_RESULT_STATUS"

translatorEndpoint = "http://neamt.cs.upb.de:6100/custom-pipeline"

#claimbuster, dummy
module_claimworthiness = "dummy"
claimbuster_apikey = os.getenv("API_KEY")
claimbuster_api_endpoint = "https://idir.uta.edu/claimbuster/api/v2/score/text/sentences/"

elasticsearch_index_name = "nebula"
elasticsearch_api_endpoint = "http://nebulavm.cs.uni-paderborn.de:9200"

stancedetection_api = "http://localhost:8001/check/"

run_evidence_retrival_bulk_or_single = "single"