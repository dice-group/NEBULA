import logging
from typing import Dict, Union, List, Tuple

import tomlkit


def _load_settings_from_config(config: tomlkit.TOMLDocument) -> Tuple[int, str]:
    try:
        hashtags_config = config["layout_and_formal"]["hashtags"]

        hashtag_count_threshold: int = hashtags_config["hashtag_count_threshold"]
        if type(hashtag_count_threshold) is not int:
            raise ValueError(
                "Provided setting for hashtags count threshold 'hashtag_count_threshold' is not "
                "correctly defined. Are you sure it is an integer?"
            )

        display_message_warning: str = hashtags_config["display_message_warning"]
        if not isinstance(display_message_warning, str):
            raise ValueError(
                "Provided setting for hashtags warning message 'display_message_warning' is not "
                "correctly defined. Are you sure it is a string?"
            )

        return hashtag_count_threshold, display_message_warning
    except KeyError as config_not_found_err:
        logging.error(
            "Incorrect capitalization configuration! Check that all required settings are defined."
        )
        raise config_not_found_err


def _extract_hash_tags_unique(input_text: str) -> List[str]:
    return list(
        set(hashtag[1:] for hashtag in input_text.split() if hashtag.startswith("#"))
    )


def detect_excessive_hashtag_usage(
    input_text, config: tomlkit.TOMLDocument
) -> Union[bool, Dict[str, Union[str, List[str]]]]:
    hashtag_count_threshold, display_message_warning = _load_settings_from_config(
        config
    )

    hashtag_list = _extract_hash_tags_unique(input_text)
    hashtag_count = len(hashtag_list)
    if hashtag_list and hashtag_count >= hashtag_count_threshold:
        results = {
            "display_message": display_message_warning,
            "hashtags_list": hashtag_list,
        }
        logging.info(display_message_warning)
        logging.info(
            f"Total number of detected hashtags (without duplicates): {hashtag_count}"
        )

        return results
    else:
        logging.info("No excessive use of hashtags beyond set thresholds.")
        return False
