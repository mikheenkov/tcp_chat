import os
import enum
from collections import namedtuple


class Settings(enum.Enum):
    SERVER_HOST = os.environ["SERVER_HOST"]
    SERVER_PORT = int(os.environ["SERVER_PORT"])
    SERVER_LOGGER_NAME = os.environ["SERVER_LOGGER_NAME"]
    CLIENT_LOGGER_NAME = os.environ["CLIENT_LOGGER_NAME"]

    TEXT_ENCODING = os.environ["TEXT_ENCODING"]
    BYTES_READ_LIMIT = int(os.environ["BYTES_READ_LIMIT"])
    DATA_QUEUE_SIZE = int(os.environ["DATA_QUEUE_SIZE"])

    NORMAL_EXIT_CODE = int(os.environ["NORMAL_EXIT_CODE"])
    ABNORMAL_EXIT_CODE = int(os.environ["ABNORMAL_EXIT_CODE"])

    DATA_QUEUE_GET_NOWAIT_INTERVAL = float(os.environ[
        "DATA_QUEUE_GET_NOWAIT_INTERVAL"
    ])


class Messages(enum.Enum):
    CONNECTION_HAS_BEEN_MADE = os.environ["CONNECTION_HAS_BEEN_MADE"]
    CONNECTION_HAS_NOT_BEEN_MADE = os.environ["CONNECTION_HAS_NOT_BEEN_MADE"]

    CLIENT_HAS_CONNECTED = os.environ["CLIENT_HAS_CONNECTED"]
    CLIENT_HAS_SENT_EOF = os.environ["CLIENT_HAS_SENT_EOF"]
    CLIENT_HAS_BEEN_STOPPED = os.environ["CLIENT_HAS_BEEN_STOPPED"]

    SERVER_HAS_BEEN_STARTED = os.environ["SERVER_HAS_BEEN_STARTED"]
    SERVER_HAS_SENT_EOF = os.environ["SERVER_HAS_SENT_EOF"]
    SERVER_HAS_BEEN_STOPPED = os.environ["SERVER_HAS_BEEN_STOPPED"]

    SOCKET_ERROR = namedtuple(
        'SocketError',
        ('write', 'read', 'close', 'anonymous_close', 'client_close')
    )(
        os.environ["SOCKET_WRITE_ERROR"],
        os.environ["SOCKET_READ_ERROR"],
        os.environ["SOCKET_CLOSE_ERROR"],
        os.environ["SOCKET_ANONYMOUS_CLOSE_ERROR"],
        os.environ["SOCKET_CLIENT_CLOSE_ERROR"]
    )
    EXCEPTION_OCCURED = os.environ["EXCEPTION_OCCURED"]
