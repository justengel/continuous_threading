import time
import continuous_threading


def test_thread():
    class Thread(continuous_threading.Thread):
        def _run(self, *args, **kwargs):
            print('here')

    th = Thread()
    th.start()
    time.sleep(0.1)


def test_continuous():
    class CountingThread(continuous_threading.ContinuousThread):
        def __init__(self):
            super(CountingThread, self).__init__()
            self.counter = 0

        def _run(self):
            self.counter += 1

    th = CountingThread()
    th.start()
    time.sleep(0.1)
    print('Iterations', th.counter)


def test_pausable():
    class PausableCountingThread(continuous_threading.PausableThread):
        def __init__(self):
            super(PausableCountingThread, self).__init__()
            self.counter = 0

        def _run(self):
            self.counter += 1

    th = PausableCountingThread()
    th.start()
    time.sleep(0.1)
    th.stop()
    print('Iterations (paused)', th.counter)
    th.start()
    time.sleep(0.1)
    print('Iterations', th.counter)


def test_operation():
    class SetValueThread(continuous_threading.OperationThread):
        def __init__(self):
            super(SetValueThread, self).__init__()
            self.value = 0

        def _run(self, data, *args, **kwargs):
            self.value = data

    th = SetValueThread()
    th.start()
    time.sleep(0.1)
    assert th.value == 0

    th.add_data(1)
    time.sleep(0.1)
    assert th.value == 1

    any(th.add_data(i) for i in range(20000))  # th.add_data returns None, so the entire range is executed
    # time.sleep(0.01)  # Not needed

    print('The set value', th.value, '| remaining queue size:', th.get_queue_size())

    # DO NOT STOP, CLOSE, OR, JOIN THE THREAD


if __name__ == '__main__':
    # Run one option at a time
    import sys

    # Default test run
    # run_test = test_thread
    # run_test = test_continuous
    # run_test = test_pausable
    run_test = test_operation

    if len(sys.argv) > 1:
        value = str(sys.argv[1]).lower()
        if value == '0' or value == 'thread':
            run_test = test_thread
        elif value == '1' or 'continuous' in value:
            run_test = test_continuous
        elif value == '2' or 'paus' in value:
            run_test = test_pausable
        elif value == '3' or 'op' in value:
            run_test = test_operation

    run_test()

    # You should observe that python.exe is no longer a running process when the program finishes.
    # exit code should be 0
