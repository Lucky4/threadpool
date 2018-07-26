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
    def __init__(self):
        self.num_workers = 10               # 线程池默认核心线程数
        self.max_thread_num = 50            # 线程池最大线程数
        self.thread_worker_high_ratio = 3   # 线程数与任务峰值比例
        self.thread_worker_low_ratio = 1    # 任务数与线程数低谷比例
        self.manage_adjust_interval = 5     # 管理线程动态调节时间间隔（s）
        self.workers = []
        self.job_queue = Queue.Queue()
        self.result_queue = Queue.Queue() # yet to be done

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
        self.job_queue.join()
        os._exit(0)

    def check(self):
        print '------Checking the thread worker ratio------'
        workers_length = len(self.workers)
        thread_worker_ratio = self.job_queue.qsize() / workers_length

        if thread_worker_ratio > self.thread_worker_high_ratio:
            if workers_length < self.max_thread_num:
                print 'Thread worker high ratio, add one thread.'
                self.add_workers(1)
        elif thread_worker_ratio < self.thread_worker_low_ratio:
            if workers_length > self.num_workers:
                print 'Thread worker low ratio, delete one thread.'
                self.dismiss_workers(1)


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

            if not self.is_core:    # 如果是非核心线程执行完任务后则结束线程
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

    main = ThreadPool()

    # 模拟任务数量增加，线程池动态的增加线程
    while True:
        time.sleep(1)
        for i in range(400):
            args = ('formalx', 'formaly')
            kwargs = {'testx': 'keywordx', 'testy': 'keywordy'}
            job = ThreadJob(do_something, args, kwargs)
            main.add_job(job)
        main.check()

    main.destroy_pool()