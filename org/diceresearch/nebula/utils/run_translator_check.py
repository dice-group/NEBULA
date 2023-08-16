import argparse
import glob
import json
from logging.config import fileConfig

import requests
import spacy
from ftlangdetect import detect
from tqdm import tqdm

import settings

model = spacy.load('xx_sent_ud_sm')


def parse_args():
    """
    Parse program arguments
    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', required=True, help='Dataset folder')
    parser.add_argument('--save', required=True, help='Path where to save the results')
    return parser.parse_args()


def main():
    fileConfig(settings.logging_config)
    prog_args = parse_args()
    files = []
    bad_json = []
    url = 'http://neamt1.cs.upb.de:6100/custom-pipeline'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    for file in tqdm(glob.glob(prog_args.path + '**/*.json', recursive=True)):
        with open(file, encoding='utf8') as json_data:
            try:
                # load json and fix if the unescaped quotes if needed
                json_file = sanitize_unescaped_quotes_and_load_json_str(json_data.read())
            except Exception as e:
                bad_json.append(json_data.read())
                continue

        translated_text = json_file['maintext']
        original_text = json_file['originaltext']
        result = detect(text=translated_text, low_memory=False)

        # if the translation didn't happen, flag it for translation
        if result['lang'] != 'en':
            # logging.info('Rejected because of language result {}'.format(result))
            files.append(file)
            # translate it again and overwrite file to file
            redo_fail(json_file, file, url, headers, original_text)
            continue

        # check the difference in sentences instead
        # if it's not similar, flag it for translation
        tr_no_sent = len(list(model(translated_text).sents))
        og_no_sent = len(list(model(original_text).sents))
        diff = og_no_sent - tr_no_sent
        if diff > 1:
            # logging.info('Rejected because of sentence difference {}'.format(diff))
            files.append(file)
            # translate it again and overwrite file to file
            redo_fail(json_file, file, url, headers, original_text)
            continue


def redo_fail(json_file, file, url, headers, original_text):
    # translate it again
    json_file['maintext'] = post_neamt(url, headers, original_text)
    # overwrite the file
    with open(file, 'w', encoding='utf8') as p:
        p.write(json.dumps(json_file, indent=3))


def post_neamt(url, headers, query):
    encode = {'components': 'mbart_mt', 'lang': 'de', 'query': query}
    return requests.post(url, data=encode, headers=headers).content.decode('utf-8')


def sanitize_unescaped_quotes_and_load_json_str(s: str, strict=False) -> dict:  # type: ignore
    """
    Taken from https://kevinquinn.fun/blog/a-real-world-solution-to-escape-embedded-double-quotes-in-json/
    It escapes double quotes inside double quotes
    """
    # one thing this doesn't handle, is if the unescaped text includes valid JSON - then you're just out of luck
    js_str = s
    prev_pos = -1
    curr_pos = 0
    while curr_pos > prev_pos:
        # after while check, move marker before we overwrite it
        prev_pos = curr_pos
        try:
            return json.loads(js_str, strict=strict)
        except json.JSONDecodeError as err:
            curr_pos = err.pos
            if curr_pos <= prev_pos:
                # previous change didn't make progress, so error
                raise err

            # find the previous " before e.pos
            prev_quote_index = js_str.rfind('"', 0, curr_pos)
            # escape it to \"
            js_str = js_str[:prev_quote_index] + "\\" + js_str[prev_quote_index:]


if __name__ == '__main__':
    main()