import os
import sys
import time
import traceback
import collections
import threading
import multiprocessing as mp

try:
    from queue import Empty
except (ImportError, Exception):
    try:
        from Queue import Empty
    except (ImportError, Exception):
        Empty = Exception

try:
    import psutil
except (ImportError, Exception):
    psutil = None


__all__ = ['Empty', 'ProcessError', 'MpEvent', 'MpQueue', 'MpJoinableQueue', 'MpSimpleQueue',
           'is_parent_process_alive', 'mark_task_done',
           'Process', 'ContinuousProcess', 'PausableProcess', 'PeriodicProcess', 'OperationProcess',
           'BaseCommand', 'ObjectCommand', 'ProcessCommand', 'ExecCommand', 'CommandProcess']


IS_PY27 = sys.version_info < (3, 0)


ProcessError = mp.ProcessError
MpEvent = mp.Event
MpQueue = mp.Queue
MpJoinableQueue = mp.JoinableQueue
try:
    MpSimpleQueue = mp.SimpleQueue
except (AttributeError, Exception):
    MpSimpleQueue = mp.Queue


def print_exception(exc, msg=None):
    """Print the given exception. If a message is given it will be prepended to the exception message with a \n."""
    if msg:
        exc = "\n".join((msg, str(exc)))
    _, _, exc_tb = sys.exc_info()
    typ = type(exc)
    traceback.print_exception(typ, typ(exc), exc_tb)


def is_parent_process_alive():
    """Return if the parent process is alive. This relies on psutil, but is optional."""
    if psutil is None:
        return True
    try:
        return psutil.pid_exists(os.getppid())
    except (AttributeError, KeyboardInterrupt, Exception):
        return False


def mark_task_done(que):
    """Mark a JoinableQueue as done."""
    # Mark done
    try:
        que.task_done()
    except (AttributeError, ValueError):  # Value error if task_done called more times than put
        pass


class Process(mp.Process):
    """Run a function in a separate process."""
    def __init__(self, target=None, name=None, args=None, kwargs=None, daemon=None, group=None):
        """Initialize the new process object.

        Args:
            target (object)[None]: Target functions to run in a separate process.
            name (str)[None]: Name of the new process.
            args (tuple)[None]: Default positional arguments to pass into the given target function.
            kwargs (dict)[None]: Default keyword arguments to pass into the given target function.
            daemon (bool)[None]: If this process should be a daemon process. This is automatically forced to be False.
                Non-daemon process/threads call join when python exits.
            group (object)[None]: Not used in python multiprocessing at this time.
        """
        self.force_non_daemon = True
        if args is None:
            args = tuple()
        if kwargs is None:
            kwargs = {}
        self._started = mp.Event()
        super(Process, self).__init__(target=target, name=name, args=args, kwargs=kwargs, daemon=daemon, group=group)

        if self._target is None and hasattr(self, '_run'):
            self._target = self._run

    def was_started(self):
        """Return if the process was started."""
        return self._started.is_set()

    def is_main_process(self):
        """Return if this process is the main process."""
        return getattr(self, '_popen', None) is not None

    def is_child_process(self):
        """Return if this is the separate process."""
        return getattr(self, '_popen', None) is None

    def should_run(self):
        """Return if this separate process should keep running."""
        return is_parent_process_alive()

    def start(self):
        """Start running the thread.

        Note:
            The `force_non_daemon` attribute is initialized to True. This variable will set `daemon = False` when this
            `start()` function is called. If you want to run a daemon thread set `force_non_daemon = False` and set
            `daemon = True`. If you do this then the `close()` function is not guaranteed to be called.
        """
        if not self._started.is_set():
            # If daemone=False python forces join to be called which closes the thread properly.
            self.daemon = self.force_non_daemon or self.daemon
            if self.force_non_daemon:
                self.daemon = False

            super(Process, self).start()
        self._started.set()
        return self

    def stop(self):
        """Stop the thread."""
        return self

    def close(self):
        """Close the thread (clean up variables)."""
        self.stop()

    def join(self, timeout=None):
        """Properly close the process."""
        self.close()
        super(Process, self).join(timeout)

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


