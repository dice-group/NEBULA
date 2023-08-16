import argparse
import glob
import json
import logging
import time
from logging.config import fileConfig

import pandas as pd
import requests

import settings
from data.results import ResponseStatus


def parse_args():
    """
    Parse program arguments
    :return:
    """
    parser = argparse.ArgumentParser(prog='Get intermediate results')
    parser.add_argument('--endpoint', help='Service endpoint')
    parser.add_argument('--path', help='Dataset folder')
    parser.add_argument('--save', help='Path where to save the results')
    # parser.add_argument('--save-fails', help='Path where to save the failed ids')
    return parser.parse_args()


args = parse_args()
CHECK_URL = args.endpoint + "/check?lang=en&text="
STATUS_URL = args.endpoint + "/rawstatus?id="


def main():
    fileConfig(settings.logging_config)

    count = 0
    # read all from folder
    for file in glob.glob(args.path + '/*'):
        print(file)
        with open(file) as fin:
            data = json.load(fin)
            for item in data:
                # submit request to check?lang=en&text=
                article_text = item['content']
                if article_text is None:
                    continue
                check_text = CHECK_URL + article_text

                req = requests.get(check_text)

                # read status
                if req.status_code == 200:
                    id = req.json()['id']

                    status_id = check_status(id)
                    while status_id is False:
                        time.sleep(1)
                        status_id = check_status(id)

                    with open(args.save, 'a+', encoding='utf8') as f:
                        small_result = ResponseStatus(
                            id=status_id['id'],
                            wiseone=pd.read_json(status_id['wiseone'], orient='index')['wise_score'].to_json(orient='values'),
                            status=status_id['status'])
                        f.write('{0}\n'.format(small_result.get_json()))

                    count += 1
                    if count % 100 == 0:
                        logging.info('Processed {0} articles'.format(count))


def check_status(id):
    response = requests.get(STATUS_URL + id).json()
    cur_status = response['status']
    if cur_status is None or cur_status == 'ONGOING':
        return False
    else:
        return response


if __name__ == '__main__':
    main()