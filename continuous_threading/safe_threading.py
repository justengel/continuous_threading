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
import sys
import time
import threading
import contextlib

try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty


__all__ = [
    'is_py27', 'Queue', 'Empty',
    'Thread', 'ContinuousThread', 'PausableThread', 'OperationThread', 'PeriodicThread'
    ]


SMALL_SLEEP_VALUE = 0.00001
is_py27 = sys.version_info < (3, 0)

# Thread Objects
BaseThread = threading.Thread
Event = threading.Event
Timer = threading.Timer
RLock = threading.RLock


@contextlib.contextmanager
def safe_release(lock):
    """Fixes RuntimeError for unlocking a released lock."""
    # with lock:
    #     yield
    try:
        lock.acquire()
        yield
    finally:
        if lock.locked():
            lock.release()


class Thread(BaseThread):
    """Basic thread that contains context managers for use with the with statement.

    Note:
        There is a close_warning property. If this is set to True and this thread does not join successfully then
        a timer will alert the user that the thread did not join properly.

    Notes:
        Daemon threads are killed as Python is exiting. A Daemon thread with an infinite loop will get stuck and not
        close properly. These threads are setup to handle closing a looping thread.
    """

    def __init__(self, target=None, name=None, args=None, kwargs=None, daemon=None, group=None):
        self.force_non_daemon = True
        self.close_warning = False
        self._is_alive = Event()
        if args is None:
            args = tuple()
        if kwargs is None:
            kwargs = dict()
        super(Thread, self).__init__(target=target, name=name, args=args, kwargs=kwargs, daemon=daemon, group=group)

        # Check the daemon argument
        if daemon is not None:
            self.daemon = daemon

        if is_py27:
            self._args = self.__args
            self._kwargs = self.__kwargs
            self._started = self.__started
            self._target = self.__target

        if self._target is None and hasattr(self, '_run'):
            if is_py27:
                self.__target = self._run
            self._target = self._run

    def start(self):
        """Start running the thread.

        Note:
            The `force_non_daemon` attribute is initialized to True. This variable will set `daemon = False` when this
            `start()` function is called. If you want to run a daemon thread set `force_non_daemon = False` and set
            `daemon = True`. If you do this then the `close()` function is not guaranteed to be called.
        """
        if not self._started.is_set():
            # If daemone=False python forces join to be called which closes the thread properly.
            if self.force_non_daemon:
                self.daemon = False

            self._is_alive.set()
            super(Thread, self).start()

    def stop(self):
        """Stop the thread."""
        pass

    def close(self):
        """Close the thread (clean up variables)."""
        self.stop()

    def is_alive(self):
        """Return if the Thread is alive.

        The threading.Thread.is_alive uses the "_tstate_lock". This library implemented allow_shutdown() which allows
        users to change the "_tstate_lock". This stops threading._shutdown() from halting until "_tstate_lock"
        is released.
        """
        try:
            return self._is_alive.is_set()
        except (AttributeError, Exception):
            return False

    def _run(self, *args, **kwargs):
        """Default function target to run if a target is not given."""
        pass

    def allow_shutdown(self):
        """Release the "_tstate_lock" to allow threading._shutdown to finish.

        The threading._shutdown() function waits for all non-daemon threads to release their "_t_state_lock".
        This allows the ContinuousThread to join() automatically at exit.

        Returns:
            lock (RLock): The "_tstate_lock" or new RLock that can be used to safely run code blocks.
                See Also ContinuousThread.run().
        """
        lock = getattr(self, '_tstate_lock')
        if lock is not None:
            lock.release()
        else:
            lock = RLock()
        return lock
    
    def join(self, timeout=None):
        """Properly close the thread."""
        try:
            self._is_alive.clear()

            # Close warning
            join_tmr = self._create_close_warning_timer(timeout)

            self.close()  # Cleanup function
            time.sleep(SMALL_SLEEP_VALUE)  # Wait for the run method to exit a loop and close everything

            # Join the thread
            super(Thread, self).join(timeout)
        finally:
            try:
                join_tmr.cancel()
                join_tmr.join()
            except AttributeError:
                pass

    def _create_close_warning_timer(self, timeout):
        """Create and return a timer that will Warn the user that the thread did not close."""
        # Close warning
        join_tmr = None
        if self.close_warning:
            tmr_out = (timeout or 3) + 2 + SMALL_SLEEP_VALUE
            join_tmr = Timer(tmr_out, self._warn_user)  # Indicate there is an error if not closed soon
            join_tmr.start()

        return join_tmr

    def _warn_user(self):
        """Method that raises a runtime error to warn the user that the thread did not close
        properly.
        """
        raise RuntimeError("WARNING: The thread '{0}' did not join properly!\n"
                           "A loop may be keeping the thread from joining. "
                           "Try overriding the close method to clean up the thread.".format(str(self)))

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
    def __init__(self, target=None, name=None, args=None, kwargs=None, daemon=None, group=None,
                 init=None, iargs=None, ikwargs=None):
        """Initialize the thread object.

        Args:
            target (object)[None]: Target functions to run in a separate thread.
            name (str)[None]: Name of the new process.
            args (tuple)[None]: Default positional arguments to pass into the given target function.
            kwargs (dict)[None]: Default keyword arguments to pass into the given target function.
            daemon (bool)[None]: If this process should be a daemon process. This is automatically forced to be False.
                Non-daemon process/threads call join when python exits.
            group (object)[None]: Not used in python multiprocessing at this time.
            init (callable)[None]: Run this function at the start of the process. If it returns a dictionary pass the
                dictionary as keyword arguments into the target function.
            iargs (tuple)[None]: Positional arguments to pass into init
            ikwargs (dict)[None]: Keyword arguments to pass into init.
        """
        # Thread properties
        self.alive = Event()  # If the thread is running
        self.init = init
        self.iargs = iargs or tuple()
        self.ikwargs = ikwargs or dict()

        super(ContinuousThread, self).__init__(target=target, name=name, args=args, kwargs=kwargs,
                                               daemon=daemon, group=group)

    def is_running(self):
        """Return if the serial port is connected and alive."""
        return self.alive.is_set()
    
    is_active = is_running

    def start(self):
        """Start running the thread."""
        self.alive.set()
        super(ContinuousThread, self).start()

    def stop(self):
        """Stop running the thread."""
        self.alive.clear()
        time.sleep(SMALL_SLEEP_VALUE)

    def _run(self, *args, **kwargs):
        """Run method called if a target is not given to the thread. This method should be overridden if inherited."""
        pass

    def run_init(self):
        """Run the init function and return the args and kwargs."""
        args = self._args
        kwargs = self._kwargs
        if callable(self.init):
            kwds = self.init(*self.iargs, **self.ikwargs)
            if isinstance(kwds, dict) and len(kwds) > 0:
                kwds.update(kwargs)
                kwargs = kwds
        return args, kwargs

    def run(self):
        """The thread will loop through running the set _target method (default _run()). This 
        method can be paused and restarted.
        """
        args, kwargs = self.run_init()

        # Allow threading._shutdown() to continue
        lock = self.allow_shutdown()

        while self.alive.is_set():
            # Run the thread method while protected in the lock state
            with safe_release(lock):
                self._target(*args, **kwargs)
