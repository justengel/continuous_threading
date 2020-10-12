import time
import continuous_threading

# # Does not work. Process halted before atexit
# import atexit
# atexit.register(continuous_threading.shutdown)


c = 0

def count():
    global c

    c += 1
    time.sleep(1)


th = continuous_threading.ContinuousThread(target=count)
th.start()

time.sleep(2)
print('Count:', c)

# Process will exit without a problem
