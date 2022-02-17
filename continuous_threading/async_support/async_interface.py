import asyncio
import inspect
from .utils import get_loop, call_async


__all__ = ['Event', 'Lock', 'Condition', 'Queue', 'QueueFull', 'QueueEmpty',
           'AsyncTask', 'ContinuousTask']


Event = asyncio.Event
Lock = asyncio.Lock
Condition = asyncio.Condition
Queue = asyncio.Queue
QueueFull = asyncio.QueueFull
QueueEmpty = asyncio.QueueEmpty
CancelledError = asyncio.CancelledError


class AsyncTask:
    """Basic thread that contains context managers for use with the with statement.

    Note:
        There is a close_warning property. If this is set to True and this thread does not join successfully then
        a timer will alert the user that the thread did not join properly.

    Notes:
        Daemon threads are killed as Python is exiting. A Daemon thread with an infinite loop will get stuck and not
        close properly. These threads are setup to handle closing a looping thread.
    """

    def __init__(self, target=None, name=None, args=None, kwargs=None, kill=None, loop=None, **kwds):
        super(AsyncTask, self).__init__()

        self._task = None
        self._loop = loop
        self.name = name
        self._target = target
        self._args = args or tuple()
        self._kwargs = kwargs or dict()
        self.kill = kill or asyncio.Event()

        if self._target is None and hasattr(self, '_run'):
            self._target = self._run

    @property
    def loop(self):
        """Return the event loop for this object."""
        return getattr(self, '_loop', None) or get_loop()

    @loop.setter
    def loop(self, loop):
        setattr(self, '_loop', loop)

    def is_running(self):
        """Return if the async task is alive and running"""
        return not self.kill.is_set() and self._task is not None

    is_alive = is_running

    def start(self):
        self.kill.clear()
        if self._task is None:
            self._task = self.loop.create_task(self.run(), name=self.name)
        return self

    async def run(self):
        await call_async(self._target, *self._args, LOOP=self.loop, **self._kwargs)
        self.kill.set()

    async def _run(self, *args, **kwargs):
        """Default function target to run if a target is not given."""
        pass

    def stop(self):
        """Stop the thread."""
        self.kill.set()
        try:
            self._task.cancel()
        except (AttributeError, Exception):
            pass
        self._task = None

    def close(self):
        """Close the thread (clean up variables)."""
        self.stop()

    def join(self, timeout=None):
        """Properly close the thread."""
        try:
            self.kill.set()
            self.close()  # Cleanup function
        except (AttributeError, Exception):
            pass
        self._task = None

    def __await__(self):
        return self.run().__await__()

    async def __aenter__(self):
        self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            self.join(0)
        except (AttributeError, Exception):
            pass
        return exc_type is None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.join(0)
        except (AttributeError, Exception):
            pass
        return exc_type is None


class ContinuousTask(AsyncTask):
    """Thread that is continuously running and closes properly. Do not override the run method.
    If you are using this class with inheritance override the '_run' method.
    """
    def __init__(self, target=None, name=None, args=None, kwargs=None, init=None, iargs=None, ikwargs=None,
                 kill=None, loop=None, **kwds):
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
            alive (threading.Event)[None]: Alive event to indicate if the thread is alive.
        """
        # Thread properties
        self.init = init
        self.iargs = iargs or tuple()
        self.ikwargs = ikwargs or dict()

        super(ContinuousTask, self).__init__(target=target, name=name, args=args, kwargs=kwargs, kill=kill, loop=loop,
                                             **kwds)

    def _run(self, *args, **kwargs):
        """Run method called if a target is not given to the thread. This method should be overridden if inherited."""
        pass

    async def run_init(self):
        """Run the init function and return the args and kwargs."""
        args = self._args
        kwargs = self._kwargs
        if callable(self.init):
            kwds = await call_async(self.init, *self.iargs, LOOP=self.loop, **self.ikwargs)
            if isinstance(kwds, dict) and len(kwds) > 0:
                kwds.update(kwargs)
                kwargs = kwds
        return args, kwargs

    async def run(self):
        """The thread will loop through running the set _target method (default _run()). This
        method can be paused and restarted.
        """
        args, kwargs = await self.run_init()

        while self.is_alive():
            await call_async(self._target, *args, LOOP=self.loop, **kwargs)
            await asyncio.sleep(0)  # Release async event loop if target function did not really wait?

        self.kill.set()
