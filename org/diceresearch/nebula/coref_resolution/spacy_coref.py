import threading

import spacy

# Load spaCy model and add Coreferee
import orchestrator
import settings
from utils.database_utils import update_database, log_exception

nlp = spacy.load('en_core_web_trf')
nlp.add_pipe('coreferee')


def replace_corefs(text, identifier):
    """
    Finds and replaces the coreferences by the most representational mention
    :param text: Input text
    :param identifier: ID
    :return: The coreferenced text
    """
    try:
        # Process the text
        doc = nlp(text)

        # Replace coreferences
        replacements = []
        for chain in doc._.coref_chains:
            ind_rep_mention = chain[chain.most_specific_mention_index].root_index
            representative_mention = doc[ind_rep_mention].text
            for mention in chain:
                if mention.root_index is ind_rep_mention:
                    continue
                mention_span = doc[min(mention.token_indexes):max(mention.token_indexes) + 1]
                start, end = mention_span.start_char, mention_span.end_char
                replacements.append((start, end, representative_mention))

        # Perform replacements from the end of the text to the start
        replacements.sort(key=lambda x: x[0], reverse=True)
        for start, end, rep_text in replacements:
            text = text[:start] + rep_text + text[end:]

        # save the result in database
        update_database(settings.results_coref_column_name, settings.results_coref_column_status, text, identifier)

        # go next level
        orchestrator.goNextLevel(identifier)
    except Exception as e:
        log_exception(e, identifier)

