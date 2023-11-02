import logging
from typing import List, Union, Dict

import nltk
from nltk.tokenize import word_tokenize

import tomlkit


def _load_settings_from_config(config: tomlkit.TOMLDocument) -> str:
    try:
        capitalization_config = config["layout_and_formal"]["capitalization"]

        display_message_warning: str = capitalization_config["display_message_warning"]
        if not isinstance(display_message_warning, str):
            raise ValueError(
                "Provided setting for capitalization warning message 'display_message_warning' is not "
                "correctly defined. Are you sure it is a string?"
            )

        return display_message_warning
    except KeyError as config_not_found_err:
        logging.error(
            "Incorrect capitalization configuration! Check that all required settings are defined."
        )
        raise config_not_found_err


def check_for_excessive_capitalization(
    input_text: str, config: tomlkit.TOMLDocument
) -> Union[bool, Dict[str, Union[str, List[int]]]]:
    display_message_warning: str = _load_settings_from_config(config)
    nltk.download("punkt")

    words: List[str] = word_tokenize(input_text)

    # Initialize list to store positions of all caps letters in the text
    allcaps_positions: List[int] = []

    # Count number of words in all caps and store the positions of all caps letters
    allcaps_count: int = 0  # Initialize a counter for all caps words
    current_position: int = 0  # Initialize the position tracker in the text

    for idx, word in enumerate(words):
        if word.isupper():
            allcaps_count += 1
            word_start = input_text.find(word, current_position)
            if word_start != -1:
                for letter_position in range(word_start, word_start + len(word)):
                    allcaps_positions.append(letter_position)
                current_position = word_start + len(word)

    # Print positions of all caps letters
    if allcaps_positions:
        results = {
            "display_message": display_message_warning,
            "allcaps_positions": allcaps_positions,
        }
        logging.info(display_message_warning)
        logging.info(
            "Excessive capitalisation is detected in the following positions:\n"
        )
        for position in allcaps_positions:
            logging.info(f"Position: {position}")

        return results
    else:
        logging.info("No all-caps letters have been detected in the text.")
        return False
