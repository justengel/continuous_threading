"""
threading._shutdown changed. It used to call "join" on every non-daemon Thread. This kind of kills the purpose for
this library. This library was created to automatically join and safely clean up long running threads. This module
changes "_shutdown" to "join" all non-daemon Threads again.
"""
import threading


__all__ = ['shutdown', 'get_shutdown_timeout', 'set_shutdown_timeout', 'get_allow_shutdown', 'set_allow_shutdown',
           'threading_shutdown', 'custom_shutdown', 'using_custom_shutdown', 'set_shutdown', 'reset_shutdown']


SHUTDOWN_TIMEOUT = 1
ALLOW_SHUTDOWN = False


def get_shutdown_timeout():
    """Return the shutdown timeout value."""
    global SHUTDOWN_TIMEOUT
    return SHUTDOWN_TIMEOUT


def set_shutdown_timeout(value):
    """Set the shutdown timeout value (int)."""
    global SHUTDOWN_TIMEOUT
    SHUTDOWN_TIMEOUT = value


def get_allow_shutdown():
    """Return if "shutdown" automatically calls the thread allow_shutdown."""
    global ALLOW_SHUTDOWN
    return ALLOW_SHUTDOWN


def set_allow_shutdown(value):
    """Set if "shutdown" automatically calls the thread allow_shutdown."""
    global ALLOW_SHUTDOWN
    ALLOW_SHUTDOWN = value


def shutdown(timeout=None, allow_shutdown=True):
    """Join and allow all threads to shutdown.

    Python's threading._shutdown may hang preventing the process from exiting completely. It uses the "_tstate_lock"
    to wait for every thread to "join". Python's threading._shutdown used to call join to achieve the same behavior.

    This library overrides threading._shutdown to "join" all Threads before the process ends.

    You may want to put this at the end of your code. Atexit will not work for this.

    I did not have a problem with Python 3.4. I noticed this issue in Python 3.8. I do not know
    when this changed and stopped working.

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

    Args:
        timeout (int/float)[None]: Timeout argument to pass into every thread's join method.
        allow_shutdown (bool)[True]: If True also call allow_shutdown on the thread.
    """
    if allow_shutdown is None:
        allow_shutdown = get_allow_shutdown()

    for th in threading.enumerate():
        # Join the thread if not joined
        try:
            if th is not threading.main_thread() and th.is_alive() and not th.isDaemon():
                th.join(timeout)
        except (AttributeError, ValueError, TypeError, Exception) as err:
            print(err)

        # Allow threading._shutdown() to continue
        if allow_shutdown:
            try:
                th.allow_shutdown()
            except (AttributeError, Exception):
                pass


# Save the original threading._shutdown function
threading_shutdown = threading._shutdown


def custom_shutdown():
    """Safely shutdown the threads."""
    shutdown(get_shutdown_timeout(), get_allow_shutdown())
    threading_shutdown()


def using_custom_shutdown():
    """Return True if the threading._shutdown function is using the custom shutdown function."""
    return threading._shutdown != threading_shutdown


def set_shutdown(func=None):
    """Set the threading._shutdown function to "join" all threads."""
    if func is None:
        func = custom_shutdown
    threading._shutdown = func


def reset_shutdown():
    """Reset the threading._shutdown function to use its original function."""
    threading._shutdown = threading_shutdown


# Change threading._shutdown to use our custom function
set_shutdown()

