import argparse
import glob
import logging
import sys
from logging.config import fileConfig

from utils.mp_handler import MPHandler

sys.path.insert(1, '../')
import settings
from utils.crawler_utils import crawl_file


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

    mp_handler = MPHandler(prog_args.np, prog_args.total)

    for i, file in enumerate(glob.glob(prog_args.path + '/*.json')):
        save_file = '{0}_{1}.jsonl'.format(prog_args.save, i)
        mp_handler.add_process(crawl_file, (file, save_file))

    mp_handler.close_pool()

    logging.info(mp_handler.error_counter)