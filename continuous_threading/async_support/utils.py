import sys
import asyncio
import inspect
import functools
import traceback


__all__ = ['get_loop', 'call', 'call_async', 'AsyncCallbackChain']


GLOBAL_LOOP = None


def get_loop():
    """Get the current async event loop."""
    global GLOBAL_LOOP
    if GLOBAL_LOOP is not None:
        return GLOBAL_LOOP

    try:
        GLOBAL_LOOP = asyncio.get_running_loop()
        return GLOBAL_LOOP
    except (AttributeError, RuntimeError, TypeError, RuntimeError, Exception):
        try:
            GLOBAL_LOOP = asyncio.get_event_loop()
            return GLOBAL_LOOP
        except (AttributeError, TypeError, RuntimeError, Exception):
            return GLOBAL_LOOP


def call(callback=None, *args, LOOP=None, **kwargs):
    """Call the given callback function. This function can be a normal function or a coroutine."""
    if LOOP is None:
        LOOP = get_loop()

    if inspect.iscoroutinefunction(callback):
        return LOOP.run_until_complete(callback(*args, **kwargs))
    elif callable(callback):
        return callback(*args, **kwargs)


async def call_async(callback=None, *args, LOOP=None, **kwargs):
    """Call the given callback function. This function can be a normal function or a coroutine."""
    if LOOP is None:
        LOOP = get_loop()

    if inspect.iscoroutinefunction(callback) or isinstance(callback, AsyncCallbackChain):
        return await callback(*args, **kwargs)
    elif callable(callback):
        return await LOOP.run_in_executor(None, functools.partial(callback, *args, **kwargs))


class AsyncCallbackChain(list):
    def append(self, callback):
        if (callable(callback) or inspect.iscoroutinefunction(callback)) and callback not in self:
            super(AsyncCallbackChain, self).append(callback)

    async def __call__(self, *args, **kwargs):
        for callback in self.callbacks:
            # Call the callback
            try:
                await call_async(callback, *args, **kwargs)
            except (AttributeError, RuntimeError, Exception) as err:
                await print_exception_async(err, self.msg, error_cls=err.__class__)


def get_traceback(exc=None):
    """Get the exception traceback or the system traceback."""
    _, _, sys_tb = sys.exc_info()
    try:
        return exc.__traceback__
    except (AttributeError, Exception):
        return sys_tb


def print_exception(exc, msg=None, error_cls=RuntimeError):
    """Print the given exception. If a message is given it will be prepended to the exception message with a \n.

    Args:
        exc (Exception): Exception that was raised.
        msg (str)[None]: Additional message to prepend to the exception.
        error_cls (Exception)[CommunicationError]: New Exception class to print the exception as.
    """
    # Prepend the message to the exception if given
    if msg:
        msg = "\n".join((msg, str(exc)))
    else:
        msg = str(exc)

    try:
        exc_tb = get_traceback(exc)
        traceback.print_exception(error_cls, error_cls(msg), exc_tb)
    except (Exception):
        pass  # some version error happened. Traceback may have changed. Python keeps breaking things


async def print_exception_async(exc, msg=None, error_cls=RuntimeError, loop=None):
    """Print the given exception. If a message is given it will be prepended to the exception message with a \n.

    Args:
        exc (Exception): Exception that was raised.
        msg (str)[None]: Additional message to prepend to the exception.
        error_cls (Exception)[CommunicationError]: New Exception class to print the exception as.
        loop (asyncio.AbstractEventLoop)[None]: loop to run with.
    """
    loop = loop or get_loop()
    return await loop.run_in_executor(None, print_exception, exc, msg, error_cls)
