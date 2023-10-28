import logging
from typing import List, Tuple

import tomlkit
from language_tool_python import LanguageTool, Match


def _load_settings_from_config(config: tomlkit.TOMLDocument) -> Tuple[str, str]:
    try:
        grammar_config = config["layout_and_formal"]["grammar"]

        language: str = grammar_config["languagetool"]["lang"]
        if type(language) is not str:
            raise ValueError(
                "Provided setting for LanguageTool language 'language' is not "
                "correctly defined. Are you sure it is a string?"
            )

        display_message_warning: str = grammar_config["display_message_warning"]
        if type(display_message_warning) is not str:
            raise ValueError(
                "Provided setting for grammar check warning message 'display_message_warning' is not "
                "correctly defined. Are you sure it is a string?"
            )

        return language, display_message_warning
    except KeyError as config_not_found_err:
        logging.error(
            "Incorrect grammar configuration! Check that all required settings are defined."
        )
        raise config_not_found_err


def check_incorrect_grammar(input_text: str, config: tomlkit.TOMLDocument):
    # Check for grammar and style errors

    language, display_message_warning = _load_settings_from_config(config)
    tool = LanguageTool(
        language=language, config={"cacheSize": 1000, "pipelineCaching": True}
    )
    matches: List[Match] = tool.check(input_text)

    # Initialize a list to store grammar errors and positions.
    grammar_errors: List[Tuple[str, int, int]] = []

    # Process the detected errors and save them in a list.
    # ASK Are only grammar errors supposed to be considered here?
    for match in matches:
        error_message = match.message
        error_offset = match.offset
        error_length = match.errorLength
        grammar_errors.append((error_message, error_offset, error_length))

    # Output misspelled words (spelling errors).
    if grammar_errors:
        results = {
            "display_message": display_message_warning,
            "grammar_errors": grammar_errors,
        }
        logging.info(display_message_warning)
        logging.info("The following grammatical mistakes were identified:")
        for error in grammar_errors:
            logging.info(f"Grammatical error: {error[0]} (Position {error[1]})")

        return results
    else:
        logging.info("No grammatical errors were identified.")
        return False
