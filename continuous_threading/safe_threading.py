"""
This thread module provides several useful safe thread tools. The reason this module was created
was to easily create and manage threads that run continuously, allowing concurrency.

The basic thread can be used like a normal python thread and gives methods stop and close. The basic
thread also allows the thread to be used as a context manager using the 'with' statement.

.. code-block:: python

    import time
    
    def print_runs(run):
        i = 0
        while run.is_set():
            print(i)
            i += 1
        print("finished")

    run = Event()
    run.set()
    with Thread(target=print_runs, args=(run,):
        time.sleep(0.1)
        run.clear()


Another thread tool in this module is the ContinuousThread which helps you loop over a method until
you tell the thread to stop, close, or join.

.. code-block:: python

    import time

    def print_here():
        print("here")
    
    with ContinuousThread(target=print_here):
        time.sleep(0.1)
    print("finished")


The PausableThread can have an operation run then be paused for any length of time by calling stop(). Use start again to
continue the thread execution.

.. code-block:: python

    import time

    def print_here():
        print("here")
    
    th = threads.PausableThread(target=print_here)
    th.start()
    print("Thread is running")
    time.sleep(0.001)
    th.stop()
    print("Thread is paused")
    time.sleep(0.1)
    print("Thread is paused")
    print("Thread is paused")
    print("Thread is paused")
    th.start()
    time.sleep(0.001)
    print("Thread is running")
    print("Thread is running")
    
    th.close()
    print("finished")

Note:

    When python exits it calls join on every thread. This is problematic if your thread run method
    has a loop that exits on a condition the join will wait forever making it so your python program
    never exits. This also makes it so that atexit never calls all of it's registered exit functions.
"""
import threading
import time
from queue import Queue


__all__ = ['Thread', 'ContinuousThread', 'PausableThread', 'OperationThread']

SMALL_SLEEP_VALUE = 0.0000000000001


class Thread(threading.Thread):
    """Basic thread that contains context managers for use with the with statement.

    Note:
        There is a close_warning property. If this is set to True and this thread does not join successfully then
        a timer will alert the user that the thread did not join properly.

    Notes:
        Daemon threads are killed as Python is exiting. A Daemon thread with an infinite loop will get stuck and not
        close properly. These threads are setup to handle closing a looping thread.
    """

    def __init__(self, target=None, name=None, args=None, kwargs=None, daemon=None):
        self.close_warning = False
        if args is None:
            args = tuple()
        if kwargs is None:
            kwargs = dict()
        super(Thread, self).__init__(target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)

        if not hasattr(self, '_args'):
            self._args = args
        if not hasattr(self, '_kwargs'):
            self._kwargs = kwargs.copy()
        if not hasattr(self, '_started'):
            # Should be created by __init__ (parent method).
            self._started = threading.Event()

        if (not hasattr(self, "_target") or not self._target) and hasattr(self, "_run"):
            self._target = self._run

    def start(self):
        """Start running the thread."""
        super(Thread, self).start()
        if not self._started.is_set():
            self._started.set()

    def stop(self):
        """Stop the thread."""
        pass

    def close(self):
        """Close the thread."""
        self.stop()

    def _run(self, *args, **kwargs):
        """Default function target to run if a target is not given."""
        pass
    
    def join(self, timeout=None):
        """Properly close the thread."""
        tmr_out = (timeout or 3) + 2

        join_tmr = None
        if self.close_warning:
            join_tmr = threading.Timer(tmr_out, self._warn_user)  # Indicate there is an error if not closed soon
            join_tmr.start()

        self.close()
        time.sleep(SMALL_SLEEP_VALUE)  # Give time for the run method close everything
        super(Thread, self).join(timeout)

        try:
            join_tmr.cancel()
            join_tmr.join()
        except AttributeError:
            pass

    def _warn_user(self):
        """Method that raises a runtime error to warn the user that the thread did not close
        properly.
        """
        raise RuntimeError("WARNING: The thread did not join properly!\n"
                           "Consider making this a daemon thread or a loop is keeping the thread from joining. " +
                           str(self))

    def __call__(self):
        """Call and return self. It makes it easier to use the "with" statement."""
        return self

    def __enter__(self):
        """Enter statement for use of 'with' statement."""
        self.start()
        return self

    def __exit__(self, ttype, value, traceback):
        """Exit statement for use of the 'with' statement."""
        try:
            self.join(0)  # Make sure join has a 0 timeout so it is not blocking while exiting
        except RuntimeError:
            pass

        return ttype is None  # Return False if there was an error
# end class Thread


