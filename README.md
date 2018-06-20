# continuous_threading
This library provides several classes to help manage threads that run continuously.

There are some problems with threads runing continuously in a loop. Calculation threads are greedy and keep running 
which starves other threads. Another problem is if you don't exit an infinite loop in a thread it may keep running 
after python has tried to exit. This library aims to solve those problems.

## Thread context manager
This library turns threads into a context manager which automatically starts and stops threads.

```python
import continuous_threading

thread_success = [False]

def do_something():
    print('here')
    thread_success[0] = True


with continuous_threading.Thread(target=do_something):
    print('in context')
    
assert thread_success[0] is True
```

## ContinuousThread
The ContinuousThread is a simple thread in an infinite while loop. The while loop keeps looping while the thread 
alive Event is set. Call `thread.stop()`, `thread.close()`, or `thread.join()` to stop the thread. The thread should 
also stop automatically when the python program is exiting/closing.

```python
import continuous_threading

class CountingThread(continuous_threading.ContinuousThread):
    def __init__(self):
        super().__init__()
        self.counter = 0
        
    def _run(self):
        self.counter += 1


with CountingThread() as th:
    print('in context')
    
assert th.counter > 0
print("Simple context manager print caused %d thread iterations" % th.counter)
```

Example of start and stop methods.
```python
import time
import continuous_threading

class CountingThread(continuous_threading.ContinuousThread):
    def __init__(self):
        super().__init__()
        self.counter = 0
        
    def _run(self):
        self.counter += 1

th = CountingThread()
th.start()
time.sleep(0.1)
th.stop()  # or th.close() or th.join()
    
assert th.counter > 0
print("Simple context manager print caused %d thread iterations" % th.counter)
```

## PausableThread
A continuous thread that can be stopped and started again.

```python
import time
import continuous_threading


counter = [0]

def inc_counter():
    counter[0] += 1
    
th = continuous_threading.PausableThread(target=inc_counter)

th.start()
time.sleep(0.1)

th.stop()
time.sleep(0.1)

value = counter[0]
assert value > 0

time.sleep(0.1)
assert value == counter[0]

th.start()
time.sleep(0.1)
assert counter[0] > value
```

Again this can be used as a context manager.
```python
import time
import continuous_threading

class CountingThread(continuous_threading.PausableThread):
    def __init__(self):
        super().__init__()
        self.counter = 0
        
    def _run(self):
        self.counter += 1
        
with CountingThread() as th:
    time.sleep(0.1)
    th.stop()
    value = th.counter
    assert value > 0
    
    time.sleep(0.1)
    assert value == th.counter
    
    th.start()
    time.sleep(0.1)
    assert th.counter > value
```

## OperationThread
Add data to a queue which will be operated on in a separate thread.

```python
import time
import continuous_threading


values = []

def run_calculation(data1, data2):
    values.append(data1 + data2)
    
th = continuous_threading.OperationThread(target=run_calculation)
th.start()
th.add_data(1, 1)
time.sleep(0.1)

assert len(values) > 0
assert values[0] == 2

th.add_data(2, 2)
th.add_data(3, 3)
th.add_data(4, 4)
th.add_data(5, 5)

time.sleep(0.1)
assert values == [2, 4, 6, 8, 10]
```
