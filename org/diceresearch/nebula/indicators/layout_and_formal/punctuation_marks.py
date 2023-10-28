import logging
import re

import tomlkit


def _load_settings_from_config(config: tomlkit.TOMLDocument) -> str:
    try:
        punctuation_config = config["layout_and_formal"]["punctuation"]

        display_message_warning: str = punctuation_config["display_message_warning"]
        if type(display_message_warning) is not str:
            raise ValueError(
                "Provided setting for punctuation warning message 'display_message_warning' is not "
                "correctly defined. Are you sure it is a string?"
            )

        return display_message_warning
    except KeyError as config_not_found_err:
        logging.error(
            "Incorrect punctuation configuration! Check that all required settings are defined."
        )
        raise config_not_found_err


def check_excessive_punctuation(input_text: str, config: tomlkit.TOMLDocument):
    display_message_warning = _load_settings_from_config(config)

    # Define a RegEx pattern to match excessive punctuation (more than one consecutive punctuation mark)
    # ASK Should this be moved over to the config?
    excessive_punctuation_pattern = r"[?!.]{2,}"

    # Find matches using the RegEx pattern
    matches = re.finditer(excessive_punctuation_pattern, input_text)

    # Initialize a list to store positions and excessive punctuation sequences
    punctuation_positions = []

    # Process and store matches
    for match in matches:
        start_pos = match.start()
        end_pos = match.end()
        punctuation_sequence = input_text[start_pos:end_pos]
        punctuation_positions.extend(range(start_pos, end_pos))

    # Print positions and excessive punctuation sequences
    if punctuation_positions:
        results = {"display_message": display_message_warning}
        logging.info(display_message_warning)
        logging.info("The following punctuation marks are used excessively:")
        for _ in punctuation_positions:
            # FIXME Possible reference before assignment (may lead to runtime error).
            logging.info(
                f"Excessive punctuation: '{punctuation_sequence}' (Position: {start_pos}-{end_pos})"
            )

        return results
    else:
        logging.info("No excessive punctuation has been detected in the input text.")
        return False
