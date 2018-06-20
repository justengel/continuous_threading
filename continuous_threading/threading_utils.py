import functools


def make_thread_safe(lock_varname="lock", func=None):
    """Decorate a function making it threadsafe by using the threading lock that matches the lock_varname.

    Example:

        ..code-block:: python

            >>> import threading
            >>>
            >>> class A(object):
            >>>     x = 1
            >>>     def get_x(self):
            >>>         return self.x
            >>>
            >>>     def set_x(self, x):
            >>>         self.x = x
            >>>
            >>> class B(A):
            >>>     lock = threading.RLock()
            >>>     get_x = make_thread_safe(A.get_x)
            >>>
            >>>     @make_thread_safe
            >>>     def set_x(self, x):
            >>>         self.x = x * 2
            >>>
            >>> class C(B):
            >>>     lock2 = threading.RLock()
            >>>
            >>>     @make_thread_safe('lock2')
            >>>     def set_lock2(self):
            >>>         print("I have lock2")

    Args:
        lock_varname (str/method)['lock']: Threading lock variable name or
            a function to decorate with 'lock' variable being a threading.Lock
        func (function/method) [None]: Function to wrap.

    Returns:
        wrap (function): Function that was decorated/wrapped or a function that will decorate a function.
    """
    if not isinstance(lock_varname, str):
        # Function was given decorate the function
        func = lock_varname
        lock_varname = 'lock'

    if func is None:
        # Return a decorator
        def real_decorator(func):
            return make_thread_safe(lock_varname, func)
        return real_decorator

    elif isinstance(func, property):
        # Make all of a properties functions thread safe
        fget = None
        fset = None
        fdel = None
        if func.fget:
            fget = make_thread_safe(lock_varname, func.fget)
        if func.fset:
            fset = make_thread_safe(lock_varname, func.fset)
        if func.fdel:
            fdel = make_thread_safe(lock_varname, func.fdel)
        return property(fget, fset, fdel, func.__doc__)

    else:
        # Return the new function which wraps the old function
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with getattr(args[0], lock_varname):
                return func(*args, **kwargs)
        return wrapper