# end class ContinuousThread


class PausableThread(ContinuousThread):
    """Thread that is continuously running, can be paused, and closes properly. Do not override
    the run method. If you are using this class with inheritance override the '_run' method.
    """

    def __init__(self, target=None, name=None, args=None, kwargs=None, daemon=None, group=None,
                 init=None, iargs=None, ikwargs=None):
        """Initialize the thread object.

        Args:
            target (object)[None]: Target functions to run in a separate thread.
            name (str)[None]: Name of the new process.
            args (tuple)[None]: Default positional arguments to pass into the given target function.
            kwargs (dict)[None]: Default keyword arguments to pass into the given target function.
            daemon (bool)[None]: If this process should be a daemon process. This is automatically forced to be False.
                Non-daemon process/threads call join when python exits.
            group (object)[None]: Not used in python multiprocessing at this time.
            init (callable)[None]: Run this function at the start of the process. If it returns a dictionary pass the
                dictionary as keyword arguments into the target function.
            iargs (tuple)[None]: Positional arguments to pass into init
            ikwargs (dict)[None]: Keyword arguments to pass into init.
        """
        self.kill = Event()  # Loop condition to exit and kill the thread
        super(PausableThread, self).__init__(target=target, name=name, args=args, kwargs=kwargs,
                                             daemon=daemon, group=group, init=init, iargs=iargs, ikwargs=ikwargs)

    def is_running(self):
        """Return if the serial port is connected and alive."""
        return not self.kill.is_set() and self.alive.is_set()

    is_active = is_running

    def start(self):
        """Start running the thread.

        Note:
            The `force_non_daemon` attribute is initialized to True. This variable will set `daemon = False` when this
            `start()` function is called. If you want to run a daemon thread set `force_non_daemon = False` and set
            `daemon = True`. If you do this then the `close()` function is not guaranteed to be called.
        """
        # Resume the thread run method
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
        args, kwargs = self.run_init()

        # Allow threading._shutdown() to continue
        lock = self.allow_shutdown()

        while not self.kill.is_set():
            self.alive.wait()  # If alive is set then it does not wait according to docs.
            if self.kill.is_set():
                break

            # Run the thread method while protected in the lock state
            with safe_release(lock):
                self._target(*args, **kwargs)
        # end

        self.alive.clear()  # The thread is no longer running
