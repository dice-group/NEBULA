import argparse
import glob
import json
import sys
import time
from datetime import timedelta
from tqdm import tqdm

sys.path.insert(0, '../')

import pandas as pd
import requests

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
CHECK_URL = args.endpoint + "/check"
STATUS_URL = args.endpoint + "/rawstatus?id="


def main():
    source_labels = pd.read_csv(args.labels, header=0, index_col=0)['label'].to_dict()

    # read saved ids, keep article_id
    article_ids = set()
    with open(args.save, 'r', encoding='utf8') as save:
        lines = save.readlines()
        for line in lines:
            a_id = json.loads(line)['article_id']
            article_ids.add(a_id)

    count = 0
    # read all from folder
    start = time.time()
    for file in tqdm(glob.glob(args.path + '/*')):
        with open(file) as fin, \
                open(args.save, 'a+', encoding='utf8') as save, \
                open(args.save_fails, 'a+', encoding='utf8') as fail_save:
            lines = fin.readlines()

            for item2 in lines:
                item = json.loads(item2)
                cur_label = source_labels.get(item['source'], -1)
                count += 1

                art_id = item['id']
                # check if we already processed it
                if art_id in article_ids:
                    print('Already seen this article {0}'.format(count))
                    continue

                article_text = item['new_content']
                # FIXME
                if not article_text:
                    continue
                if 'Disrupting the Borg is expensive and time consuming! Please help with a gift by clicking the button below.' in article_text:
                    continue
                if 'You have not enabled JavaScript!' in article_text:
                    continue
                start_article = time.time()
                data = {
                    'lang': 'en',
                    'text': article_text
                }
                req = requests.post(CHECK_URL, json=data)

                # read status
                if req.status_code == 200:
                    id = req.json()['id']

                    status_id = check_status(id)

                    # limit to 1 minute processing time
                    t_end = time.time() + 60
                    while status_id is False:
                        time.sleep(1)
                        status_id = check_status(id)
                        if time.time() > t_end:
                            break

                    if not status_id or status_id['status'] != 'DONE':
                        print('Problem with {0}th article'.format(count))
                        if status_id:
                            s = status_id['status']
                        else:
                            s = 'error'
                        f_result = ResponseStatus(
                            id=id,
                            article_id=item['id'],
                            status=s)
                        fail_save.write('{0}\n'.format(f_result.get_json()))

                    else:
                        res = pd.read_json(status_id['wiseone'], orient='index')
                        small_result = ResponseStatus(
                            id=id,
                            article_id=item['id'],
                            stancescore=res['stance_score'].to_json(orient='values'),
                            wiseone=res['wise_score'].to_json(orient='values'),
                            label=cur_label,
                            status=status_id['status'])
                        save.write('{0}\n'.format(small_result.get_json()))
                else:
                    f_result = ResponseStatus(
                        count=count,
                        article_id=item['id'],
                        http_code=req.status_code)
                    fail_save.write('{0}\n'.format(f_result.get_json()))
                article_elapsed = (time.time() - start_article)
                print('Processed {1}th in {0} seconds'.format(article_elapsed, count))
    elapsed = (time.time() - start)
    print('Took {0} for {1} articles'.format(timedelta(seconds=elapsed), count))


def check_status(id):
    response = requests.get(STATUS_URL + id).json()
    cur_status = response['status']
    if cur_status is None or cur_status == 'ONGOING':
        return False
    else:
        return response


if __name__ == '__main__':
    main()