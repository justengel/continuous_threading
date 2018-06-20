
from continuous_threading import threading_utils


class FakeTestLock(object):
    def __init__(self):
        self.was_in_context = False
        self.in_context = False

    def __enter__(self):
        self.was_in_context = True
        self.in_context = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.in_context = False


def test_make_thread_safe_function():
    class A(object):
        x = 1

        def get_x(self):
            return self.x

    class B(A):
        lock = FakeTestLock()
        get_x = threading_utils.make_thread_safe(A.get_x)

    b = B()
    assert not b.lock.in_context
    assert not b.lock.was_in_context
    b.get_x()
    assert not b.lock.in_context
    assert b.lock.was_in_context

def test_make_thread_safe_function_diff_lock_varname():
    class A(object):
        x = 1

        def get_x(self):
            return self.x

    class B(A):
        my_lock = FakeTestLock()
        get_x = threading_utils.make_thread_safe('my_lock', A.get_x)

    b = B()
    assert not b.my_lock.in_context
    assert not b.my_lock.was_in_context
    b.get_x()
    assert not b.my_lock.in_context
    assert b.my_lock.was_in_context


def test_make_thread_safe_decorator():
    class A(object):
        x = 1

        def get_x(self):
            return self.x

    class B(A):
        lock = FakeTestLock()

        @threading_utils.make_thread_safe
        def get_x(self):
            return self.x

    b = B()
    assert not b.lock.in_context
    assert not b.lock.was_in_context
    b.get_x()
    assert not b.lock.in_context
    assert b.lock.was_in_context


def test_make_thread_safe_decorator_diff_lock_varname():
    class A(object):
        x = 1

        def get_x(self):
            return self.x

    class B(A):
        my_lock = FakeTestLock()

        @threading_utils.make_thread_safe('my_lock')
        def get_x(self):
            return self.x

    b = B()
    assert not b.my_lock.in_context
    assert not b.my_lock.was_in_context
    b.get_x()
    assert not b.my_lock.in_context
    assert b.my_lock.was_in_context


if __name__ == '__main__':
    test_make_thread_safe_function()
    test_make_thread_safe_function_diff_lock_varname()
    test_make_thread_safe_decorator()
    test_make_thread_safe_decorator_diff_lock_varname()

    print("All tests passed successfully!")
