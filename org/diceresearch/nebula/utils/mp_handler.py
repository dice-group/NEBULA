from collections import Counter
import multiprocessing as mp

from tqdm import tqdm


class MPHandler(object):
    def __init__(self, num_proc, total=None):
        # create pool and manager
        self.pool = mp.Pool(processes=num_proc)

        # manager
        self.mp_man = mp.Manager()

        # collects errors that occurred inside each thread
        self.error_counter = Counter()

        # create progress bar process if total is known
        if total is not None:
            self.bar_queue = self.mp_man.Queue()
            self.bar_process = mp.Process(target=self.update_bar, args=(total,), daemon=True)
            self.bar_process.start()

    def collect_result(self, result):
        # updates errors occurring in threads with frequency
        self.error_counter.update(result)

    def add_process(self, function, args):
        if self.bar_queue:
            self.pool.apply_async(function, args=args + (self.bar_queue,), callback=self.collect_result)
        else:
            self.pool.apply_async(function, args=args, callback=self.collect_result)

    def close_pool(self):
        self.pool.close()
        self.pool.join()

    def update_bar(self, total):
        pbar = tqdm(total=total, position=0, leave=True)
        while True:
            x = self.bar_queue.get()
            pbar.update(x)