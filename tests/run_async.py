import asyncio


async def run_task():
    from continuous_threading import AsyncTask

    t = [False]

    async def run_test():
        t[0] = True

    tsk = AsyncTask(target=run_test)
    await tsk
    assert t[0]

    # Run using create task
    t[0] = False
    tsk.start()  # Start the task non-blocking
    assert not t[0], 'The task should not have run yet'
    await asyncio.sleep(0.001)  # Let the task run while await is blocking
    assert t[0]
    tsk.stop()


async def run_continuous_task():
    from continuous_threading import ContinuousTask

    t = []

    async def run_test():
        t.append(True)

    tsk = ContinuousTask(target=run_test)
    tsk.start()
    await asyncio.sleep(0.01)
    assert len(t) > 1
    tsk.stop()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(
            run_task(),
            run_continuous_task()
            ))


if __name__ == '__main__':
    main()
    print('All tasks passed successfully!')
