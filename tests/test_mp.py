import time
import multiprocessing as mp
from continuous_threading import PeriodicProcess


def log_time(queue):
    queue.put(time.time())


def test_periodic_accuracy(periodic_class=None):
    if periodic_class is None:
        periodic_class = PeriodicProcess

    period = 0.001  # 0.0001 NOT ACCURATE ON WINDOWS
    que = mp.Queue()
    time_list = []

    # Cannot pickle local function variables
    # def log_time(queue):
    #     queue.put(time.time())

    proc = periodic_class(period, target=log_time, args=(que,))
    proc.start()

    time.sleep(4)
    proc.join()

    for i in range(que.qsize()):
        time_list.append(que.get())

    # Compare times
    diff = [(time_list[i+1] - time_list[i]) - period for i in range(0, len(time_list)-1, 2)]
    # print('Time offsets:', diff)
    print(periodic_class.__name__, 'Average time offset:', sum(diff)/len(diff),
          'The period was ', period,
          'The number of occurrences was', len(diff))


if __name__ == '__main__':
    test_periodic_accuracy()
