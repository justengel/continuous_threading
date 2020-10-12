from .__meta__ import version as __version__


__all__ = [
    # Base threading library
    'deque', 'BaseThread', 'Event', 'Timer', 'Lock', 'RLock', 'Condition', 'Semaphore', 'BoundedSemaphore',
    'active_count', 'current_thread', 'enumerate', 'setprofile', 'settrace', 'main_thread', 'Barrier',
    'BrokenBarrierError',

    # Timer utils
    'start_timer', 'stop_timer',

    # Threading utils
    'make_thread_safe',

    # continuous_threading
    'is_py27', 'Queue', 'Empty',
    'Thread', 'ContinuousThread', 'PausableThread', 'OperationThread', 'PeriodicThread',

    # Fix threading._shutdown
    'threading_shutdown', 'get_shutdown_timeout', 'set_shutdown_timeout',
    'get_allow_shutdown', 'set_allow_shutdown', 'shutdown',
    'using_custom_shutdown', 'set_shutdown', 'reset_shutdown',

    # Multiprocessing
    'ProcessError', 'MpEvent', 'MpQueue', 'MpJoinableQueue', 'MpSimpleQueue',
    'is_parent_process_alive', 'mark_task_done',
    'Process', 'ContinuousProcess', 'PausableProcess', 'PeriodicProcess', 'OperationProcess',
    'BaseCommand', 'ObjectCommand', 'ProcessCommand', 'ExecCommand', 'CommandProcess'
    ]


from collections import deque

# ===== Required threading classes =====
from threading import Thread as BaseThread, Event, Timer

# threading imports that are not required. Just a shortcut
try:
    from threading import Lock, RLock, Condition, Semaphore, BoundedSemaphore, \
        active_count, current_thread, enumerate, setprofile, settrace
except ImportError as err:
    # Your threading library has problems, but I don't care
    class ThreadingLibraryError:
        error = err
        def __new__(cls, *args, **kwargs):
            raise EnvironmentError('Cannot import from threading library! ' + str(cls.error))

    Lock = ThreadingLibraryError
    RLock = ThreadingLibraryError
    Condition = ThreadingLibraryError
    Semaphore = ThreadingLibraryError
    BoundedSemaphore = ThreadingLibraryError
    active_count = ThreadingLibraryError
    current_thread = ThreadingLibraryError
    enumerate = ThreadingLibraryError
    setprofile = ThreadingLibraryError
    settrace = ThreadingLibraryError

try:
    from threading import main_thread, Barrier, BrokenBarrierError
except ImportError:
    # Running Python 2.7?
    class ThreadingLibraryError(Exception):
        error = err
        def __new__(cls, *args, **kwargs):
            raise EnvironmentError('Cannot import from threading library! ' + str(cls.error))

    main_thread = ThreadingLibraryError
    Barrier = ThreadingLibraryError
    BrokenBarrierError = ThreadingLibraryError


# ===== Timer utils =====
from .timer_utils import start_timer, stop_timer

# ===== Continuous Threading Objects =====
from .threading_utils import make_thread_safe
from .safe_threading import is_py27, Queue, Empty, \
    Thread, ContinuousThread, PausableThread, OperationThread, PeriodicThread

# ===== Fix threading._shutdown =====
from .fix_threading_shutdown import \
    shutdown, get_shutdown_timeout, set_shutdown_timeout, get_allow_shutdown, set_allow_shutdown, \
    threading_shutdown, custom_shutdown, using_custom_shutdown, set_shutdown, reset_shutdown

# ===== Multiprocessing Objects =====
try:
    from .safe_multiprocessing import ProcessError, MpEvent, MpQueue, MpJoinableQueue, MpSimpleQueue, \
        is_parent_process_alive, mark_task_done, \
        Process, ContinuousProcess, PausableProcess, PeriodicProcess, OperationProcess, \
        BaseCommand, ObjectCommand, ProcessCommand, ExecCommand, CommandProcess
except (ImportError, Exception):
    ProcessError = None
    MpEvent = None
    MpQueue = None
    MpJoinableQueue = None
    MpSimpleQueue = None
    is_parent_process_alive = None
    mark_task_done = None
    Process = None
    ContinuousProcess = None
    PausableProcess = None
    PeriodicProcess = None
    OperationProcess = None
    BaseCommand = ObjectCommand = ProcessCommand = ExecCommand = None
    CommandProcess = None
