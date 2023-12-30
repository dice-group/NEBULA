from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Database table name and column names
database_name = "db20230530.db"
results_table_name="RESULTS"
stage_number="STAGE_NUMBER"
results_inputtext_column_name = "INPUT_TEXT"
results_inputlang_column_name = "INPUT_LANG"
results_translation_column_name = "TRANSLATED_TEXT"
results_translation_column_status = "TRANSLATED_TEXT_STATUS"
results_coref_column_name = "COREF_TEXT"
results_coref_column_status = "COREF_TEXT_STATUS"
results_claimworthiness_column_status = "CLAIM_CHECK_WORTHINESS_RESULT_STATUS"
results_evidenceretrieval_column_status = "EVIDENCE_RETRIEVAL_RESULT_STATUS"
results_stancedetection_column_status = "STANCE_DETECTION_RESULT_STATUS"
results_wiseone_column_status = "WISE_ONE_RESULT_STATUS"
results_wise_final_column_name = "WISE_FINAL_RESULT"
results_wise_final_column_status = "WISE_FINAL_RESULT_STATUS"
results_veracity_label = "VERACITY_LABEL"
sentences = "SENTENCES"
results_notificationtoken_column_name = "REGISTRATION_TOKEN"
results_indicator_check = "INDICATOR_CHECK"
results_indicator_check_status = "INDICATOR_CHECK_STATUS"

# Status literals
skipped = "SKIPPED"
completed = "COMPLETED"
done = "DONE"
ongoing = "ONGOING"
failed = "FAILED"
error = "ERROR"
error_msg = "ERROR_BODY"
timestamp = "CHECK_TIMESTAMP"
status = "STATUS"

# Logging configuration
logging_config = 'resources/logging_config.ini'

# translator options
translatorEndpoint = "http://neamt.cs.upb.de:6100/custom-pipeline"
translator = "opus_mt"

# Coreference resolution
coref_endpoint = "http://nebulavm2-bullseye.cs.upb.de:9090/validate"

# claim check options
module_claimworthiness = "claimbuster"
claimbuster_apikey = os.getenv("API_KEY")
claimbuster_api_endpoint = "https://idir.uta.edu/claimbuster/api/v2/score/text/sentences/"
claim_limit=10

# Evidence retrieval options
elasticsearch_index_name = "nebula"
elasticsearch_api_endpoint = "http://nebulavm.cs.uni-paderborn.de:9200"
run_evidence_retrival_bulk_or_single = "single"

# Stance detection options
stancedetection_api = "http://localhost:8001/check/"

# WISE options
trained_model = "./resources/model_130723.pt"
model_timestamp = "2023-07-13"  # WISE model last trained date
low_threshold = 0.66  # Thresholds to be used in case of regression model
high_threshold = 0.69
class_labels = ['REFUTED', 'NOT ENOUGH INFO', 'SUPPORTED']  # fever labels

# Final WISE step options
rnn_model = "./resources/model_rnn_061223.pt"
final_model_timestamp = "2023-12-06"
final_low_threshold = 0.46  # Thresholds to be used in case of regression model
final_high_threshold = 0.47
final_class_labels = ['UNRELIABLE', 'MIXED', 'RELIABLE']  # nela labels
false_label = 'UNRELIABLE'

# Reference corpus last modified date
knowledge_timestamp = "2023-05-31"

# firebase push notifications
firebase_certificate = './resources/nebula-dev-c8f4a-firebase-adminsdk-acvxz-db4b4471d0.json'

