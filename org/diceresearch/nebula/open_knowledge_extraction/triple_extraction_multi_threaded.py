import os
import threading
import re
import json

from transformers import pipeline
from nltk.tokenize import sent_tokenize
import nltk

data = []


class ArgumentParserMock:
    def __init__(self):
        self.args = {}

    def add_argument(self, name, default=None):
        self.args[name] = default

    def parse_args(self, args=[]):
        return self.args


# Create a lock
lock = threading.Lock()


def tokenize_into_sentences(paragraph):
    sentences = sent_tokenize(paragraph)
    return sentences


def read_file_chunk(start, end, input_file_path):
    # with open(file_path, 'rb') as file:
    #     file.seek(start)
    #     chunk = file.read(end - start)
    return data[start:end]


def add_backslash_to_quotes(input_string):
    input_string = repr(input_string)
    if input_string[0]!="\"" and input_string[-1]!="\"":
        input_string = input_string.replace('"', '\\"')
        input_string = "\""+input_string+"\""

    input_string = input_string.replace("\\\'","\'")
    input_string = input_string.replace("\\u200e", "\u200e")
    return input_string


def write_to_output(chunk, id_chunk, output_file1, output_file2):
    with open(output_file2, 'a') as file:
        for tpl in chunk.keys():
#             todo fix issue with tpl, it can come double quotes inside
            file.write("{" + (str(tpl)) + " , \"claim\":" + add_backslash_to_quotes(chunk[tpl]) + " , \"id\":" +
                       add_backslash_to_quotes(id_chunk[tpl]) + "}\n")
    with open(output_file1, 'a') as file:
        for tpl in chunk.keys():
            file.write(tpl + "\n")


def extract_triplets(text):
    triplets = []
    relation, subject, relation, object_ = '', '', '', ''
    text = text.strip()
    current = 'x'
    for token in text.replace("<s>", "").replace("<pad>", "").replace("</s>", "").split():
        if token == "<triplet>":
            current = 't'
            if relation != '':
                triplets.append(
                    {'head': f'"{subject.strip()}"', 'type': f'"{relation.strip()}"', 'tail': f'"{object_.strip()}"'})
                relation = ''
            subject = ''
        elif token == "<subj>":
            current = 's'
            if relation != '':
                triplets.append(
                    {'head': f'"{subject.strip()}"', 'type': f'"{relation.strip()}"', 'tail': f'"{object_.strip()}"'})
            object_ = ''
        elif token == "<obj>":
            current = 'o'
            relation = ''
        else:
            if current == 't':
                subject += ' ' + token
            elif current == 's':
                object_ += ' ' + token
            elif current == 'o':
                relation += ' ' + token
    if subject != '' and relation != '' and object_ != '':
        triplets.append(
            {'head': f'{add_backslash_to_quotes(subject.strip())}', 'type': f'{add_backslash_to_quotes(relation.strip())}', 'tail': f'{add_backslash_to_quotes(object_.strip())}'})
    return triplets


def process_chunk(start, end, input_file_path, args):
    chunk = read_file_chunk(start, end, input_file_path)

    dataset = args["--dataset_path"]
    dataset_type = args["--dataset_type"]
    output_file_triples, output_file_mapping = dataset + 'output/output_' + dataset_type + '/output_triples.jsonl', dataset + 'output/output_' + dataset_type + '/output_triples_mapping.jsonl'

    target_tag = args['--text_tag']
    target_tag_id = args['--text_tag_id']
    claim_type = args['--short_claims']

    # Find the corresponding text
    target_text = None
    relations = []
    ii = 0
    nltk.download('punkt')

    triplet_extractor = pipeline('text2text-generation', model='Babelscape/rebel-large',
                                 tokenizer='Babelscape/rebel-large')

    for tag_info in chunk:
        triple_calim_dict = dict()
        triple_id_dict = dict()
        print("start:" + str(start) + ",end:" + str(end) + ",current:" + str(ii) + "\n")
        if tag_info.get(target_tag):
            ii = ii + 1
            # if i < 2:
            #    continue
            target_text = tag_info.get(target_tag)
            target_text_id = tag_info.get(target_tag_id)
            content1 = target_text

            # for NELA .... it misses abriviations with dot "."
            # sentences = tokenize_into_sentences(content1)
            # for fever because it has only one sentence per claim most of the time
            if claim_type:
                sentences = [content1]
            else:
                sentences = tokenize_into_sentences(content1)

            # extract relations
            relations = []
            for idx, sentence in enumerate(sentences, 1):
                # We need to use the tokenizer manually since we need special tokens.
                extracted_text = triplet_extractor.tokenizer.batch_decode(
                    [triplet_extractor(sentence, return_tensors=True, return_text=False)[0]["generated_token_ids"]])
                # print(extracted_text[0])
                extracted_triplets = extract_triplets(extracted_text[0])
                # print(extracted_triplets)
                extracted_triplets1 = extracted_triplets

                tple_to_remove = []
                for tpl in extracted_triplets1:
                    i = 0
                    # check if the extracted triplet (subject and object) is not in the claim it should not be added
                    for key, value in tpl.items():
                        # i!=1 is to check if it's a relation then don't need to remove it
                        if i != 1:
                            if re.split(r'\W+', value)[0] not in sentence:
                                print("\n=======removed entity===========>>>>>>:-" + value)
                                tple_to_remove.append(tpl)
                                # print(str(i)+"\n")
                                break
                        i = i + 1

                if len(tple_to_remove) > 0:
                    for tt in tple_to_remove:
                        extracted_triplets.remove(tt)

                if len(extracted_triplets) > 0:
                    relations.append(extracted_triplets)

                for tpl in extracted_triplets:
                    line = ',\t'.join([f"\"{key}\": {value}" for key, value in tpl.items()])
                    triple_calim_dict[line] = str(sentence)
                    triple_id_dict[line] = str(target_text_id)

        with lock:
            write_to_output(triple_calim_dict, triple_id_dict, output_file_triples, output_file_mapping)


