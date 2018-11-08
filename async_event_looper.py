import asyncio
import datetime
import functools
import signal


_SYS_EXIT = "_SYS_EXIT"


class AsyncioEventLooper:
    def __init__(self):
        self._loop = asyncio.get_event_loop()
        self._q = asyncio.Queue()
        self._init_handler = None
        self._event_handler = None
        self._exit_handler = None
        self._context = None

        self._add_default_signal_handler()

    def _default_signal_handler(self, signame):
        self._q.put_nowait((_SYS_EXIT, signame))

    def _add_default_signal_handler(self):
        for signame in ('SIGINT', 'SIGTERM'):
            self._loop.add_signal_handler(getattr(signal, signame), functools.partial(self._default_signal_handler, signame))

    async def _task_generate_event(self, event, param, initial_sleep_time, time_delta):
        if initial_sleep_time > 0.0:
            await asyncio.sleep(initial_sleep_time)
        await self._q.put((event, param))

        if time_delta is not None:
            next_put_time = datetime.datetime.now() + time_delta
            while True:
                sleep_time = (next_put_time - datetime.datetime.now()).total_seconds()
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                await self._q.put((event, param))
                next_put_time += time_delta

    async def _run_loop(self):
        keep_running = True

        if self._init_handler:
            keep_running = await self._init_handler(self)

        while keep_running is not False:
            event, param = await self._q.get()

            if event == _SYS_EXIT:
                if self._exit_handler:
                    await self._exit_handler(self)
                for task in asyncio.Task.all_tasks():
                    if task is not asyncio.tasks.Task.current_task():
                        task.cancel()
                await asyncio.sleep(1.0)
                break

            keep_running = await self._event_handler(self, event, param)

    def generate_event_nowait(self, event, param):
        self._q.put_nowait((event, param))

    async def generate_event(self, event, param):
        return self._loop.create_task(self._task_generate_event(event, param, 0.0, None))

    async def generate_event_after(self, event, param, seconds):
        return self._loop.create_task(self._task_generate_event(event, param, seconds, None))

    async def generate_event_after_periodically(self, event, param, seconds, period):
        return self._loop.create_task(self._task_generate_event(event, param, seconds, datetime.timedelta(seconds=period)))

    async def generate_event_at(self, event, param, date_time):
        initial_sleep_time = (date_time - datetime.datetime.now()).total_seconds()
        return self._loop.create_task(self._task_generate_event(event, param, initial_sleep_time, None))

    async def generate_event_at_perodically(self, event, param, date_time, time_delta):
        initial_sleep_time = (date_time - datetime.datetime.now()).total_seconds()
        return self._loop.create_task(self._task_generate_event(event, param, initial_sleep_time, time_delta))

    async def register_async_func(self, async_func):
        return self._loop.create_task(async_func)

    def stop(self):
        self._q.put_nowait((_SYS_EXIT, None))

    def add_signal_handler(self, signal_names, signal_handler):
        for signame in signal_names:
            self._loop.add_signal_handler(getattr(signal, signame), functools.partial(signal_handler, self, signame))

    def set_context(self, context):
        self._context = context

    def get_context(self):
        return self._context

    def run(self, init_handler, event_handler, exit_handler):
        self._init_handler = init_handler
        self._event_handler = event_handler
        self._exit_handler = exit_handler
        self._loop.run_until_complete(self._run_loop())
        asyncio.gather(*asyncio.Task.all_tasks(), return_exceptions=True)
        self._loop.stop()
        self._loop.close()


#-----------------------------------------------------------------------------------------------------------------------
# Test

class ClientContext:
    def __init__(self):
        self.count = 0


async def init_handler(looper):
    await looper.generate_event_after_periodically('event_update3', None, 7, 3)
    await looper.generate_event_after_periodically('event_update5', None, 0, 5)
    looper.set_context(ClientContext())
    return True


async def exit_handler(looper):
    print('Exiting...')


async def event_handler(looper, event, param):
    context = looper.get_context()
    print("{:3} {} {}".format(context.count, datetime.datetime.now().strftime('%H:%M:%S.%f')[:-4], event))
    context.count += 1

    if context.count > 10:
        looper.stop()
    return True


if __name__ == "__main__":
    _looper = AsyncioEventLooper()

    _looper.run(init_handler, event_handler, exit_handler)
