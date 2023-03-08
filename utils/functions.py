import sys
import uuid
import queue
import asyncio
import logging
from logging.handlers import QueueHandler, QueueListener


LoggerLevel = int


def create_logger(
    name: str,
    *,
    level: LoggerLevel = logging.DEBUG,
) -> logging.Logger:
    """Creates logger that performes logging in a non-blocking manner.

    Each log record is handled in a separate thread:
    Logger's log method invocation (e.g., .error()) -> QueueHandler ->
    <separate thread> QueueListener -> Handler(s)'(s) .handle() method.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    return update_logger(logger)


def update_logger(logger: logging.Logger) -> logging.Logger:
    file_handler = logging.FileHandler(
        logger.name + "-" + str(uuid.uuid4()) + ".log"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(filename)s - %(levelname)s - %(message)s"
        )
    )

    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setLevel(logging.INFO)

    queue_ = queue.Queue[logging.LogRecord]()
    logger.addHandler(QueueHandler(queue_))
    logger.__queue_listener = (  # There were used two underscores to
        QueueListener(           # Prevent possible attribute name collisions.
            queue_,              # This attribute can be accessed later on;
            file_handler,        # No special meaning was implied.
            stream_handler,
            respect_handler_level=True
        )
    )
    logger.__queue_listener.start()

    return logger


async def cancel_tasks() -> None:
    """Cancels and awaits all tasks except current one.
    """
    all_tasks_except_current_one = tuple(
        task for task in asyncio.all_tasks()
        if task is not asyncio.current_task()
    )

    for task in all_tasks_except_current_one:
        task.cancel()

    await asyncio.gather(*all_tasks_except_current_one, return_exceptions=True)
