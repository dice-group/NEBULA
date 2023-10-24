from tomlkit import load

with open("../config.toml", "rb") as config_file:
    config = load(config_file)

"""
Parameters to be modified accordingly:

ANGRY_EMOJIS: A list of emojis which are to be considered as expressing an
angry or upset emotion.

EMOJI_COUNT: The minimum number of occurrences of an angry emoji before
the containing sentence is considered an indicator (since not every usage of
emojis, even angry onces, necessarily constitutes an indicator).

CONSECUTIVE_EMOJIS: Whether only consecutively occurring angry emojis should be
considered. This is useful if we wish to only look for the specific use case of
emojis occurring in a row. THIS PARAMETER IS EXPERIMENTAL AND MAY NOT WORK AS
INTENDED!

INPUT: The input string in which to look for angry emojis.
"""
# ANGRY_EMOJIS = ["😤", "😠", "😡", "🤬", "👿"]
# CONSECUTIVE_EMOJI_COUNT_THRESHOLD: int = 3
# TOTAL_EMOJI_COUNT_THRESHOLD: int = 3
# CONSECUTIVE_EMOJIS: bool = True
# TOTAL_EMOJIS = True

ANGRY_EMOJIS = config["layout_and_formal"]["emojis"]["angry_emojis"]
TOTAL_EMOJIS = config["layout_and_formal"]["emojis"]["total_emojis"]
TOTAL_EMOJI_COUNT_THRESHOLD: int = config["layout_and_formal"]["emojis"]["total_emoji_count_threshold"]
CONSECUTIVE_EMOJIS: bool = config["layout_and_formal"]["emojis"]["consecutive_emojis"]
CONSECUTIVE_EMOJI_COUNT_THRESHOLD: int = config["layout_and_formal"]["emojis"]["consecutive_emoji_count_threshold"]


def check_for_angry_emojis(input_text: str):
    detected, detected_consecutive, detected_total = False, False, False
    occurrences_indices_total, occurrences_indices_consecutive = [], []

    detected_angry_emojis = [angry_emoji for angry_emoji in input_text if angry_emoji in ANGRY_EMOJIS]
    detected_angry_emojis_total_count = len(detected_angry_emojis)

    if CONSECUTIVE_EMOJIS:
        def unify_angry_emojis():
            """
            A fix to allow the correct detection of the number of
            consecutive angry emoji occurrences by converting them all into a
            single pre-defined angry emoji so that the consecutive emoji count
            can be correctly determined.

            Note that the original argument input_text is left unchanged.
            """
            unified_input_text = input_text

            for angry_emoji in ANGRY_EMOJIS:
                unified_input_text = unified_input_text.replace(angry_emoji, "😠")

            return unified_input_text

        processed_input_text = unify_angry_emojis()
        angry_emoji_products = [''.join(p) for p in itertools.product(["😠"], repeat=CONSECUTIVE_EMOJI_COUNT_THRESHOLD)]
        for product in angry_emoji_products:
            occurrences_indices_consecutive += [match.start() for match in re.finditer(product, processed_input_text)]

        number_of_detected_angry_emojis = len(detected_angry_emojis)
        if occurrences_indices_consecutive:
            detected = True
            detected_consecutive = True

    if TOTAL_EMOJIS:
        if detected_angry_emojis_total_count >= TOTAL_EMOJI_COUNT_THRESHOLD:
            detected = True
            detected_total = True
            for angry_emoji in ANGRY_EMOJIS:
                occurrences_indices_total += [match.start() for match in re.finditer(angry_emoji, input_text)]

    if detected:
        print(
            "The use of excessive emojis can be used by fake news outlets and sources to evoke negative emotions in "
            "and manipulate the reader.")
        print(
            "Serious outlets are not known to use them and thus you should exercise caution by checking against "
            "reputable and trustworthy sources.")
        print("List of detected angry emojis: {}\n".format(set(detected_angry_emojis)))
        if detected_consecutive:
            print("Total number of detected consecutive angry emojis: {}".format(number_of_detected_angry_emojis))
            print("Locations of detected consecutive angry emojis: {}\n".format(occurrences_indices_consecutive))
        if detected_total:
            print("Total number of detected angry emojis: {}".format(number_of_detected_angry_emojis))
            print("Locations of all detected angry emojis: {}".format(occurrences_indices_total))
    else:
        print("No detected angry emojis beyond set thresholds.")


check_for_angry_emojis("Hello World 😤😤😤😤")
