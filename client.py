import sys
import time
import queue
import atexit
import signal
import asyncio
import threading
import contextvars
from types import FrameType
from typing import Optional

from .utils.constants import Settings, Messages
from .utils.functions import create_logger, cancel_tasks


async def _run_app() -> None:
    try:
        rd, wr = await asyncio.open_connection(
            Settings.SERVER_HOST.value,
            Settings.SERVER_PORT.value
        )
    except OSError:
        _logger.error(
            Messages.CONNECTION_HAS_NOT_BEEN_MADE.value,
            exc_info=True
        )
    else:
        _reader.set(rd)
        _writer.set(wr)

        process_data_task = asyncio.create_task(
            _process_data(),
            name=_process_data.__name__
        )
        _backgroud_tasks.add(process_data_task)
        process_data_task.add_done_callback(_backgroud_tasks.discard)

        await asyncio.sleep(0)
        _logger.info(Messages.CONNECTION_HAS_BEEN_MADE.value)

        await _has_termination_been_required.wait()
        _logger.info(Messages.CLIENT_HAS_BEEN_STOPPED.value)
        await _stop_app()


async def _stop_app() -> None:
    await cancel_tasks()
    wr = _writer.get()

    try:
        wr.close()
        await wr.wait_closed()
    except OSError:
        _logger.error(Messages.SOCKET_ERROR.value.client_close)


async def _process_data() -> None:
    threading.Thread(target=_read_and_enqueue_data, daemon=True).start()
    tasks = (
        asyncio.create_task(_send_data(), name=_send_data.__name__),
        asyncio.create_task(_recv_data(), name=_recv_data.__name__)
    )
    done, pending = await asyncio.wait(
        tasks,
        return_when=asyncio.FIRST_COMPLETED
    )
    await _process_wait_results(done, pending)
    _has_termination_been_required.set()


async def _process_wait_results(
    done: set[asyncio.Task], pending: set[asyncio.Task]
) -> None:
    for task in done:
        try:
            task.result()
        except Exception:
            _logger.error(
                Messages.EXCEPTION_OCCURED.value, exc_info=True
            )
        except asyncio.CancelledError:
            pass

    for task in pending:
        task.cancel()

    await asyncio.gather(*pending, return_exceptions=True)


async def _send_data() -> None:
    wr = _writer.get()

    while not _has_termination_been_required.is_set():
        try:
            data = _data_queue.get_nowait()
        except queue.Empty:
            await asyncio.sleep(Settings.DATA_QUEUE_GET_NOWAIT_INTERVAL.value)
            continue

        wr.write(data.strip().encode(Settings.TEXT_ENCODING.value))
        await wr.drain()
        _data_queue.task_done()


async def _recv_data() -> None:
    rd = _reader.get()

    while not _has_termination_been_required.is_set():
        data = (
            await rd.read(Settings.BYTES_READ_LIMIT.value)
        ).decode(Settings.TEXT_ENCODING.value)

        if not data:
            _logger.info(Messages.SERVER_HAS_SENT_EOF.value)
            break

        await asyncio.to_thread(print, data, flush=True)


def _read_and_enqueue_data() -> None:
    while not _has_termination_been_required.is_set():
        data = sys.stdin.readline()

        if data in Settings.IGNORABLE_STRINGS.value:
            continue

        _data_queue.put(data)


def _handle_signal(signal: int, frame: Optional[FrameType]) -> None:
    _has_termination_been_required.set()


if __name__ == '__main__':
    _logger = create_logger(
        Settings.CLIENT_LOGGER_NAME.value,
        suffix=str(round(time.time()))
    )
    atexit.register(lambda: _logger.__queue_listener.stop())
    signal.signal(signal.SIGINT, _handle_signal)

    _reader = contextvars.ContextVar[asyncio.StreamReader]('reader')
    _writer = contextvars.ContextVar[asyncio.StreamWriter]('writer')

    _data_queue: queue.Queue[str] = queue.Queue(Settings.DATA_QUEUE_SIZE.value)
    _has_termination_been_required = asyncio.Event()
    _backgroud_tasks: set[asyncio.Task] = set()

    asyncio.run(_run_app())
