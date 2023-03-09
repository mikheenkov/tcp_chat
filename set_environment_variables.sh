export SERVER_HOST=localhost
export SERVER_PORT=54321
export SERVER_LOGGER_NAME=server_logger
export CLIENT_LOGGER_NAME=client_logger
export TEXT_ENCODING=utf-8
export BYTES_READ_LIMIT=4096
export DATA_QUEUE_SIZE=100
export NORMAL_EXIT_CODE=0
export ABNORMAL_EXIT_CODE=1
export DATA_QUEUE_GET_NOWAIT_INTERVAL=0.01

export CONNECTION_HAS_BEEN_MADE="You have connected successfully; type something so everyone can see!"
export CONNECTION_HAS_NOT_BEEN_MADE="Connection has not been made."
export CLIENT_HAS_CONNECTED="%s has connected."
export CLIENT_HAS_SENT_EOF="Client %s has sent EOF. Closing connection..."
export CLIENT_HAS_BEEN_STOPPED="Goodbye!"
export SERVER_HAS_BEEN_STARTED="Server has been started on (%s, %s).
Starting accepting connections..."
export SERVER_HAS_SENT_EOF="Server has sent EOF. Terminating client..."
export SERVER_HAS_BEEN_STOPPED="Server has been stopped..."
export SOCKET_WRITE_ERROR="Error occured while writing to a socket (%s)."
export SOCKET_READ_ERROR="Error occured while reading from a socket (%s)."
export SOCKET_CLOSE_ERROR="Error occured while closing a socket (%s)."
export SOCKET_ANONYMOUS_CLOSE_ERROR="Error occured while closing a socket with an unknown IP address."
export SOCKET_CLIENT_CLOSE_ERROR="Error occured while closing a socket (clientside)."
export EXCEPTION_OCCURED="Exception occured."
