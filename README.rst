====================
continuous_threading
====================

This library provides several classes to help manage threads that run continuously.

There are some problems with threads runing continuously in a loop. Calculation threads are greedy and keep running 
which starves other threads. Another problem is if you don't exit an infinite loop in a thread it may keep running 
after python has tried to exit. Daemon threads will close, but resources/variables may not be cleaned up properly. 
Mostly, I needed to finish writing data to a file before the thread closed. This library aims to solve those problems.

This library provides 4 main thread utilities:
  * shutdown - Call `join(timeout)` on every non-daemon thread that is active.
  * Thread - threading with context manager support
  * ContinuousThread - Run a function continuously in a loop (It is suggested sleep is called periodically if no I/O)
  * PausableThread - Continuous thread that can be stopped and started again.
  * OperationThread - Thread that will run a calculation in a separate thread with different data.
  * PeriodicThread - Thread that runs a function periodically at a given interval.


Shutdown Update
---------------

Noticed issue with Python 3.8 on Windows. Python's threading._shutdown method is never called or hangs before exit.
This library is dependent on that function. I added a shutdown method that can be added to the end of your code.
This will ensure that `join()` is called on all of the non-daemon threads.

This issue may have been caused by me adding a `_stop` method to the Thread class. Python's threading library may
require the use of the `_stop` function. I removed this method and everything seems to work, so this may not be an issue
anymore.


.. code-block :: python

    import time
    import continuous_threading

    def do_something():
        print('hello')
        time.sleep(1)

    th = continuous_threading.PausableThread(target=do_something)
    th.start()

    time.sleep(10)

    continuous_threading.shutdown()


Thread context manager
----------------------
This library turns threads into a context manager which automatically starts and stops threads.

.. code-block:: python

    import continuous_threading

    thread_success = [False]

    def do_something():
        print('here')
        thread_success[0] = True


    with continuous_threading.Thread(target=do_something):
        print('in context')

    assert thread_success[0] is True


ContinuousThread
----------------
The ContinuousThread is a simple thread in an infinite while loop. The while loop keeps looping while the thread 
alive Event is set. Call `thread.stop()`, `thread.close()`, or `thread.join()` to stop the thread. The thread should 
also stop automatically when the python program is exiting/closing.

.. code-block:: python

    import continuous_threading

    class CountingThread(continuous_threading.ContinuousThread):
        def __init__(self):
            super().__init__()
            self.counter = 0

        def _run(self):
            self.counter += 1


    with CountingThread() as th:
        print('in context')

    assert th.counter > 0
    print("Simple context manager print caused %d thread iterations" % th.counter)


Example of start and stop methods.
.. code-block:: python

    import time
    import continuous_threading

    class CountingThread(continuous_threading.ContinuousThread):
        def __init__(self):
            super().__init__()
            self.counter = 0

        def _run(self):
            self.counter += 1

    th = CountingThread()
    th.start()
    time.sleep(0.1)
    th.stop()  # or th.close() or th.join()

    assert th.counter > 0
    print("Simple context manager print caused %d thread iterations" % th.counter)


PausableThread
--------------
A continuous thread that can be stopped and started again.

.. code-block:: python

    import time
    import continuous_threading


    counter = [0]

    def inc_counter():
        counter[0] += 1

    th = continuous_threading.PausableThread(target=inc_counter)

    th.start()
    time.sleep(0.1)

    th.stop()
    time.sleep(0.1)

    value = counter[0]
    assert value > 0

    time.sleep(0.1)
    assert value == counter[0]

    th.start()
    time.sleep(0.1)
    assert counter[0] > value


Again this can be used as a context manager.
.. code-block:: python

    import time
    import continuous_threading

    class CountingThread(continuous_threading.PausableThread):
        def __init__(self):
            super().__init__()
            self.counter = 0

        def _run(self):
            self.counter += 1

    with CountingThread() as th:
        time.sleep(0.1)
        th.stop()
        value = th.counter
        assert value > 0

        time.sleep(0.1)
        assert value == th.counter

        th.start()
        time.sleep(0.1)
        assert th.counter > value


PeriodicThread
--------------

Run a function periodically.

.. code-block:: python

    import time
    import continuous_threading


    time_list = []

    def save_time():
        time_list.append(time.time())

    th = continuous_threading.PeriodicThread(0.5, save_time)
    th.start()

    time.sleep(4)
    th.join()

    print(time_list)


OperationThread
---------------
Add data to a queue which will be operated on in a separate thread.

.. code-block:: python

    import time
    import continuous_threading


    values = []

    def run_calculation(data1, data2):
        values.append(data1 + data2)

    th = continuous_threading.OperationThread(target=run_calculation)
    th.start()
    th.add_data(1, 1)
    time.sleep(0.1)

    assert len(values) > 0
    assert values[0] == 2

    th.add_data(2, 2)
    th.add_data(3, 3)
    th.add_data(4, 4)
    th.add_data(5, 5)

    time.sleep(0.1)
    assert values == [2, 4, 6, 8, 10]


Process
=======

All of the above Thread classes can also be used as a separate Process:
  * Process
  * ContinuousProcess
  * PausableProcess
  * PeriodicProcess
  * OperationProcess
  * CommandProcess


CommandProcess
--------------

Run functions and commands on an object that lives in a different process.

.. code-block:: python

    from continuous_threading import CommandProcess


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


    obj1 = MyObj()
    obj2 = MyObj()

    proc = CommandProcess(target=obj1)
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

    proc.join()
