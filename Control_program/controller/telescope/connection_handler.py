from threading import Lock
from socket import SHUT_WR, SHUT_RD, SHUT_RDWR


class TelescopeConnection:
    def __init__(self, host, port, sock):
        # thread_safety
        self.__io_lock = Lock()

        self._socket = sock
        self._socket.connect((host, port))

    def terminate(self):
        with self.__io_lock:
            self._socket.shutdown(SHUT_WR)
            self._socket.close()

    def send_and_receive(self, command, read_bytes=0x400):
        """
        Sends command to the device.
        Returns the response if read_bytes > 0. Default is decimal 1024
        This method is thread-safe.
        """
        with self.__io_lock:
            self.__write_message(command)
            if read_bytes > 0:
                return self.__read_message(read_bytes)

    def __write_message(self, message):
        """
        Writes message to the socket output stream.
        """
        self._socket.sendall('%s\r' % (message))

    def __read_message(self, max_bytes):
        """
        Reads up to max_bytes bytes from the socket input stream.
        """
        return self._socket.recv(max_bytes)
