import sys
import ssl
import queue
import atexit
import signal
import asyncio
import threading
import contextvars
from types import FrameType
from typing import Optional

from utils.constants import Settings, Messages
from utils.functions import create_logger, cancel_tasks


async def run_app() -> None:
    try:
        rd, wr = await asyncio.open_connection(
            Settings.SERVER_HOST.value,
            Settings.SERVER_PORT.value,
            ssl=ssl_context.get()
        )
    except OSError:
        logger.error(
            Messages.CONNECTION_HAS_NOT_BEEN_MADE.value,
            exc_info=True
        )
    else:
        reader.set(rd)
        writer.set(wr)

        process_data_task = asyncio.create_task(
            process_data(),
            name=process_data.__name__
        )
        backgroud_tasks.add(process_data_task)
        process_data_task.add_done_callback(backgroud_tasks.discard)

        await asyncio.sleep(0)
        logger.info(Messages.CONNECTION_HAS_BEEN_MADE.value)

        await has_termination_been_required.wait()
        logger.info(Messages.CLIENT_HAS_BEEN_STOPPED.value)
        await stop_app()


async def stop_app() -> None:
    await cancel_tasks()
    wr = writer.get()

    try:
        wr.close()
        await wr.wait_closed()
    except OSError:
        logger.error(Messages.SOCKET_ERROR.value.client_close)


async def process_data() -> None:
    threading.Thread(target=read_and_enqueue_data, daemon=True).start()
    tasks = (
        asyncio.create_task(send_data(), name=send_data.__name__),
        asyncio.create_task(recv_data(), name=recv_data.__name__)
    )
    done, pending = await asyncio.wait(
        tasks,
        return_when=asyncio.FIRST_COMPLETED
    )
    await process_wait_results(done, pending)
    has_termination_been_required.set()


async def process_wait_results(
    done: set[asyncio.Task], pending: set[asyncio.Task]
) -> None:
    for task in done:
        try:
            task.result()
        except Exception:
            logger.error(
                Messages.EXCEPTION_OCCURED.value, exc_info=True
            )
        except asyncio.CancelledError:
            pass

    for task in pending:
        task.cancel()

    await asyncio.gather(*pending, return_exceptions=True)


async def send_data() -> None:
    wr = writer.get()

    while not has_termination_been_required.is_set():
        try:
            data = data_queue.get_nowait()
        except queue.Empty:
            await asyncio.sleep(Settings.DATA_QUEUE_GET_NOWAIT_INTERVAL.value)
            continue

        wr.write(data.strip().encode(Settings.TEXT_ENCODING.value))
        await wr.drain()
        data_queue.task_done()


async def recv_data() -> None:
    rd = reader.get()

    while not has_termination_been_required.is_set():
        data = (
            await rd.read(Settings.BYTES_READ_LIMIT.value)
        ).decode(Settings.TEXT_ENCODING.value)

        if not data:
            logger.info(Messages.SERVER_HAS_SENT_EOF.value)
            break

        await asyncio.to_thread(print, data, flush=True)


def read_and_enqueue_data() -> None:
    while not has_termination_been_required.is_set():
        data = sys.stdin.readline()

        if data in Settings.IGNORABLE_STRINGS.value:
            continue

        data_queue.put(data)


def handle_signal(signal: int, frame: Optional[FrameType]) -> None:
    # Run threadsafe to exclude problems concerning threadsafety.
    asyncio.get_running_loop().call_soon_threadsafe(
        has_termination_been_required.set
    )


if __name__ == "__main__":
    logger = create_logger(Settings.CLIENT_LOGGER_NAME.value)
    atexit.register(lambda: logger.__queue_listener.stop())
    signal.signal(signal.SIGINT, handle_signal)

    reader = contextvars.ContextVar[asyncio.StreamReader]("reader")
    writer = contextvars.ContextVar[asyncio.StreamWriter]("writer")

    data_queue: queue.Queue[str] = queue.Queue(Settings.DATA_QUEUE_SIZE.value)
    has_termination_been_required = asyncio.Event()
    backgroud_tasks: set[asyncio.Task] = set()

    ssl_context = contextvars.ContextVar[ssl.SSLContext]("client_ssl_context")
    ctx = ssl.create_default_context()
    ctx.load_verify_locations("tls_options/server.crt")
    ssl_context.set(ctx)

    asyncio.run(run_app())
