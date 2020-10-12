import time
import threading

# # Does not work. Process halted before atexit
# import atexit
# atexit.register(continuous_threading.shutdown)


c = 0

def count_loop():
    global c

    while True:
        c += 1
        time.sleep(1)


th = threading.Thread(target=count_loop)
th.start()

time.sleep(2)
print('Count:', c)

# Calling join will not work because of "while True"
# th.join(1)

# Could exit if th._tstate_lock.release() was called. This works without calling join. Could cause problems?

# Process will not exit
print('Process will not exit!')
