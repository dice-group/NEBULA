"""
Hate speech

Model is specialized to detect hate speech against women and immigrants. Latest version.
https://huggingface.co/cardiffnlp/twitter-roberta-base-hate-latest
"""
import tweetnlp

def _load_settings_from_config(config: tomlkit.TOMLDocument) -> str:
    try:
        hate_speech_config = config["topical"]["hate_speech"]

        display_message_warning: str = hate_speech_config["display_message_warning"]
        if not isinstance(display_message_warning, str):
            raise ValueError(
                "Provided setting for hate_speech warning message 'display_message_warning' is not "
                "correctly defined. Are you sure it is a string?"
            )

        return display_message_warning
    except KeyError as config_not_found_err:
        logging.error(
            "Incorrect hate_speech configuration! Check that all required settings are defined."
        )
        raise config_not_found_err


def check_for_hate_speech(
    input_text: str, config: tomlkit.TOMLDocument
) -> Union[bool, Dict[str, Union[str, List[int]]]]:
    display_message_warning: str = _load_settings_from_config(config)
    
    text: List[str] = input_text                 #ToDo: Input Text auf Englisch ändern
    
    # Initialize list to store position (entire text)
    hate_speech_positions: List[int] = []         #ToDo: If hate speech is recognised, all positions of the entire text in original language must be saved in list 

    
    model_hate = tweetnlp.load_model('hate')
    results_hatespeech = model_hate.predict(text, return_probability=True)

    for idx in enumerate(text):
        if results_hatespeech["label"] == "HATE": # Check if the predicted label is "hate_speech" before printing
            hate_speech_positions.append(list(range(len(input_text))))       #ToDo: If hate speech is recognised, all positions of the entire text in original language must be saved in list - ...like that?

 # Print positions of hate speech (entire text, because of transformer model classification)
    if hate_speech_positions:
        results = {
            "display_message": display_message_warning,
            "hate_speech_positions": hate_speech_positions,
        }
        logging.info(display_message_warning)
        logging.info(
            "Excessive capitalisation is detected in the following positions:\n"
        )
        for position in allcaps_positions:
            logging.info(f"Position: {position}")

        return results
    else:
        logging.info("No hate speech been detected in the text.")
        return False
