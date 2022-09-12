import enum
from collections import namedtuple


class Settings(enum.Enum):
    SERVER_HOST = '127.0.0.1'
    SERVER_PORT = 54321
    SERVER_LOGGER_NAME = 'server_logger'
    CLIENT_LOGGER_NAME = 'client_logger'

    TEXT_ENCODING = 'utf-8'
    BYTES_READ_LIMIT = 4096
    DATA_QUEUE_SIZE = 1

    NORMAL_EXIT_CODE = 0
    ABNORMAL_EXIT_CODE = 1

    DATA_QUEUE_GET_NOWAIT_INTERVAL = 0.01

    IGNORABLE_STRINGS = ('\n', '\r\n', '')


class Messages(enum.Enum):
    CONNECTION_HAS_BEEN_MADE = (
        'You have connected successfully;'
        ' type something so everyone can see!'
    )
    CONNECTION_HAS_NOT_BEEN_MADE = (
        'Connection has not been made.'
    )
    CLIENT_HAS_CONNECTED = '%s has connected.'
    CLIENT_HAS_SENT_EOF = 'Client %s has sent EOF. Closing connection...'
    CLIENT_HAS_BEEN_STOPPED = 'Goodbye!'

    SERVER_HAS_BEEN_STARTED = (
        'Server has been started on (%s, %s).'
        ' Starting accepting connections...'
    )
    SERVER_HAS_SENT_EOF = (
        'Server has sent EOF. Terminating client...'
    )
    SERVER_HAS_BEEN_STOPPED = 'Server has been stopped...'

    SOCKET_ERROR = namedtuple(
        'SocketError',
        ('write', 'read', 'close', 'anonymous_close', 'client_close')
    )(
        'Error occured while writing to a socket (%s).',
        'Error occured while reading from a socket (%s).',
        'Error occured while closing a socket (%s).',
        'Error occured while closing a socket with an unknown IP address.',
        'Error occured while closing a socket (clientside).'
    )
    EXCEPTION_OCCURED = 'Exception occured.'
