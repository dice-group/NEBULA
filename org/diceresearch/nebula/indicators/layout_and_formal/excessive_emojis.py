import itertools
import logging
import re

import tomlkit
from typing import Tuple, List, Dict, Union


def _load_settings_from_config(
    config: tomlkit.TOMLDocument,
) -> Tuple[List[str], bool, int, bool, int, str]:
    try:
        emoji_config = config["layout_and_formal"]["emojis"]

        angry_emojis = emoji_config["angry_emojis"]
        if not (
            isinstance(angry_emojis, list)
            and all(isinstance(emoji, str) for emoji in angry_emojis)
        ):
            raise ValueError(
                "Configuration for angry emojis list `angry_emojis` is incorrect. Are you sure it is "
                "a list of emoji each enclosed in quotes?"
            )

        total_emojis = emoji_config["total_emojis"]["enabled"]
        if type(total_emojis) is not bool:
            raise ValueError(
                "Configuration for whether to carry out total emoji count checks `total_emojis` is "
                "incorrect. Are you sure it is either 'true' or 'false' without quotes?"
            )

        total_emojis_count_threshold: int = emoji_config["total_emojis"][
            "count_threshold"
        ]
        if type(total_emojis_count_threshold) is not int:
            raise ValueError(
                "Configuration for the total emoji count threshold `total_emoji_count_threshold` is "
                "incorrectly defined. Are you sure it is an integer without quotes?"
            )

        consecutive_emojis: bool = emoji_config["consecutive_emojis"]["enabled"]
        if type(consecutive_emojis) is not bool:
            raise ValueError(
                "Configuration for whether to carry out consecutive emoji count checks "
                "`total_emojis` is incorrect. Are you sure it is either 'true' or 'false' without "
                "quotes?"
            )

        consecutive_emojis_count_threshold: int = emoji_config["consecutive_emojis"][
            "count_threshold"
        ]
        if type(consecutive_emojis_count_threshold) is not bool:
            raise ValueError(
                "Configuration for the consecutive emoji count threshold "
                "`consecutive_emoji_count_threshold` is incorrectly defined. Are you sure it is an "
                "integer without quotes?"
            )

        display_message_warning: str = emoji_config["display_message"]
        if type(display_message_warning) is not bool:
            raise ValueError(
                "Configuration for the warning display message for emojis is of incorrect type. Are you "
                "sure it is a string?"
            )

        return (
            angry_emojis,
            total_emojis,
            total_emojis_count_threshold,
            consecutive_emojis,
            consecutive_emojis_count_threshold,
            display_message_warning,
        )
    except KeyError as config_not_found_err:
        logging.error(
            "Incorrect emojis configuration! Check that all required settings are defined."
        )
        raise config_not_found_err


def _get_consecutive_emoji_positions(
    input_text: str, angry_emojis: List[str], consecutive_emoji_count_threshold: int
) -> List[int]:
    def unify_angry_emojis():
        """
        A fix to allow the correct detection of the number of
        consecutive angry emoji occurrences by converting them all into a
        single pre-defined angry emoji so that the consecutive emoji count
        can be correctly determined.

        Note that the original argument input_text is left unchanged.
        """
        unified_input_text = input_text

        for angry_emoji in angry_emojis:
            unified_input_text = unified_input_text.replace(angry_emoji, "😠")

        return unified_input_text

    consecutive_emojis_indices = []
    processed_input_text = unify_angry_emojis()
    angry_emoji_products = [
        "".join(p)
        for p in itertools.product(["😠"], repeat=consecutive_emoji_count_threshold)
    ]
    for product in angry_emoji_products:
        consecutive_emojis_indices += [
            match.start() for match in re.finditer(product, processed_input_text)
        ]

    return consecutive_emojis_indices


def _get_total_emoji_positions(input_text: str, angry_emojis: List[str]) -> List[int]:
    all_emojis_indices = []
    for angry_emoji in angry_emojis:
        all_emojis_indices += [
            match.start() for match in re.finditer(angry_emoji, input_text)
        ]

    return all_emojis_indices


def _get_detected_angry_emojis(input_text: str, angry_emojis: List[str]) -> List[str]:
    return [angry_emoji for angry_emoji in input_text if angry_emoji in angry_emojis]


def check_for_angry_emojis(
    input_text: str, config: tomlkit.TOMLDocument
) -> Union[bool, Dict[str, Union[str, List[int]]]]:
    (
        angry_emojis,
        total_emojis,
        total_emoji_count_threshold,
        consecutive_emojis,
        consecutive_emoji_count_threshold,
        display_message_warning,
    ) = _load_settings_from_config(config)

    consecutive_detected_emojis_positions: List[int]
    total_detected_emojis_positions: List[int]
    consecutive_detected_emojis_positions, total_detected_emojis_positions = [], []

    # Step 1: Which angry emojis exist in the text?
    detected_angry_emojis = _get_detected_angry_emojis(input_text, angry_emojis)

    # Step 2a: Check for consecutively occurring angry emojis.
    if consecutive_emojis:
        consecutive_detected_emojis_positions = _get_consecutive_emoji_positions(
            input_text, angry_emojis, consecutive_emoji_count_threshold
        )

    # Step 2b: Check the total number of angry emojis in the text.
    if total_emojis:
        total_detected_emojis_positions = _get_total_emoji_positions(
            input_text, angry_emojis
        )

    # Step 3: Return back with results.
    if consecutive_detected_emojis_positions or total_detected_emojis_positions:
        logging.info(display_message_warning)
        logging.info(f"List of detected angry emojis: {set(detected_angry_emojis)}\n")

        results = {"display_message": display_message_warning}
        if consecutive_detected_emojis_positions:
            logging.info(
                f"Total number of detected consecutive angry emojis: "
                f"{len(consecutive_detected_emojis_positions) * consecutive_emoji_count_threshold}"
            )
            logging.info(
                f"Locations of detected consecutive angry emojis: {consecutive_detected_emojis_positions}\n"
            )
            results["consecutive_positions"] = consecutive_detected_emojis_positions

        if total_detected_emojis_positions:
            logging.info(
                f"Total number of detected angry emojis: {len(total_detected_emojis_positions)}"
            )
            logging.info(
                f"Locations of all detected angry emojis: {total_detected_emojis_positions}"
            )
            results["total_positions"] = total_detected_emojis_positions

        return results
    else:
        logging.info("No detected angry emojis beyond set thresholds.")
        return False