class ContinuousProcess(Process):
    """Process that is continuously running a function and closes properly. If you want a single function to run over
    and over again give a target function or override the '_run' method. It is not recommended to override the normal
    'run' method.
    """
    def __init__(self, target=None, name=None, args=None, kwargs=None, daemon=None, group=None):
        """Initialize the new process object.

        Args:
            target (object)[None]: Target functions to run in a separate process.
            name (str)[None]: Name of the new process.
            args (tuple)[None]: Default positional arguments to pass into the given target function.
            kwargs (dict)[None]: Default keyword arguments to pass into the given target function.
            daemon (bool)[None]: If this process should be a daemon process. This is automatically forced to be False.
                Non-daemon process/threads call join when python exits.
            group (object)[None]: Not used in python multiprocessing at this time.
        """
        # Thread properties
        self.alive = mp.Event()  # If the thread is running
        super(ContinuousProcess, self).__init__(target=target, name=name, args=args, kwargs=kwargs,
                                                daemon=daemon, group=group)

    def is_running(self):
        """Return if the serial port is connected and alive."""
        return self.alive.is_set()

    is_active = is_running

    def should_run(self):
        """Return if this separate process should keep running."""
        return self.alive.is_set() and is_parent_process_alive()

    def start(self):
        """Start running the thread."""
        self.alive.set()
        super(ContinuousProcess, self).start()
        return self

    def stop(self):
        """Stop running the thread."""
        self.alive.clear()
        return self

    def _run(self, *args, **kwargs):
        """Run method called if a target is not given to the thread. This method should be overridden if inherited."""
        pass

    def run(self):
        """The thread will loop through running the set _target method (default _run()). This
        method can be paused and restarted.
        """
        while self.should_run():
            # Run the thread method
            self._target(*self._args, **self._kwargs)


class PausableProcess(ContinuousProcess):
    """Process that is continuously running, can be paused, and closes properly. If you want a single function to run
    over and over again give a target function or override the '_run' method. It is not recommended to override the
    normal 'run' method.
    """

    def __init__(self, target=None, name=None, args=None, kwargs=None, daemon=None, group=None):
        """Initialize the new process object.

        Args:
            target (object)[None]: Target functions to run in a separate process.
            name (str)[None]: Name of the new process.
            args (tuple)[None]: Default positional arguments to pass into the given target function.
            kwargs (dict)[None]: Default keyword arguments to pass into the given target function.
            daemon (bool)[None]: If this process should be a daemon process. This is automatically forced to be False.
                Non-daemon process/threads call join when python exits.
            group (object)[None]: Not used in python multiprocessing at this time.
        """
        self.kill = mp.Event()  # Loop condition to exit and kill the thread
        super(PausableProcess, self).__init__(target=target, name=name, args=args, kwargs=kwargs,
                                              daemon=daemon, group=group)

    def is_running(self):
        """Return if the serial port is connected and alive."""
        return not self.kill.is_set() and self.alive.is_set()

    is_active = is_running

    def should_run(self):
        """Return if this separate process should keep running."""
        return not self.kill.is_set() and is_parent_process_alive()

    def start(self):
        """Start running the thread.

        Note:
            The `force_non_daemon` attribute is initialized to True. This variable will set `daemon = False` when this
            `start()` function is called. If you want to run a daemon thread set `force_non_daemon = False` and set
            `daemon = True`. If you do this then the `close()` function is not guaranteed to be called.
        """
        # Resume the thread run method
        super(PausableProcess, self).start()
        return self

    def stop(self):
        """Stop running the thread. Use close or join to completely finish using the thread.
        When Python exits it will call the thread join method to properly close the thread.
        """
        self.alive.clear()  # Cause the thread to wait, pausing execution until alive is set.
        return self

    def close(self):
        """Completely finish using the thread. When Python exits it will call the thread join
        method to properly close the thread. It should not be necessary to call this method.
        """
        self.kill.set()  # Exit the loop to kill the thread
        self.alive.set()  # If in alive.wait then setting this flag will resume the thread

    def _run(self, *args, **kwargs):
        """Run method called if a target is not given to the thread. This method should be overridden if inherited."""
        pass

    def run(self):
        """The thread will loop through running the set _target method (default _run()). This
        method can be paused and restarted.
        """
        while self.should_run():
            self.alive.wait()  # If alive is set then it does not wait according to docs.
            if self.kill.is_set():
                break

            # Run the read and write
            self._target(*self._args, **self._kwargs)
        # end

        self.alive.clear()  # The thread is no longer running


class PeriodicProcess(ContinuousProcess):
    """This process class is for running a function continuously at a given interval."""
    def __init__(self, interval, target=None, name=None, args=None, kwargs=None, daemon=None, group=None):
        """Initialize the new process object.

        Args:
            interval (int/float): How often to run a function in seconds.
            target (object)[None]: Target functions to run in a separate process.
            name (str)[None]: Name of the new process.
            args (tuple)[None]: Default positional arguments to pass into the given target function.
            kwargs (dict)[None]: Default keyword arguments to pass into the given target function.
            daemon (bool)[None]: If this process should be a daemon process. This is automatically forced to be False.
                Non-daemon process/threads call join when python exits.
            group (object)[None]: Not used in python multiprocessing at this time.
        """
        self.interval = interval
        super(PeriodicProcess, self).__init__(target=target, name=name, args=args, kwargs=kwargs,
                                              daemon=daemon, group=group)

    def run(self):
        """The thread will loop through running the set _target method (default _run()). This
        method can be paused and restarted.
        """
        while self.should_run():
            # Run the thread method
            start = time.time()
            self._target(*self._args, **self._kwargs)
            try:
                pause = self.interval - (time.time() - start)
                if pause > 0:
                    time.sleep(pause)
            except ValueError:
                pass  # sleep time less than 0


