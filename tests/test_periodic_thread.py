"""
Test different timing solutions for accuracy. I ran these on Windows ... windows is not very accurate

Conclusion:

The best results seem to come from PeriodicThread_1.

The worst results seem to come from the Timer which very closely mimics the threading.Timer class.
"""
# from __future__ import division
import os
import time
import continuous_threading

DIRNAME = os.path.dirname(__file__)


class PeriodicThread_1(continuous_threading.ContinuousThread):
    def __init__(self, period, target=None, name=None, args=None, kwargs=None, daemon=None):
        """Create a thread that will run a function periodically.

        Args:
            period (int/float): How often to run a function in seconds.
        """
        super(PeriodicThread_1, self).__init__(target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)
        self.period = period

    def run(self):
        """The thread will loop through running the set _target method (default _run()). This
        method can be paused and restarted.
        """
        while self.alive.is_set():
            # Run the thread method
            start = time.time()
            self._target(*self._args, **self._kwargs)
            try:
                time.sleep(self.period - (time.time() - start))
            except ValueError:
                pass  # sleep time less than 0


class PeriodicThread_2(continuous_threading.ContinuousThread):
    def __init__(self, period, target=None, name=None, args=None, kwargs=None, daemon=None):
        """Create a thread that will run a function periodically.

        Args:
            period (int/float): How often to run a function in seconds.
        """
        super(PeriodicThread_2, self).__init__(target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)
        self.period = period

    def run(self):
        """The thread will loop through running the set _target method (default _run()). This
        method can be paused and restarted.
        """
        start = time.time()

        while self.alive.is_set():
            # Run the thread method
            duration = time.time() - start
            time.sleep(max(0, self.period - duration))

            self._target(*self._args, **self._kwargs)
            start = time.time()


class PeriodicThread_3(continuous_threading.PausableThread):
    def __init__(self, period, target=None, name=None, args=None, kwargs=None, daemon=None):
        """Create a thread that will run a function periodically.

        Args:
            period (int/float): How often to run a function in seconds.
        """
        super(PeriodicThread_3, self).__init__(target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)
        self.period = period

    def run(self):
        """The thread will loop through running the set _target method (default _run()). This
        method can be paused and restarted.
        """
        while not self.kill.is_set():
            self.alive.wait()  # If alive is set then it does not wait according to docs.
            if self.kill.is_set():
                break

            # Run the function
            start = time.time()
            self._target(*self._args, **self._kwargs)
            duration = time.time() - start
            time.sleep(max(0, self.period - duration))
        # end

        self.alive.clear()  # The thread is no longer running


class PeriodicThread_4(continuous_threading.PausableThread):
    def __init__(self, period, target=None, name=None, args=None, kwargs=None, daemon=None):
        """Create a thread that will run a function periodically.

        Args:
            period (int/float): How often to run a function in seconds.
        """
        super(PeriodicThread_4, self).__init__(target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)
        self.period = period

    def run(self):
        """The thread will loop through running the set _target method (default _run()). This
        method can be paused and restarted.
        """
        # Get the time
        start = time.time()

        while not self.kill.is_set():
            self.alive.wait()  # If alive is set then it does not wait according to docs.
            if self.kill.is_set():
                break

            # Wait to run the function again.
            duration = time.time() - start
            time.sleep(max(0, self.period - duration))

            # Run the function
            self._target(*self._args, **self._kwargs)

            # Get the time
            start = time.time()
        # end

        self.alive.clear()  # The thread is no longer running


class Timer(continuous_threading.ContinuousThread):
    def __init__(self, interval, target=None, name=None, args=None, kwargs=None, daemon=None):
        """Create a thread that will run a function periodically.

        Args:
            interval (int/float): How often to run a function in seconds.
        """
        super(Timer, self).__init__(target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)
        self.interval = interval
        self.time_event = continuous_threading.Condition()

    def stop(self):
        with self.time_event:
            self.time_event.notify_all()
        super(Timer, self).stop()

    def cancel(self):
        self.stop()

    def run(self):
        """The thread will loop through running the set _target method (default _run()). This
        method can be paused and restarted.
        """
        while self.alive.is_set():
            # Run the thread method
            self._target(*self._args, **self._kwargs)

            # Python 2.7 is fast, Python 3.6 is horribly slow (stop will be more responsive)
            with self.time_event:
                self.time_event.wait(self.interval)  # Will return True when time_event.set() is called


def test_periodic_accuracy(periodic_thread_class=None):
    if periodic_thread_class is None:
        periodic_thread_class = PeriodicThread_1

    period = 0.001  # 0.0001 NOT ACCURATE ON WINDOWS
    time_list = []
    add_time = time_list.append

    def log_time():
        add_time(time.time())

    th = periodic_thread_class(period, target=log_time)
    th.start()

    time.sleep(4)
    th.join()

    # Compare times
    diff = [(time_list[i+1] - time_list[i]) - period for i in range(0, len(time_list)-1, 2)]
    # print('Time offsets:', diff)
    print(periodic_thread_class.__name__, 'Average time offset:', sum(diff)/len(diff),
          'The period was ', period,
          'The number of occurrences was', len(diff))


if __name__ == '__main__':
    test_periodic_accuracy(PeriodicThread_1)
    test_periodic_accuracy(PeriodicThread_2)
    test_periodic_accuracy(PeriodicThread_3)
    test_periodic_accuracy(PeriodicThread_4)
    test_periodic_accuracy(Timer)
