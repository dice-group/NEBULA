import logging
from typing import List, Tuple, Union


def check_for_excessive_capitalization(input_text: str, words: List[str]) -> Union[bool, Tuple[List[int], str]]:
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

    # Check if any all caps letters were found
    allcaps_infotext = "Excessive capitalisation attracts attention. This might be used for emotional manipulation."
    allcaps_info = allcaps_positions, allcaps_infotext

    # Print positions of all caps letters
    if allcaps_positions:
        # print(allcaps_infotext)
        # print("Excessive capitalisation is detected in the following positions:")
        logging.info(allcaps_infotext)
        logging.info("Excessive capitalisation is detected in the following positions:")
        for position in allcaps_positions:
            # print(f"Position: {position}")
            logging.info(f"Position: {position}")

        return allcaps_positions, allcaps_infotext
    else:
        # print("No all caps letters have been detected in the text.")
        logging.info("No all caps letters have been detected in the text.")

        return False