class ContinuousThread(Thread):
    """Thread that is continuously running and closes properly. Do not override the run method.
    If you are using this class with inheritance override the '_run' method.
    """
    def __init__(self, target=None, name=None, args=None, kwargs=None, daemon=None):
        # Thread properties
        self.alive = threading.Event()  # If the thread is running
        super(ContinuousThread, self).__init__(target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)

    def is_running(self):
        """Return if the serial port is connected and alive."""
        return self.alive.is_set()
    
    is_active = is_running

    def start(self):
        """Start running the thread."""
        if not self._started.is_set():
            self.daemon = False  # Forces join to be called which closes the thread properly.
        self.alive.set()
        super(ContinuousThread, self).start()
    
    def stop(self):
        """Stop running the thread."""
        self.alive.clear()
        time.sleep(SMALL_SLEEP_VALUE)

    def _run(self, *args, **kwargs):
        """Run method called if a target is not given to the thread. This method should be overridden if inherited."""
        pass

    def run(self):
        """The thread will loop through running the set _target method (default _run()). This 
        method can be paused and restarted.
        """
        while self.alive.is_set():
            # Run the thread method
            self._target(*self._args, **self._kwargs)
# end class ContinuousThread


class PausableThread(ContinuousThread):
    """Thread that is continuously running, can be paused, and closes properly. Do not override
    the run method. If you are using this class with inheritance override the '_run' method.
    """

    def __init__(self, target=None, name=None, args=None, kwargs=None, daemon=None):
        self.kill = threading.Event()  # Loop condition to exit and kill the thread
        super(PausableThread, self).__init__(target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)

    def is_running(self):
        """Return if the serial port is connected and alive."""
        return not self.kill.is_set() and self.alive.is_set()

    is_active = is_running

    def start(self):
        """Start running the thread."""
        # Resume the thread run method
        self.alive.set()  # If in alive.wait then setting this flag will resume the thread

        # If the thread has not been started then start it. Start can only run once
        if not self._started.is_set():
            super(PausableThread, self).start()

    def stop(self):
        """Stop running the thread. Use close or join to completely finish using the thread.
        When Python exits it will call the thread join method to properly close the thread.
        """
        self.alive.clear()  # Cause the thread to wait, pausing execution until alive is set.
        time.sleep(SMALL_SLEEP_VALUE)
    
    def close(self):
        """Completely finish using the thread. When Python exits it will call the thread join
        method to properly close the thread. It should not be necessary to call this method.
        """
        self.kill.set()  # Exit the loop to kill the thread
        self.alive.set()  # If in alive.wait then setting this flag will resume the thread
        time.sleep(SMALL_SLEEP_VALUE)

    def _run(self, *args, **kwargs):
        """Run method called if a target is not given to the thread. This method should be overridden if inherited."""
        pass

    def run(self):
        """The thread will loop through running the set _target method (default _run()). This 
        method can be paused and restarted.
        """
        while not self.kill.is_set():
            self.alive.wait()  # If alive is set then it does not wait according to docs.
            if self.kill.is_set():
                break

            # Run the read and write
            self._target(*self._args, **self._kwargs)
        # end

        self.alive.clear()  # The thread is no longer running
# end class PausableThread


class OperationThread(PausableThread):
    """This thread class is for running a calculation over and over, but with different data.
    
    Set the target function to be the operation that runs. Call add_data to run the calculation on that piece of data.
    Data must be the first argument of the target function.
    """

    PUMP_QUEUE_DATA = '__PUMP_QUEUE__'

    def __init__(self, target=None, name=None, args=None, kwargs=None, daemon=None):
        self._operations = Queue()
        self.stop_processing = False
        super(OperationThread, self).__init__(target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)

    def get_queue_size(self):
        """Return the operation Queue size."""
        return self._operations.qsize()

    def add_data(self, data, *args, **kwargs):
        """Add data to the operation queue to process."""
        self._operations.put([data, args, kwargs])
        self.start()

    def pump_queue(self):
        """Unblock the queue. The _operations queue may be blocking on the `get()` function. This function puts dummy
        data into the queue so it exits the `get()` command. The dummy data is ignored.
        """
        self.add_data(self.PUMP_QUEUE_DATA)

    def run(self):
        """The thread will loop through running the set _target method (default _run()). This 
        method can be paused and restarted.
        """
        while not self.kill.is_set():
            self.alive.wait()  # If alive is set then it does not wait according to docs.
            if self.kill.is_set():
                break

            # Wait for data and other arguments
            data, args, kwargs = self._operations.get()

            # Check if this data should be executed
            if not self.stop_processing and data != self.PUMP_QUEUE_DATA:
                # Run the data through the target function
                args = args or self._args
                kwargs = kwargs or self._kwargs
                self._target(data, *args, **kwargs)
        # end

        self.alive.clear()  # The thread is no longer running

    def stop(self):
        super(OperationThread, self).stop()
        self.pump_queue()

    def close(self):
        super(OperationThread, self).close()
        time.sleep(0.1)
        self.pump_queue()
# end class OperationThread
