import asyncio_event_looper


class Context:
    def __init__(self, datagram_task, stream_task):
        self.datagram_task = datagram_task
        self.stream_task = stream_task


async def init_handler(looper):
    datagram_task = await looper.register_datagram_server('EVENT_DGRAM_CONN', 'EVENT_DGRAM', 65534)
    stream_task = await looper.register_stream_server('EVENT_STREAM_CONN', 'EVENT_STREAM', 65534)

    looper.set_context(Context(datagram_task, stream_task))


async def exit_handler(looper):
    context = looper.get_context()

    context.datagram_task.cancel()
    context.stream_task.cancel()


async def datagram_conn(looper, param):
    pass


async def datagram(looper, param):
    pass


async def stream_conn(looper, param):
    pass


async def stream(looper, param):
    #self.transport.close()
    pass


handler_map = {
                  'EVENT_DGRAM_CONN': datagram_conn,
                  'EVENT_DGRAM': datagram,
                  'EVENT_STREAM_CONN': stream_conn,
                  'EVENT_STREAM': stream
}


async def event_handler(looper, event, param):
    print('{}: {}'.format(event, param))

    await handler_map[event](looper, param)


if __name__ == '__main__':
    _loop = asyncio_event_looper.AsyncioEventLooper()

    _loop.run(init_handler, event_handler, exit_handler)