def argparse_default(description=None):
    # Create an ArgumentParser instance
    parser = ArgumentParserMock()

    parser.add_argument("--dataset_path",  default='/upb/users/u/uqudus/profiles/unix/cs/NEBULA/TripleExtraction/rebel_output/NELA/')
    # parser.add_argument("--sentence_length_threshold", default=50)
    # parser.add_argument("--text_tag", default='claim')
    parser.add_argument("--num_threads", default=2)


    # Paths.
    # parser.add_argument("--dataset_path",
    #                     default='/home/uqudus/PycharmProjects/TripleExtraction/data/nela/')
    # parser.add_argument("--dataset_path",default='/home/uqudus/PycharmProjects/TripleExtraction/data/nela/')

    parser.add_argument("--dataset_file_name", default='results2.jsonl') # for fever 'fever_paper_' + 'dataset_type(tain or test or dev)' + '.jsonl'
    parser.add_argument("--sentence_length_threshold", default=50)
    parser.add_argument("--text_tag", default='claim')
    parser.add_argument("--text_tag_id", default='id')
    parser.add_argument("--short_claims", default=False)
    parser.add_argument("--dataset_type", default='train')

    if description is None:
        return parser.parse_args()
    else:
        return parser.parse_args(description)


def read_processed_claims(path=None):
    # Define a list to store the claims
    claims = []

    # Assuming you have a file named 'claims.jsonl'
    with open(path, 'r') as file:
        for line in file:
            # Load each line as a JSON object
            print(line)
            line = "{\"head\": " + add_backslash_to_quotes(str(line.split("\"head\": \"")[1].split("\",	\"type\":")[0]))
            + ",	\"type\": " + add_backslash_to_quotes(str(line.split("\",	\"type\": \"")[1].split("\",	\"tail\": \"")[0]))
            + ",	\"tail\": " + add_backslash_to_quotes(str(line.split("\",	\"tail\": \"")[1].split("\" , \"claim\":\"")[0]))
            + " , \"claim\":" + str(add_backslash_to_quotes(str(line.split(", \"claim\":\"")[1].split("\" , \"id\":\"")[0])))
            + " , \"id\":" + str(add_backslash_to_quotes(str(line.split(", \"id\":\"")[1].split("\"}")[0]))) + "}"
            claim_data = json.loads(line.strip())

            # Extract and store the 'claim' value
            claim = claim_data.get('claim')
            print(claim)

            # Check if 'claim' exists and is not empty
            if claim:
                claims.append(claim)

    # Now 'claims' list contains all the claims from the file
    return claims


def main():
    test = True  # test_output/
    args = argparse_default()
    dataset = args["--dataset_path"]
    dataset_file_name = args["--dataset_file_name"]
    dataset_type = args["--dataset_type"]
    input_file_path = dataset + dataset_file_name
    # output_file_triples = dataset + 'output/output_' + dataset_type + '/output_triples.jsonl'
    output_file_mapping = dataset + 'output/output_' + dataset_type + '/output_triples_mapping.jsonl'

    # TODO: Check if file does not exist create it!!
    claims = list(set(read_processed_claims(output_file_mapping)))
    print("processed claims:" + str(len(claims)))


    # Reading the output file if already some data exists.
    with open(input_file_path, 'r') as file:
        for line in file:
            try:
                json_object = json.loads(line)
                # Process the JSON object
            except json.decoder.JSONDecodeError as e:
                print(f"Error decoding JSON on line {line}: {e}")
            # print(json_object['claim'])
            if json_object['claim'] not in claims:
                data.append(json_object)

    num_threads = args['--num_threads']  # Adjust the number of threads as needed

    # Get the size of the file
    file_size = len(data)

    # Calculate chunk size for each thread
    chunk_size = len(data) // num_threads
    print("chunksize:" + str(chunk_size))
    # exit(0)
    # Create threads
    threads = []
    for i in range(num_threads):
        start = i * chunk_size
        end = (i + 1) * chunk_size if i < num_threads - 1 else file_size
        thread = threading.Thread(target=process_chunk, args=(start, end, input_file_path, args))
        threads.append(thread)

    # Start threads
    for thread in threads:
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()


if __name__ == '__main__':
    main()

