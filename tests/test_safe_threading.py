import time
import continuous_threading


def test_thread():
    h = [False]

    def set_h():
        h[0] = True

    th = continuous_threading.Thread(target=set_h)
    th.start()
    time.sleep(0.01)
    assert h[0] is True
    th.join()

    # Test class based approach
    class Th(continuous_threading.Thread):
        def __init__(self):
            super(Th, self).__init__()

            self.h = False

        def _run(self):
            self.h = True

    th = Th()
    th.start()
    time.sleep(0.01)
    assert th.h is True
    th.join()

    # Test context manager
    with Th() as th:
        pass
    assert th.h is True


def test_continuous_thread():
    counter = [0]

    def inc_counter():
        counter[0] += 1

    th = continuous_threading.ContinuousThread(target=inc_counter)
    th.start()
    time.sleep(0.01)
    val = counter[0]
    assert val > 0
    time.sleep(0.01)
    th.join()

    assert counter[0] > 1
    assert counter[0] > val

    # Test class based approach
    class Th(continuous_threading.ContinuousThread):
        def __init__(self):
            super(Th, self).__init__()
            self.counter = 0

        def _run(self, *args, **kwargs):
            self.counter += 1

    with Th() as th:
        pass

    assert th.counter > 0


def test_pausable_thread():
    counter = [0]

    def inc_counter():
        counter[0] += 1

    th = continuous_threading.PausableThread(target=inc_counter)
    th.start()

    time.sleep(0.01)
    th.stop()
    # time.sleep(0.01)  # Stop may not happen immediately
    val = counter[0]
    assert counter[0] == val
    assert val > 0

    time.sleep(0.01)
    assert counter[0] == val

    th.start()
    time.sleep(0.01)
    th.join()
    assert counter[0] > 1
    assert counter[0] > val

    # Test class based approach
    class Th(continuous_threading.PausableThread):
        def __init__(self):
            super(Th, self).__init__()
            self.counter = 0

        def _run(self, *args, **kwargs):
            self.counter += 1

    with Th() as th:
        time.sleep(0.01)
        th.stop()
        val = th.counter
        assert val > 0
        assert val == th.counter

        th.start()
        time.sleep(0.01)

    assert th.counter > 1
    assert th.counter > val


def test_operation_thread():
    values = []

    def operation(value):
        values.append(value)

    th = continuous_threading.OperationThread(target=operation)

    th.start()

    th.add_data(1)
    time.sleep(0.01)
    assert len(values) > 0
    assert values[0] == 1

    th.add_data(2)
    th.add_data(3)
    th.add_data(4)
    time.sleep(0.01)
    assert len(values) == 4
    assert values[1] == 2
    assert values[2] == 3
    assert values[3] == 4

    th.join()

    # Test the class based approach
    class Th(continuous_threading.OperationThread):
        def __init__(self):
            super(Th, self).__init__()

            self.values = []

        def _run(self, value):
            self.values.append(value)

    with Th() as th:
        assert len(th.values) == 0

        th.add_data(1)
        time.sleep(0.01)
        assert len(th.values) == 1
        assert th.values[0] == 1

        th.add_data(2)
        th.add_data(3)
        th.add_data(4)
        time.sleep(0.01)
        assert len(th.values) == 4
        assert th.values[1] == 2
        assert th.values[2] == 3
        assert th.values[3] == 4


if __name__ == '__main__':
    test_thread()
    test_continuous_thread()
    test_pausable_thread()
    test_operation_thread()
    print("All tests passed successfully!")