# end class PausableThread


class OperationThread(ContinuousThread):
    """This thread class is for running a calculation over and over, but with different data.
    
    Set the target function to be the operation that runs. Call add_data to run the calculation on that piece of data.
    Data must be the first argument of the target function.
    """

    def __init__(self, target=None, name=None, args=None, kwargs=None, daemon=None, group=None,
                 init=None, iargs=None, ikwargs=None, timeout=2):
        """Initialize the thread object.

        Args:
            target (object)[None]: Target functions to run in a separate thread.
            name (str)[None]: Name of the new process.
            args (tuple)[None]: Default positional arguments to pass into the given target function.
            kwargs (dict)[None]: Default keyword arguments to pass into the given target function.
            daemon (bool)[None]: If this process should be a daemon process. This is automatically forced to be False.
                Non-daemon process/threads call join when python exits.
            group (object)[None]: Not used in python multiprocessing at this time.
            init (callable)[None]: Run this function at the start of the process. If it returns a dictionary pass the
                dictionary as keyword arguments into the target function.
            iargs (tuple)[None]: Positional arguments to pass into init
            ikwargs (dict)[None]: Keyword arguments to pass into init.
            timeout (int/float): Queue.get timeout.
        """
        self._operations = Queue()
        self.stop_processing = False
        self._timeout = timeout
        super(OperationThread, self).__init__(target=target, name=name, args=args, kwargs=kwargs,
                                              daemon=daemon, group=group, init=init, iargs=iargs, ikwargs=ikwargs)

    def get_timeout(self):
        """Return the queue timeout."""
        return self._timeout

    def set_timeout(self, value):
        """Set the queue timeout."""
        self._timeout = value

    @property
    def timeout(self):
        """Return the queue timeout."""
        return self.get_timeout()

    @timeout.setter
    def timeout(self, value):
        """Set the queue timeout."""
        self.set_timeout(value)

    def get_queue_size(self):
        """Return the operation Queue size."""
        return self._operations.qsize()

    def add_data(self, *args, **kwargs):
        """Add data to the operation queue to process."""
        self.start()
        self._operations.put([args, kwargs])

    def run(self):
        """The thread will loop through running the set _target method (default _run()). This 
        method can be paused and restarted.
        """
        args, kwargs = self.run_init()

        # Allow threading._shutdown() to continue
        lock = self.allow_shutdown()

        while self.alive.is_set():
            try:
                # Wait for data and other arguments
                op_args, op_kwargs = self._operations.get(timeout=self.timeout)

                # Check if this data should be executed
                if not self.stop_processing:
                    # Run the thread method while protected in the lock state
                    with safe_release(lock):
                        # Run the data through the target function
                        op_args = op_args or args
                        op_kwargs.update(kwargs)
                        self._target(*op_args, **op_kwargs)
            except Empty:
                continue

        self.alive.clear()  # The thread is no longer running
# end class OperationThread


class PeriodicThread(ContinuousThread):
    def __init__(self, interval, target=None, name=None, args=None, kwargs=None, daemon=None, group=None,
                 init=None, iargs=None, ikwargs=None):
        """Create a thread that will run a function periodically.

        Args:
            interval (int/float): How often to run a function in seconds.
            target (object)[None]: Target functions to run in a separate thread.
            name (str)[None]: Name of the new process.
            args (tuple)[None]: Default positional arguments to pass into the given target function.
            kwargs (dict)[None]: Default keyword arguments to pass into the given target function.
            daemon (bool)[None]: If this process should be a daemon process. This is automatically forced to be False.
                Non-daemon process/threads call join when python exits.
            group (object)[None]: Not used in python multiprocessing at this time.
            init (callable)[None]: Run this function at the start of the process. If it returns a dictionary pass the
                dictionary as keyword arguments into the target function.
            iargs (tuple)[None]: Positional arguments to pass into init
            ikwargs (dict)[None]: Keyword arguments to pass into init.
        """
        super(PeriodicThread, self).__init__(target=target, name=name, args=args, kwargs=kwargs,
                                             daemon=daemon, group=group, init=init, iargs=iargs, ikwargs=ikwargs)
        self.interval = interval

    def run(self):
        """The thread will loop through running the set _target method (default _run()). This
        method can be paused and restarted.
        """
        args, kwargs = self.run_init()

        # Allow threading._shutdown() to continue
        lock = self.allow_shutdown()

        start = time.time()
        while self.alive.is_set():
            # Run the thread method while protected in the lock state
            with safe_release(lock):
                self._target(*args, **kwargs)
            try:
                time.sleep(self.interval - (time.time() - start))
            except ValueError:
                pass  # sleep time less than 0
            start = time.time()