class OperationProcess(ContinuousProcess):
    """This thread class is for running a calculation over and over, but with different data.

    Set the target function to be the operation that runs. Call add_data to run the calculation on that piece of data.
    """

    def __init__(self, target=None, name=None, args=None, kwargs=None, daemon=None, group=None):
        """Initialize the new process object.

        Args:
            target (object)[None]: Target functions to run in a separate process.
            name (str)[None]: Name of the new process.
            args (tuple)[None]: Default positional arguments to pass into the given target function.
            kwargs (dict)[None]: Default keyword arguments to pass into the given target function.
            daemon (bool)[None]: If this process should be a daemon process. This is automatically forced to be False.
                Non-daemon process/threads call join when python exits.
            group (object)[None]: Not used in python multiprocessing at this time.
        """
        self._operations = mp.Queue()
        self._stop_processing = mp.Event()
        self._timeout = 2  # Timeout in seconds
        super(OperationProcess, self).__init__(target=target, name=name, args=args, kwargs=kwargs,
                                               daemon=daemon, group=group)

    @property
    def stop_processing(self):
        """Return if this process is allowed to process events."""
        return self._stop_processing.is_set()

    @stop_processing.setter
    def stop_processing(self, value):
        """Set if this process is allowed to process events."""
        if value:
            self._stop_processing.set()
        else:
            self._stop_processing.clear()

    def get_timeout(self):
        """Return the queue timeout."""
        return self._timeout

    def set_timeout(self, value):
        """Set the queue timeout."""
        if self.was_started() and self.is_main_process():
            self.add_data(value, INTERNAL_PROCESS_COMMAND='set_timeout')
        self._timeout = value

    @property
    def timeout(self):
        """Return the queue timeout."""
        return self.get_timeout()

    @timeout.setter
    def timeout(self, value):
        """Set the queue timeout."""
        self.set_timeout(value)

    @property
    def queue(self):
        """Return the operation queue."""
        return self._operations

    @queue.setter
    def queue(self, value):
        """Set the operation queue."""
        if self.was_started() and self.is_main_process():  # Could be INTERNAL_PROCESS_COMMAND
            raise RuntimeError('Cannot set the Queue when the process was already started.')
        if not isinstance(value, mp.Queue):
            raise ValueError('The given value must be a type of multiprocessing Queue not a threading Queue.')
        self._operations = value

    def qsize(self):
        """Return the queue size."""
        return self._operations.qsize()

    def add_data(self, *args, **kwargs):
        """Add data to the operation queue to process."""
        if not self.was_started():
            self.start()  # This should not error for multiple runs.
        self._operations.put([args, kwargs])

    def run(self):
        """The thread will loop through running the set _target method (default _run()). This
        method can be paused and restarted.
        """
        while self.should_run():
            self._run_once()

        # Try to finish off the queue data.
        for _ in range(self.qsize()):
            self._run_once()

        self.alive.clear()  # The thread is no longer running

    def _run_once(self):
        """Try to get data from the queue and run the operation."""
        try:
            # Wait for data and other arguments
            args, kwargs = self._operations.get(timeout=self._timeout)

            # Check for an internal command
            if "INTERNAL_PROCESS_COMMAND" in kwargs:
                try:
                    getattr(self, kwargs.pop('INTERNAL_PROCESS_COMMAND', None))(*args, **kwargs)
                except (AttributeError, Exception):
                    pass
                return

            # Check if this data should be executed
            if not self.stop_processing:
                # Run the data through the target function
                args = args or self._args
                kwargs = kwargs or self._kwargs
                self._target(*args, **kwargs)

            # If joinable queue mark task as done.
            mark_task_done(self._operations)
        except Empty:
            pass


# ========== Command Setup (Must be defined at the page level for pickling) ==========
class BaseCommand(object):
    def __init__(self, *args, **kwargs):
        super(BaseCommand, self).__init__()


class ObjectCommand(BaseCommand):
    def __init__(self, name='', *args, **kwargs):
        super(ObjectCommand, self).__init__()
        self.name = name
        self.args = args
        self.kwargs = kwargs


class ProcessCommand(ObjectCommand):
    pass


class ExecCommand(BaseCommand):
    def __call__(self, *args, **kwargs):
        pass


