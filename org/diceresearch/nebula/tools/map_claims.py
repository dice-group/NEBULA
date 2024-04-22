import json
from nltk import sent_tokenize
import pandas as pd
from tqdm import tqdm


def read_jsonl(file_path):
    """
    Read a JSONL file and return a list of dictionaries.
    """
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            try:
                data.append(json.loads(line))
            except:
                continue

        # data = [json.loads(line) for line in file]
    return data


def get_sentence_index(text, claim):
    """
    Use NLTK sentence segmentation to get the sentence index of the claim in the text.
    """
    sentences = sent_tokenize(text)
    for i, sentence in enumerate(sentences):
        if claim in sentence:
            return i
    return None


def fix_capitalization(text):
    import re
    usr_str, n = re.subn("(^|[.])\s*[a-z]", lambda x: x.group(0).upper(), text)
    return usr_str


# read jsonl file with triples
# id in key "id", claim in key "claim" and triple in key "triple"
# triples = read_jsonl("testt.jsonl")

# read jsonl file with original dataset
# id in key "article_id", text in key "article_text", claims in "wise_check"
original = read_jsonl("nela_10_train.jsonl")


# read jsonl file with coreferenced dataset
# id in key "id", text in key "coreferenced_text"
coref = read_jsonl("nela_10_train_coref.jsonl")


# IDs from original
original_ids = [original_entry["article_id"] for original_entry in original]

# Create a list to store dictionaries with claim information
claim_data = []

# keep track of mismatches
count = 0
claim_count = 0

# Process each id in the original dataset
for id in tqdm(original_ids):
    # Find the corresponding entry in the original dataset
    original_entry = next(entry for entry in original if entry["article_id"] == id)
    coref_entry = next(entry for entry in coref if entry["id"] == id)

    # Extract information from the original entry
    original_text = original_entry["article_text"]
    wise_check_claims = original_entry["wise_check"]

    # Get coreferenced text
    coref_text = coref_entry["coreferenced_text"]

    # Sentence tokenize original and coref
    original_sentences = sent_tokenize(original_text)
    coref_sentences = sent_tokenize(coref_text)

    if len(coref_sentences) != len(original_sentences):
        # try again on coref
        coref_text = fix_capitalization(coref_text)
        coref_sentences = sent_tokenize(coref_text)

    if len(coref_sentences) != len(original_sentences):
        count += 1
        print("Text tokenization doesn't match {}".format(count))
        continue


    # Process each claim in the wise_check_claims
    for claim_text, _ in wise_check_claims.items():
        # find sentence index of claim_text in coref_sentences
        try:
            sentence_index = original_sentences.index(claim_text)
        except ValueError:
            sentence_index = None

        if sentence_index is not None and 0 <= sentence_index < len(coref_sentences):
            # use sentence index from previous step to retrieve corresponding original sentence
            original_claim = original_sentences[sentence_index]
            coref_claim = coref_sentences[sentence_index]

            # Add claim information to the list
            claim_data.append({
                "article_id": id,
                "original_sentence": original_claim,
                "coref_sentence": coref_claim
            })
        else:
            claim_count += 1
            print("Could not find individual claim {}".format(claim_count))

# write to file
df = pd.DataFrame(claim_data)
output_path = "nela_10_train_map.jsonl"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(df.to_json(orient='records', lines=True, force_ascii=False))
