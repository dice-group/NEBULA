import argparse
import glob
import logging
import multiprocessing as mp
import sys
from collections import Counter
from logging.config import fileConfig
from multiprocessing import Pool

sys.path.insert(1, '../')
import settings
from utils.crawler_utils import crawl_file
import utils.crawler_utils as c_util


def parse_args():
    """
    Parse program arguments
    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', required=True, help='Dataset folder')
    parser.add_argument('--save', required=True, help='Path where to save the results')
    parser.add_argument('--np', default=4, help='Number of processors')
    parser.add_argument('--total', default=1779127, type=int, help='Total number of articles')
    return parser.parse_args()


if __name__ == '__main__':
    fileConfig(settings.logging_config)
    prog_args = parse_args()

    # create pool and manager
    pool = Pool(processes=prog_args.np)

    # collects errors that occurred inside each thread
    error_counter = Counter()


    def collect_result(result):
        error_counter.update(result)


    # create progress bar process
    mp_man = mp.Manager()
    bar_queue = mp_man.Queue()
    bar_process = mp.Process(target=c_util.update_bar, args=(bar_queue, prog_args.total,), daemon=True)
    bar_process.start()

    for i, file in enumerate(glob.glob(prog_args.path + '/*.json')):
        save_file = '{0}_{1}.jsonl'.format(prog_args.save, i)
        proc = pool.apply_async(crawl_file,
                                args=(file, save_file, bar_queue),
                                callback=collect_result)

    # join all processes and get results
    pool.close()
    pool.join()

    logging.info(error_counter)