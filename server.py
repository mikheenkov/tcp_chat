import ssl
import atexit
import signal
import asyncio
import contextvars
from types import FrameType
from typing import Optional

from utils.constants import Settings, Messages
from utils.functions import create_logger, cancel_tasks


async def run_app() -> None:
    server = (
        await asyncio.start_server(
            preprocess_client,
            Settings.SERVER_HOST.value,
            Settings.SERVER_PORT.value,
            ssl=ssl_context.get()
        )
    )

    tasks = (
        asyncio.create_task(
            server.serve_forever(),
            name=server.serve_forever.__name__
        ),
        asyncio.create_task(has_termination_been_required.wait())
    )
    await asyncio.sleep(0)
    logger.info(
        Messages.SERVER_HAS_BEEN_STARTED.value,
        Settings.SERVER_HOST.value,
        Settings.SERVER_PORT.value
    )

    async with server:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    logger.info(Messages.SERVER_HAS_BEEN_STOPPED.value)
    await stop_app()


async def stop_app() -> None:
    await cancel_tasks()
    await asyncio.gather(
        *(
            close_writer(wr, wr.get_extra_info("peername")[0])
            for wr in connected_clients
        )
    )
    connected_clients.clear()


async def preprocess_client(
    rd: asyncio.StreamReader,
    wr: asyncio.StreamWriter
) -> None:
    reader.set(rd)
    writer.set(wr)
    address = wr.get_extra_info("peername")

    if not address:
        await close_writer(wr)
        return None

    ip_addr = address[0]
    ip_address.set(ip_addr)

    connected_clients.append(wr)
    logger.info(Messages.CLIENT_HAS_CONNECTED.value, ip_addr)

    process_client_task = asyncio.create_task(
        process_client(),
        name=process_client.__name__
    )
    backgroud_tasks.add(process_client_task)
    process_client_task.add_done_callback(backgroud_tasks.discard)
    return None


async def process_client() -> None:
    rd = reader.get()
    wr = writer.get()
    ip_addr = ip_address.get()

    while not has_termination_been_required.is_set():
        try:
            data = (
                await rd.read(Settings.BYTES_READ_LIMIT.value)
            ).decode(Settings.TEXT_ENCODING.value)
        except OSError:
            logger.error(Messages.SOCKET_ERROR.value.read, ip_addr)
            break

        if not data:
            logger.info(Messages.CLIENT_HAS_SENT_EOF.value, ip_addr)
            break

        broadcast_task = asyncio.create_task(
            broadcast_data(data),
            name=broadcast_data.__name__
        )
        backgroud_tasks.add(broadcast_task)
        broadcast_task.add_done_callback(backgroud_tasks.discard)

    await close_writer(wr, ip_addr)
    await asyncio.to_thread(connected_clients.remove, wr)


async def broadcast_data(data: str) -> None:
    sender = writer.get()
    sender_ip_addr = ip_address.get()

    # Use .copy() since connected_clients can be modified while iteration.
    # Consider OSError case, for example.
    for wr in connected_clients.copy():
        if (wr is sender) or wr.is_closing():
            continue

        try:
            wr.write(
                f"{sender_ip_addr}: {data}".encode(
                    Settings.TEXT_ENCODING.value
                )
            )
            await wr.drain()
        except OSError:
            ip_addr = wr.get_extra_info("peername")[0]
            logger.error(Messages.SOCKET_ERROR.value.write, ip_addr)
            await close_writer(wr, ip_addr)
            await asyncio.to_thread(connected_clients.remove, wr)


async def close_writer(
    wr: asyncio.StreamWriter,
    ip_addr: Optional[str] = None
) -> None:
    try:
        wr.close()
        await wr.wait_closed()
    except OSError:
        if ip_addr:
            logger.error(Messages.SOCKET_ERROR.value.close, ip_addr)
        else:
            logger.error(Messages.SOCKET_ERROR.value.anonymous_close)


def handle_signal(signal: int, frame: Optional[FrameType]) -> None:
    # Run threadsafe to exclude problems concerning threadsafety.
    asyncio.get_running_loop().call_soon_threadsafe(
        has_termination_been_required.set
    )


if __name__ == "__main__":
    logger = create_logger(Settings.SERVER_LOGGER_NAME.value)
    atexit.register(lambda: logger.__queue_listener.stop())
    signal.signal(signal.SIGINT, handle_signal)

    reader = contextvars.ContextVar[asyncio.StreamReader]("reader")
    writer = contextvars.ContextVar[asyncio.StreamWriter]("writer")
    ip_address = contextvars.ContextVar[str]("ip_address")

    connected_clients: list[asyncio.StreamWriter] = []
    has_termination_been_required = asyncio.Event()
    backgroud_tasks: set[asyncio.Task] = set()

    ssl_context = contextvars.ContextVar[ssl.SSLContext]("server_ssl_context")
    ctx = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    ctx.load_cert_chain("tls_options/server.crt", "tls_options/server.key")
    ssl_context.set(ctx)

    asyncio.run(run_app())
