import asyncio


class AsyncioTimerCallback:
    def __init__(self, timeout, callback, args=()):
        self._timeout = timeout
        self._callback = callback
        self._args = args
        self._task = None

    def start(self):
        self._task = asyncio.ensure_future(self._job(self._timeout, self._callback, self._args))

        return self

    @staticmethod
    async def _job(timeout, callback, args):
        await asyncio.sleep(timeout)
        callback(*args)

    def cancel(self):
        if self._task:
            self._task.cancel()
            self._task = None
