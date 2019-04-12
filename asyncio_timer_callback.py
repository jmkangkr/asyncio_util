import asyncio
import inspect
import logging
import traceback


class AsyncioTimerCallback:
    def __init__(self, logger_name, timeout, callback, args=()):
        if logger_name:
            self._logger = logging.getLogger(logger_name)
        else:
            self._logger = None

        self._timeout = timeout
        self._callback = callback
        self._args = args
        self._task = None

    def start(self):
        self._task = asyncio.ensure_future(self._job(self._timeout, self._callback, self._args, self._logger))

        return self

    @staticmethod
    async def _job(timeout, callback, args, logger):
        await asyncio.sleep(timeout)
        if inspect.iscoroutinefunction(callback):
            await callback(*args)
        else:
            try:
                callback(*args)
            except Exception as e:
                if logger:
                    logger.info("Exception occured in AsyncioTimerCallback job: {}\n{}".format(str(e), traceback.format_exc()))
                else:
                    print("Exception occured in AsyncioTimerCallback job: {}\n{}".format(str(e), traceback.format_exc()))

    def cancel(self):
        if self._task:
            self._task.cancel()
            self._task = None
