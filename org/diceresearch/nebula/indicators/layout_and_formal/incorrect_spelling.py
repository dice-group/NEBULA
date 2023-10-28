import logging
import re
import string

import tomlkit
from nltk.tokenize import word_tokenize
# noinspection PyPackageRequirements
from spellchecker import SpellChecker
from typing import Set, Tuple, List, Union, Dict

"""
Note: It is necessary to remove punctuation first because otherwise all punctuation marks are identified as spelling
mistakes because most spell checkers, including pyspellchecker, consider punctuation marks as separate words and
are typically not part of their dictionaries.
"""


def _load_settings_from_config(config: tomlkit.TOMLDocument):
    try:
        spelling_config = config["layout_and_formal"]["spelling"]

        spellchecker_lang = spelling_config["spellchecker"]["lang"]
        if type(spellchecker_lang) is not str:
            raise ValueError("Provided setting for spelling language 'spellchecker.lang' is not "
                             "correctly defined. Are you sure it is a string?")

        display_message_warning: str = spelling_config["display_message_warning"]
        if type(display_message_warning) is not str:
            raise ValueError("Provided setting for capitalization warning message 'display_message_warning' is not "
                             "correctly defined. Are you sure it is a string?")

        return spellchecker_lang, display_message_warning
    except KeyError as config_not_found_err:
        logging.error("Incorrect spelling configuration! Check that all required settings are defined.")
        raise config_not_found_err


def _remove_punctuation(input_text: str):
    return word_tokenize(input_text.translate(str.maketrans('', '', string.punctuation)))


def check_incorrect_spelling(input_text: str, config: tomlkit.TOMLDocument) \
        -> Union[bool, Dict[str, Union[str, List[str], List[Tuple[int, int]]]]]:
    spellchecker_lang, display_message_warning = _load_settings_from_config(config)

    spell = SpellChecker(language=spellchecker_lang)
    words_without_punctuation = _remove_punctuation(input_text)

    # Überprüfen der Rechtschreibung für jedes Wort im Text
    misspelled_words: Set[str] = spell.unknown(words_without_punctuation)

    # Initialize a list to store positions and words
    misspelled_words_start_end: List[Tuple[str, int, int]] = []
    for misspelled_word in misspelled_words:
        misspelled_words_start_end += [(misspelled_word, matched_word.start(), matched_word.end())
                                       for matched_word in re.finditer(misspelled_word, words_without_punctuation)]

    # Output misspelled words (spelling errors)
    if misspelled_words_start_end:
        results = {"display_message": display_message_warning, "misspelled_words": misspelled_words,
                   "misspelled_word_positions": [(word[1], word[2]) for word in misspelled_words_start_end]}
        logging.info(display_message_warning)
        logging.info("Misspelled letters found at the following positions in the text:")
        for misspelled_word_start_end in misspelled_words_start_end:
            logging.info(f"Word: {misspelled_word_start_end[0]} "
                         f"({misspelled_word_start_end[1]}-{misspelled_word_start_end[2]}.")

        return results
    else:
        logging.info("No spelling errors were identified.")
        return False
