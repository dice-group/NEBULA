from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

database_name = "test.db"
results_table_name="RESULTS"
results_translation_column_name = "TRANSLATED_TEXT"
results_claimworthiness_column_name = "CLAIM_CHECK_WORTHINESS_RESULT"
translatorEndpoint = "http://neamt.cs.upb.de:6100/custom-pipeline"
claimbuster_apikey = os.getenv("API_KEY")
claimbuster_api_endpoint = "https://idir.uta.edu/claimbuster/api/v2/score/text/sentences/"
