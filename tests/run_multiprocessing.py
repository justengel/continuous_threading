from __future__ import print_function

import time
import collections
import multiprocessing as mp
from functools import wraps


def count_items(counter, key='value', sleep=None, start_time=None):
    if start_time is not None:
        print('Count {:.02f}(s): {} = {}'.format(time.time() - start_time, key, counter[key]))
    else:
        print('Count: {} = {}'.format(key, counter[key]))
    counter[key] += 1
    try:
        time.sleep(sleep)
    except (ValueError, TypeError):
        pass


def _memoize(f):
    memo = {}
    @wraps(f)
    def wrapper(n, *args, **kwargs):
        try:
            return memo[n]  # Find already calculated value in dict
        except KeyError:
            value = f(n, *args, **kwargs)  # Calculate new
            memo[n] = value  # Save result for fast recall later.
            return value
    return wrapper


@_memoize  # Need this for speed
def fibonacci(n, is_last=True):
    if n <= 1:
        value = n
    else:
        value = fibonacci(n-1, is_last=False) + fibonacci(n-2, is_last=False)

    if is_last:
        print('Fibonacci N={}:'.format(n), value)
    return value


# ========== Testing Functions ==========
def run_normal(test_join=True):
    from continuous_threading.safe_multiprocessing import Process

    # proc = mp.Process(target=count_items, args=(collections.Counter(), 'normal'))
    # proc.start()

    proc = Process(target=count_items, args=(collections.Counter(), 'normal'))
    proc.start()

    print('MAIN:', proc)
    time.sleep(1)

    if test_join:
        proc.join()


def run_contextmanager(test_join=None):
    from continuous_threading.safe_multiprocessing import Process

    # Normal multiprocessing Process cannot use context managers
    # with mp.Process(target=count_items, args=(collections.Counter(), 'normal')) as proc:
    #     print(proc)

    with Process(target=count_items, args=(collections.Counter(), 'normal')) as proc:
        print('MAIN:', proc)

    # joins the Process at the end of the with context manager.


def run_continuous(test_join=True):
    from continuous_threading.safe_multiprocessing import ContinuousProcess

    proc = ContinuousProcess(target=count_items, args=(collections.Counter(), 'continuous'),
                             kwargs={'sleep': 0.1})
    proc.start()

    time.sleep(5)

    print('sleep finished look at printed counter to verify that it ran continuously.')
    if test_join:
        proc.join()


def run_pausable(test_join=True):
    from continuous_threading.safe_multiprocessing import PausableProcess

    proc = PausableProcess(target=count_items, args=(collections.Counter(), 'pausable'),
                           kwargs={'sleep': 0.1})
    proc.start()

    time.sleep(3)
    print('sleep finished look at printed counter to verify that it ran continuously.')

    print('stopping')
    proc.stop()
    print('stopped')

    time.sleep(1)
    print('sleep finished look at printed counter to verify that it paused.')
    time.sleep(1)

    print('starting again')
    proc.start()
    time.sleep(1)

    if test_join:
        proc.join()


def run_periodic(test_join=True):
    from continuous_threading.safe_multiprocessing import PeriodicProcess

    proc = PeriodicProcess(0.5, target=count_items, args=(collections.Counter(), 'periodic'),
                           kwargs={'start_time': time.time()})
    proc.start()

    time.sleep(3)

    if test_join:
        proc.join()


def run_operations(test_join=True):
    from continuous_threading.safe_multiprocessing import OperationProcess

    proc = OperationProcess(target=fibonacci)
    proc.start()

    # Add data after the process started
    for i in range(101):
        proc.add_data(i)

    if test_join:
        proc.join()


def run_operations_timeout_internal(test_join=True):
    from continuous_threading.safe_multiprocessing import OperationProcess

    proc = OperationProcess(target=fibonacci)
    proc.start()

    # Add data after the process started
    for i in range(101):
        if i == 50:
            proc.timeout = 5
        proc.add_data(i)

    if test_join:
        proc.join()


# ========== Command Setup (Must be defined at the page level for pickling) ==========
class MyObj(object):
    def __init__(self, x=0, y=0):
        self._x = x
        self._y = y

    def set_x(self, x):
        self._x = x

    def set_y(self, y):
        self._y = y

    def print_obj(self, msg=''):
        print(self._x, self._y, msg)

    def expect(self, x, y, msg=''):
        assert self._x == x, 'X value {} does not match expected {}'.format(self._x, x)
        assert self._y == y, 'Y value {} does not match expected {}'.format(self._y, y)
        self.print_obj(msg=msg)


def run_command(test_join=True):
    from continuous_threading.safe_multiprocessing import CommandProcess

    obj1 = MyObj()
    obj2 = MyObj()

    proc = CommandProcess(target=obj1)
    proc.daemon = True
    proc.start()

    # Send a command obj1
    print('Main Obj1')  # Note: this prints way earlier
    proc.send_cmd('print_obj', msg="Obj1")
    proc.send_cmd('set_x', 1)
    proc.send_cmd('print_obj')
    proc.send_cmd('set_y', 2)
    proc.send_cmd('print_obj')
    proc.send_cmd('expect', 1, 2, msg='Obj1 expected (1,2)')

    # Send a command obj2
    print('Main Obj2')  # Note: this prints way earlier
    proc.obj = obj2
    proc.send_cmd('print_obj', msg="Obj2")
    proc.send_cmd('set_x', 2)
    proc.send_cmd('print_obj')
    proc.send_cmd('set_y', 4)
    proc.send_cmd('print_obj')
    proc.send_cmd('expect', 2, 4, msg='Obj2 expected (2,4)')

    # *** IGNORE COMMENTS: I implemented a caching system to save object state. ***
    # Change back to obj1 (Remember this obj has attr 0,0 and when sent to other process will be a new obj 0,0).
    # Cannot remember objects unless cached (saved in a dict) on the other process. id in process will be different.
    #  ... NVM I'll just cache the obj value.
    print('Main Obj1 again (Cached)')  # Note: this prints way earlier
    proc.obj = obj1
    proc.send_cmd('expect', 1, 2, msg="Obj1 Again (Cached)")
    proc.send_cmd('set_x', 3)
    proc.send_cmd('print_obj')
    proc.send_cmd('set_y', 5)
    proc.send_cmd('print_obj')
    proc.send_cmd('expect', 3, 5, msg='Obj1 Again expected (3,5)')

    if test_join:
        proc.join()


if __name__ == '__main__':
    run_normal()
    run_contextmanager()

    run_continuous()
    run_continuous(test_join=False)

    run_pausable()
    run_pausable(test_join=False)

    run_periodic()
    run_periodic(test_join=False)

    run_operations()
    run_operations(test_join=False)
    run_operations_timeout_internal()
    run_operations_timeout_internal(test_join=False)

    run_command()
    run_command(test_join=False)
