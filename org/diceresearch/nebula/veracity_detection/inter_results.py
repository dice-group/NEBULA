import argparse
import glob
import json
import logging
import sys
import time
from datetime import timedelta
from pathlib import Path

sys.path.insert(1, '../')
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
    parser.add_argument('--labels', help='Path where the source labels are')
    parser.add_argument('--save-fails', help='Path where to save the failed ids')
    return parser.parse_args()


args = parse_args()
CHECK_URL = args.endpoint + "/check?lang=en&text="
STATUS_URL = args.endpoint + "/rawstatus?id="


def main():
    fileConfig(settings.logging_config)

    source_labels = pd.read_csv(args.labels, header=0, index_col=0)['label'].to_dict()

    count = 0
    # read all from folder
    start = time.time()
    for file in glob.glob(args.path + '/*'):
        print(file)
        cur_label=source_labels[str(Path(file).stem)]
        with open(file) as fin, \
                open(args.save, 'a+', encoding='utf8') as save, \
                open(args.save_fails, 'a+', encoding='utf8') as fail_save:
            data = json.load(fin)
            for item in data:
                # submit request to check?lang=en&text=
                count += 1
                logging.info('Processed {0} articles'.format(count))
                article_text = item['content']
                if not article_text:
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

                    if status_id['status'] == 'DONE':
                        res = pd.read_json(status_id['wiseone'], orient='index')
                        small_result = ResponseStatus(
                            id=count,
                            article_id=item['id'],
                            stancescore=res['stance_score'].to_json(orient='values'),
                            wiseone=res['wise_score'].to_json(orient='values'),
                            label=cur_label,
                            status=status_id['status'])
                        save.write('{0}\n'.format(small_result.get_json()))
                    else:
                        f_result = ResponseStatus(
                            id=count,
                            request_id=status_id['id'],
                            article_id=item['id'],
                            status=status_id['status'])
                        fail_save.write('{0}\n'.format(f_result.get_json()))
                    logging.info('Processed {0} articles'.format(count))
                else:
                    f_result = ResponseStatus(
                        id=count,
                        article_id=item['id'])
                    fail_save.write('{0}\n'.format(f_result.get_json()))

    elapsed = (time.time() - start)
    logging.info('Took {0} for {1} articles'.format(timedelta(seconds=elapsed), count))


def check_status(id):
    response = requests.get(STATUS_URL + id).json()
    cur_status = response['status']
    if cur_status is None or cur_status == 'ONGOING':
        return False
    else:
        return response


if __name__ == '__main__':
    main()