import time
import atexit
import signal
import asyncio
import contextvars
from types import FrameType
from typing import Iterable, Optional

from .utils.constants import Settings, Messages
from .utils.functions import create_logger, cancel_tasks


async def _run_app() -> None:
    server = (
        await asyncio.start_server(
            _preprocess_client,
            Settings.SERVER_HOST.value,
            Settings.SERVER_PORT.value
        )
    )

    tasks = (
        asyncio.create_task(
            server.serve_forever(),
            name=server.serve_forever.__name__
        ),
        asyncio.create_task(_has_termination_been_required.wait())
    )
    await asyncio.sleep(0)
    _logger.info(
        Messages.SERVER_HAS_BEEN_STARTED.value,
        Settings.SERVER_HOST.value,
        Settings.SERVER_PORT.value
    )

    async with server:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    _logger.info(Messages.SERVER_HAS_BEEN_STOPPED.value)
    await _stop_app()


async def _stop_app() -> None:
    await cancel_tasks()
    await asyncio.gather(
        *(
            _close_writer(wr, wr.get_extra_info('peername')[0])
            for wr in _connected_clients
        )
    )
    _connected_clients.clear()


async def _preprocess_client(
    rd: asyncio.StreamReader,
    wr: asyncio.StreamWriter
) -> None:
    _reader.set(rd)
    _writer.set(wr)
    address = wr.get_extra_info('peername')

    if not address:
        await _close_writer(wr)
        return None

    ip_addr = address[0]
    _ip_address.set(ip_addr)

    _connected_clients.append(wr)
    _logger.info(Messages.CLIENT_HAS_CONNECTED.value, ip_addr)

    process_client_task = asyncio.create_task(
        _process_client(),
        name=_process_client.__name__
    )
    _backgroud_tasks.add(process_client_task)
    process_client_task.add_done_callback(_backgroud_tasks.discard)
    return None


async def _process_client() -> None:
    rd = _reader.get()
    wr = _writer.get()
    ip_addr = _ip_address.get()

    while not _has_termination_been_required.is_set():
        try:
            data = (
                await rd.read(Settings.BYTES_READ_LIMIT.value)
            ).decode(Settings.TEXT_ENCODING.value)
        except OSError:
            _logger.error(Messages.SOCKET_ERROR.value.read, ip_addr)
            break

        if not data:
            _logger.info(Messages.CLIENT_HAS_SENT_EOF.value, ip_addr)
            break

        broadcast_task = asyncio.create_task(
            _broadcast_data(data),
            name=_broadcast_data.__name__
        )
        _backgroud_tasks.add(broadcast_task)
        broadcast_task.add_done_callback(_backgroud_tasks.discard)

    await _close_writer(wr, ip_addr)
    await asyncio.to_thread(_connected_clients.remove, wr)


async def _broadcast_data(data: str) -> None:
    sender = _writer.get()
    sender_ip_addr = _ip_address.get()

    # Use .copy() since _connected_clients can be modified while iteration.
    # Consider OSError case, for example.
    for wr in _connected_clients.copy():
        if (wr is sender) or wr.is_closing():
            continue

        try:
            wr.write(
                f'{sender_ip_addr}: {data}'.encode(
                    Settings.TEXT_ENCODING.value
                )
            )
            await wr.drain()
        except OSError:
            ip_addr = wr.get_extra_info('peername')[0]
            _logger.error(Messages.SOCKET_ERROR.value.write, ip_addr)
            await _close_writer(wr, ip_addr)
            await asyncio.to_thread(_connected_clients.remove, wr)


async def _close_writer(
    wr: asyncio.StreamWriter,
    ip_addr: Optional[str] = None
) -> None:
    try:
        wr.close()
        await wr.wait_closed()
    except OSError:
        if ip_addr:
            _logger.error(Messages.SOCKET_ERROR.value.close, ip_addr)
        else:
            _logger.error(Messages.SOCKET_ERROR.value.anonymous_close)


def _handle_signal(signal: int, frame: Optional[FrameType]) -> None:
    _has_termination_been_required.set()


if __name__ == '__main__':
    _logger = create_logger(
        Settings.SERVER_LOGGER_NAME.value,
        suffix=str(round(time.time()))
    )
    atexit.register(lambda: _logger.__queue_listener.stop())
    signal.signal(signal.SIGINT, _handle_signal)

    _reader = contextvars.ContextVar[asyncio.StreamReader]('reader')
    _writer = contextvars.ContextVar[asyncio.StreamWriter]('writer')
    _ip_address = contextvars.ContextVar[str]('ip_address')

    _connected_clients: list[asyncio.StreamWriter] = []
    _has_termination_been_required = asyncio.Event()
    _backgroud_tasks: set[asyncio.Task] = set()

    asyncio.run(_run_app())
