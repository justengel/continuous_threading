"""
Trying to find out the best way to clear variables when a thread exits.

CONCLUSION:
    The best option seems to force a non-daemon thread and override the join method to call a clean up function.
"""
from __future__ import print_function
import threading


def _run_thread_forever(li, alive_event_is_set=None):
    if alive_event_is_set is None:
        alive_event_is_set = lambda: True

    try:
        li[0] = False
    except:
        li.append(False)

    try:
        while alive_event_is_set():
            pass
    finally:
        li[0] = True
        print(li[0])


def run_my_situation():
    li = []
    th = threading.Thread(target=_run_thread_forever, args=(li,))
    # th.daemon = False  # Program never exits
    th.daemon = True  # Program exits, but never cleans up variables even with try finally.
    th.start()


def run_custom_thread():
    class Thread(threading.Thread):
        def __init__(self, *args, **kwargs):
            self.alive_event = threading.Event()
            super(Thread, self).__init__(*args, **kwargs)

        def join(self, *args, **kwargs):
            print('here')
            self.alive_event.clear()
            super(Thread, self).join(*args, **kwargs)

    alive_event = threading.Event()
    alive_event.set()
    li = []
    th = Thread(target=_run_thread_forever, args=(li, alive_event.is_set))
    th.alive_event = alive_event
    th.daemon = False  # Works successfully!
    # th.daemon = True  # Variables are not cleaned up. Join is not called.
    th.start()


def run_custom_thread_bootstrap():
    """This is what calls the run function. Can I override this to force cleanup values?"""

    class Thread(threading.Thread):
        def __init__(self, *args, **kwargs):
            self.alive_event = threading.Event()
            super(Thread, self).__init__(*args, **kwargs)

        def _bootstrap_inner(self):
            print('in bootstrap')
            try:
                self._set_ident()
                self._set_tstate_lock()
                self._started.set()
                with threading._active_limbo_lock:
                    threading._active[self._ident] = self
                    del threading._limbo[self]

                if threading._trace_hook:
                    threading._sys.settrace(threading._trace_hook)
                if threading._profile_hook:
                    threading._sys.setprofile(threading._profile_hook)

                try:
                    self.run()
                except SystemExit:
                    pass
                except:
                    # If sys.stderr is no more (most likely from interpreter
                    # shutdown) use self._stderr.  Otherwise still use sys (as in
                    # _sys) in case sys.stderr was redefined since the creation of
                    # self.
                    if threading._sys and threading._sys.stderr is not None:
                        print("Exception in thread %s:\n%s" %
                              (self.name, threading._format_exc()), file=threading._sys.stderr)
                    elif self._stderr is not None:
                        # Do the best job possible w/o a huge amt. of code to
                        # approximate a traceback (code ideas from
                        # Lib/traceback.py)
                        exc_type, exc_value, exc_tb = self._exc_info()
                        try:
                            print((
                                "Exception in thread " + self.name +
                                " (most likely raised during interpreter shutdown):"), file=self._stderr)
                            print((
                                "Traceback (most recent call last):"), file=self._stderr)
                            while exc_tb:
                                print((
                                    '  File "%s", line %s, in %s' %
                                    (exc_tb.tb_frame.f_code.co_filename,
                                        exc_tb.tb_lineno,
                                        exc_tb.tb_frame.f_code.co_name)), file=self._stderr)
                                exc_tb = exc_tb.tb_next
                            print(("%s: %s" % (exc_type, exc_value)), file=self._stderr)
                        # Make sure that exc_tb gets deleted since it is a memory
                        # hog; deleting everything else is just for thoroughness
                        finally:
                            del exc_type, exc_value, exc_tb
                finally:
                    # Prevent a race in
                    # test_threading.test_no_refcycle_through_target when
                    # the exception keeps the target alive past when we
                    # assert that it's dead.
                    #XXX self._exc_clear()
                    pass
            finally:
                self.close()  # ADDED CLOSE FUNCTION

                with threading._active_limbo_lock:
                    try:
                        # We don't call self._delete() because it also
                        # grabs _active_limbo_lock.
                        del threading._active[threading.get_ident()]
                    except:
                        pass

        def close(self):
            print('here')
            self.alive_event.clear()

    alive_event = threading.Event()
    alive_event.set()
    li = []
    th = Thread(target=_run_thread_forever, args=(li, alive_event.is_set))
    th.alive_event = alive_event
    th.daemon = False  # Does not seem to work (Never closes)
    # th.daemon = True  # Does not call the close function
    th.start()


def run_custom_thread_bootstrap_condensed():
    class Thread(threading.Thread):
        def __init__(self, *args, **kwargs):
            self.alive_event = threading.Event()
            super(Thread, self).__init__(*args, **kwargs)

        def _bootstrap_inner(self):
            try:
                super(Thread, self)._bootstrap_inner()
            finally:
                self.close()

        def close(self):
            print('here')
            self.alive_event.clear()

    alive_event = threading.Event()
    alive_event.set()
    li = []
    th = Thread(target=_run_thread_forever, args=(li, alive_event.is_set))
    th.alive_event = alive_event
    th.daemon = False  # Does not seem to work (Never closes)
    # th.daemon = True  # Does not call the close function
    th.start()


if __name__ == '__main__':
    # run_my_situation()
    run_custom_thread()
    # run_custom_thread_bootstrap()
    # run_custom_thread_bootstrap_condensed()