class CommandProcess(ContinuousProcess):
    """This process class is for running a command on an object in a separate process."""
    BaseCommand = BaseCommand
    ObjectCommand = ObjectCommand
    ProcessCommand = ProcessCommand
    ExecCommand = ExecCommand

    def __init__(self, target=None, name=None, args=None, kwargs=None, daemon=None, group=None):
        """Initialize the new process object.

        Args:
            target (object)[None]: Target object to run functions with in a separate process.
            name (str)[None]: Name of the new process.
            args (tuple)[None]: Unused in this class
            kwargs (dict)[None]: Unused in this class
            daemon (bool)[None]: If this process should be a daemon process. This is automatically forced to be False.
                Non-daemon process/threads call join when python exits.
            group (object)[None]: Not used in python multiprocessing at this time.
        """
        self._obj_cache = {}
        self._cmd_queue = mp.Queue()
        self._timeout = 2  # Timeout in seconds
        super(CommandProcess, self).__init__(target=None, name=name, args=args, kwargs=kwargs,
                                             daemon=daemon, group=group)

        # Manually set the target/object to trigger the cache.
        if target is not None:
            self.set_obj(target)

    def get_obj(self):
        """Return the target object for the commands."""
        return self._target

    def set_obj(self, value, cache_key=None):
        """Set the target object for the commands."""
        # Use the cache to save and get object
        if cache_key is None:
            cache_key = id(value)
        try:
            value = self._obj_cache[cache_key]
        except (KeyError, IndexError, TypeError):
            self._obj_cache[cache_key] = value

        # If main process send the object with the cache key to the other process.
        if self.is_main_process():
            self.send_cmd(self.ProcessCommand('set_obj', value, cache_key=cache_key))

        # Set the target object
        self._target = value

    @property
    def obj(self):
        """Return the target object for the commands."""
        return self.get_obj()

    @obj.setter
    def obj(self, value):
        """Set the target object for the commands."""
        self.set_obj(value)

    def get_timeout(self):
        """Return the queue timeout."""
        return self._timeout

    def set_timeout(self, value):
        """Set the queue timeout."""
        if self.was_started() and self.is_main_process():
            self.send_cmd(self.ProcessCommand('set_timeout', value))
        self._timeout = value

    @property
    def timeout(self):
        """Return the queue timeout."""
        return self.get_timeout()

    @timeout.setter
    def timeout(self, value):
        """Set the queue timeout."""
        self.set_timeout(value)

    @property
    def queue(self):
        """Return the operation queue."""
        return self._cmd_queue

    @queue.setter
    def queue(self, value):
        """Set the operation queue."""
        if self.was_started():
            raise RuntimeError('Cannot set the Queue when the process was already started.')
        if not isinstance(value, mp.Queue):
            raise ValueError('The given value must be a type of multiprocessing Queue not a threading Queue.')
        self._cmd_queue = value

    def send_cmd(self, name, *args, **kwargs):
        """Send a command to run on the other process.

        Args:
            name (str/BaseCommand): Name of the function or command object.
            *args (tuple/object): Positional arguments to pass into the function.
            **kwargs (dict/object): Keyword arguments to pass into the function.
        """
        if isinstance(name, self.BaseCommand):
            cmd = name
        else:
            cmd_type = kwargs.pop('COMMAND_TYPE', self.ObjectCommand)
            cmd = cmd_type(name, *args, **kwargs)
        self._cmd_queue.put_nowait(cmd)

    def qsize(self):
        """Return the queue size."""
        return self._cmd_queue.qsize()

    def run(self):
        """The thread will loop through running the set _target method (default _run()). This
        method can be paused and restarted.
        """
        while self.should_run():
            self._run_once()

        # Try to finish off the queue data.
        for _ in range(self.qsize()):
            self._run_once()

        self.alive.clear()  # The thread is no longer running

    def _run_once(self):
        """Try to get data from the queue and run the operation."""
        try:
            # Wait for data and other arguments
            cmd = self._cmd_queue.get(timeout=self.timeout)

            # Check the command type
            if isinstance(cmd, self.ExecCommand):
                func = cmd
                args = tuple()
                kwargs = {}
            elif isinstance(cmd, self.ProcessCommand):
                func = getattr(self, cmd.name, None)
                args = cmd.args
                kwargs = cmd.kwargs
            else:
                func = getattr(self._target, cmd.name, None)
                args = cmd.args
                kwargs = cmd.kwargs

            try:
                if func:
                    func(*args, **kwargs)
            except (AttributeError, TypeError, ValueError, Exception) as err:
                print_exception(err)

            # If joinable queue mark task as done.
            mark_task_done(self._cmd_queue)
        except Empty:
            pass
