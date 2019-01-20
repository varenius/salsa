from sys import stdout
from socket import socket, SHUT_WR, SHUT_RD, SHUT_RDWR
from threading import Lock


class RIOConnection:
    def __init__(self, host, port):
        self._io_lock = Lock()

        self._socket = socket()
        self._socket.connect((host, port))

    def terminate(self):
        with self._io_lock:
            self._socket.shutdown(SHUT_RDWR)
            self._socket.close()

    def send_and_receive(self, command, read_bytes=0x400):
        with self._io_lock:
            self._socket.sendall('%s\r' % (command))
            if read_bytes > 0:
                return self._socket.recv(read_bytes)


if __name__ == "__main__":
    rc = RIOConnection("localhost", 55555)
    try:
        stdout.write(rc.send_and_receive(""))
        stdout.flush()
        while 1:
            cmd = raw_input()
            if cmd.lower() == "exit":
                break
            stdout.write(rc.send_and_receive(cmd))
            stdout.flush()
    finally:
        rc.terminate()
