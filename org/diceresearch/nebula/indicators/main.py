import json
from pprint import pprint
from typing import Any
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


def _run_layout_and_formal_checks(input_text: str, config: tomlkit.TOMLDocument):
    results_capitalization = capitalization.check_for_excessive_capitalization(
        input_text=input_text, config=config
    )
    results_angry_emojis = excessive_emojis.check_for_angry_emojis(
        input_text=input_text, config=config
    )
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
