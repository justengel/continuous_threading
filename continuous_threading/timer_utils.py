import threading


def start_timer(timeout, callback):
    """Start a timer using the threading library (in seconds)."""
    tmr = threading.Timer(timeout, callback)
    tmr.start()
    return tmr
# end _start_threading_timer


def stop_timer(tmr):
    """Stop the timer."""
    try:
        tmr.cancel()
        tmr.join()
    except (AttributeError, RuntimeError):
        pass
# stop_timer
