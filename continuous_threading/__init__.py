from collections import deque
# Required threading classes
from threading import Thread as BaseThread, Event, Timer

# threading imports that are not required. Just a shortcut
try:
    from threading import Lock, RLock, Condition, Semaphore, BoundedSemaphore, \
        active_count, current_thread, enumerate, setprofile, settrace
except ImportError:
    pass  # Your threading library has problems, but I don't care
try:
    from threading import main_thread, Barrier, BrokenBarrierError
except ImportError:
    pass  # Running Python 2.7?

from .timer_utils import start_timer, stop_timer
from .threading_utils import make_thread_safe
from .safe_threading import Queue, Empty, Thread, ContinuousThread, PausableThread, OperationThread, PeriodicThread
