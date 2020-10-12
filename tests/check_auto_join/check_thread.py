import time
import continuous_threading

# # Does not work. Process halted before atexit
# import atexit
# atexit.register(continuous_threading.shutdown)


c = 0

def count_loop():
    global c

    while True:
        c += 1
        time.sleep(1)


th = continuous_threading.Thread(target=count_loop)
th.start()

time.sleep(2)
print('Count:', c)

# threading._shutdown will wait for thread to join forever. Need to free
# continuous_threading.shutdown(0)  # Need timeout for "while True"

# Alternative. This does not call join normally. continuous_threading threading._shutdown override does call "join".
th.allow_shutdown()  # Release "_tstate_lock" allowing threading._shutdown to continue

# Process will exit
