# -*- coding: utf-8 -*-
import os
import random
import sys
import threading
import time

try:
    import Queue    # Python2
except ImportError:
    import queue as Queue   # Python3

class ThreadPool(object):
    def __init__(self, num_workers=10):
        self.num_workers = num_workers
        self.job_queue = Queue.Queue()
        self.result_queue = Queue.Queue()
        self.workers = []

        # init thread pool
        self.init_pool()

    def init_pool(self):
        for i in range(self.num_workers):
            self.workers.append(WorkerThread(self.job_queue, self.result_queue, is_core=True))

    def add_job(self, job):
        self.job_queue.put(job)

    def add_workers(self, num_add_workers):
        for i in range(num_add_workers):
            self.workers.append(WorkerThread(self.job_queue, self.result_queue))

    def add_core_workers(self, num_add_core_workers):
        for i in range(num_add_core_workers):
            self.workers.append(WorkerThread(self.job_queue, self.result_queue, is_core=True))

    def dismiss_workers(self, num_dismissed_workers):
        common_threads = filter(lambda t: not t.is_core, self.workers)
        if len(common_threads) < num_dismissed_workers:
            print 'No enough no-core thread for delete.'
            os._exit(0)
        else:
            for i in range(num_dismissed_workers):
                del_thread = common_threads.pop()
                self.workers.remove(del_thread)
                del_thread.kill = True

    def destroy_pool(self):
        for i in self.workers:
            i.setDaemon(True)


class WorkerThread(threading.Thread):
    def __init__(self, job_queue, res_queue, is_core=False):
        super(WorkerThread, self).__init__()
        self.job_queue = job_queue
        self.res_queue = res_queue
        self.is_core = is_core
        self.kill = False

        # start the thread
        self.start()

    def run(self):
        while True:
            if self.kill:   # 主动结束非核心线程
                return True
            try:
                job = self.job_queue.get()
            except Queue.Empty:
                continue    # 继续请求获得任务
            job.execute()
            self.res_queue.put(job)
            self.job_queue.task_done()

            if not self.is_core:    # 如果是非核心线程则结束线程
                return True

class ThreadJob(object):
    def __init__(self, exec_func, args=None, kwds=None, callback=None):
        self.exec_func = exec_func
        self.return_value = None
        self.callback = callback #Yet to be done
        self.exception = False
        self.args = args or ()
        self.kwargs = kwds or {}

    def execute(self):
        try:
            self.return_value = self.exec_func(*self.args, **self.kwargs)
        except Exception as e:
            print 'There is an exception in execute job.'
            self.exception = e


if __name__ == '__main__':
    def do_something(x, y, testx=None, testy=None):
        time.sleep(random.randint(1, 2))
        print 'Thread id is %s and params are x=%s, y=%s, testx=%s, testy=%s\n' % \
            (threading.current_thread().ident, x, y, testx, testy)

    main = ThreadPool(2)
    for i in range(5):
        args = ('formalx', 'formaly')
        kwargs = {'testx': 'keywordx', 'testy': 'keywordy'}
        job = ThreadJob(do_something, args, kwargs)
        main.add_job(job)

    time.sleep(5)

    main.add_workers(20)
    for i in range(5):
        args = ('formalx', 'formaly')
        kwargs = {'testx': 'keywordx', 'testy': 'keywordy'}
        job = ThreadJob(do_something, args, kwargs)
        main.add_job(job)

    time.sleep(5)
    
    # main.dismiss_workers(5)
    main.dismiss_workers(100)
    for i in range(5):
        args = ('formalx', 'formaly')
        kwargs = {'testx': 'keywordx', 'testy': 'keywordy'}
        job = ThreadJob(do_something, args, kwargs)
        main.add_job(job)