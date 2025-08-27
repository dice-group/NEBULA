import json
from pprint import pprint
from typing import Any
import requests
import language_tool_python
import tomlkit
from tomlkit import load
from indicators.layout_and_formal import *

# ToDo Import check_for_excessive_capitalization, check_for_excessive_emojis, check_for_excessive_hashtags,
#  check_for_incorrect_spelling
# ToDo Import Json
# ToDo Save Json


CONFIG_PATH: str = "indicators/config.toml"


def load_config() -> tomlkit.TOMLDocument:
    with open(CONFIG_PATH, "rb") as config_file :
        return load(config_file)



def run_indicator_check_api_call(api_url: str, payload: dict) -> dict:
    """
    Calls external NEBULA API with payload, retrieves response,
    and merges API indicators into a single JSON result.
    """
    try:
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }
        # ✅ Pass dict directly (no json.dumps)
        payload = json.dumps(payload)
        api_response = requests.post(api_url, headers=headers, data=payload)
        api_response.raise_for_status()
        print("✅ Response:", api_response.json())
        resp = api_response.json()

        # This is where your API already returns 'general_warning' and 'indicators'
        enriched_output = {
            "id": resp.get("id"),
            "stage_number": resp.get("stage_number"),
            "input_text": resp.get("input_text"),
            "input_lang": resp.get("input_lang"),
            "translation": resp.get("translation"),
            "translation_status": resp.get("translation_status"),
            "claim_check": resp.get("claim_check"),
            "claim_check_status": resp.get("claim_check_status"),
            "evidence_retrieval": resp.get("evidence_retrieval"),
            "stance_detection_status": resp.get("stance_detection_status"),
            "wiseone": resp.get("wiseone"),
            "wiseone_status": resp.get("wiseone_status"),
            "status": resp.get("status"),
            "version": resp.get("version"),
            "error_body": resp.get("error_body"),
            "check_timestamp": resp.get("check_timestamp"),
            # Directly captured from API response:
            "general_warning": resp.get("general_warning", {}),
            "indicators": resp.get("indicators", {}),
        }

        return enriched_output

    except requests.RequestException as e:
        print(f"❌ API call failed: {e}")
        return {"error": str(e)}

def run_indicator_check_api(json_input: Any):
    print("indicator check:"+str(json_input))
    if json_input["TRANSLATED_TEXT"]==None:
        translation = ""
    else:
        translation = json_input["TRANSLATED_TEXT"]
    payload = {
        "id": json_input["IDENTIFIER"],
        "stage_number": json_input["STAGE_NUMBER"],
        "input_text": json_input["COREF_TEXT"],
        "input_lang": json_input["INPUT_LANG"],
        "translation": translation,
        "translation_status": json_input["TRANSLATED_TEXT_STATUS"],
        "claim_check": "",
        "claim_check_status": json_input["CLAIM_CHECK_WORTHINESS_RESULT_STATUS"],
        "evidence_retrieval": "",
        "stance_detection_status": json_input["STANCE_DETECTION_RESULT_STATUS"],
        "wiseone": "",
        "wiseone_status": json_input["WISE_ONE_RESULT_STATUS"],
        "status": "DONE",
        "version": json_input["VERSION"],
        "error_body": json_input["ERROR_BODY"],
        "check_timestamp": json_input["CHECK_TIMESTAMP"]
    }


    # Example call to your API (adjust URL!)
    api_url = "https://nebula.dev.peasec.de/input"
    indicator_check_results = run_indicator_check_api_call(api_url, payload)
    pprint(indicator_check_results)

    return indicator_check_results

def _run_layout_and_formal_checks(input_text: str, config: tomlkit.TOMLDocument):
    results_capitalization = capitalization.check_for_excessive_capitalization(
        input_text=input_text, config=config
    )
    results_angry_emojis = excessive_emojis.check_for_angry_emojis(
        input_text=input_text, config=config
    )
    print(language_tool_python.__file__)
    results_incorrect_grammar = incorrect_grammar.check_incorrect_grammar(
        input_text=input_text, config=config
    )
    results_incorrect_spelling = incorrect_spelling.check_incorrect_spelling(
        input_text=input_text, config=config
    )
    # results_punctuation = punctuation_marks.check_excessive_punctuation(input_text=input_text, config=config)

    all_results = {
        "capitalization": results_capitalization,
        "angry_emojis": results_angry_emojis,
        "incorrect_grammar": results_incorrect_grammar,
        "incorrect_spelling": results_incorrect_spelling,
    }

    return {
        indicator: indicator_results
        for indicator, indicator_results in all_results.items()
        if indicator_results is not False
    }

'''
def _run_rhetorical_checks():
        results_hate_speech = hate_speech.check_for_hate_speech(
        input_text=input_text, config=config        #input_text = translation ?
    )

    all_results = {
        "hate_speech": results_hate_speech,
    }

    return {
        indicator: indicator_results
        for indicator, indicator_results in all_results.items()
        if indicator_results is not False
    } 
'''


def _run_topical_checks():
    pass


def run_indicator_check(json_input: Any):
    input_text = json_input["input_text"]
    input_text_lang = json_input["input_lang"]
    input_text_translation_en = json_input["translation"]
    config = load_config()

    layout_and_formal_results = _run_layout_and_formal_checks(
        input_text=input_text, config=config
    )

    json_output = json_input
    json_output["indicators"] = dict()
    json_output["indicators"]["layout_and_formal"] = layout_and_formal_results

    return json_output

def run_indicator_check_text(input_text: Any):
    config = load_config()
    layout_and_formal_results = _run_layout_and_formal_checks(
        input_text=input_text, config=config
    )
    return layout_and_formal_results


if __name__ == "__main__":
    TEST_FILE_PATH = "./testfiles/testfile.json"
    with open(TEST_FILE_PATH, "r") as testfile:
        json_content = json.load(testfile)
        indicator_check_results = run_indicator_check(json_input=json_content)
        pprint(indicator_check_results)
