import fcntl
import os
import pty
import select
import signal
import struct
import sys
import termios
import time
import tty

from .exec import ExecWriter
from .exec import ExecWatcher

def thetime():
    t = time.time()
    integral = int(t)
    return (integral, int((t - integral) * 1000000))

class ExecProgram:
    def __init__(self, program, *args):
        self.__program = program
        self.__args = args

    def execute(self):
        os.execlp(self.__program, self.__program, *self.__args)

class FileWriter:
    def __init__(self, file):
        self.__file = open(file, "wb")

    def write(self, s):
        t = thetime()
        header = struct.pack("<III", t[0], t[1], len(s))
        self.__file.write(header)
        self.__file.write(s)
        self.__file.flush()

    def close(self):
        self.__file.close()

def atomic_write(out, data):
    written = 0
    while True:
        try:
            written += os.write(out, data[written:])
            break
        except InterruptedError:
            continue

class Capture:
    read_size = 256

    def __init__(self, program, idle_time, writers=[]):
        self.__program = program
        self.__writers = writers
        self.__idle_time = idle_time

        signal.signal(signal.SIGWINCH, self.__window_changed)

    def __write(self, s):
        for w in self.__writers:
            w.write(s)

    def __get_window_size(self, fd):
        buf = struct.pack('HHHH', 0, 0, 0, 0)
        size = fcntl.ioctl(fd, termios.TIOCGWINSZ, buf)
        x, y, _, _ = struct.unpack('HHHH', size)

        self.__width = x
        self.__height = y

    def __set_window_size(self, fd):
        size = struct.pack('HHHH', self.__width, self.__height, 0, 0)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, size)

    def __window_changed(self, num, frame):
        self.__get_window_size(sys.stdin.fileno())
        self.__set_window_size(self.__master)

    def run(self):
        master, slave = pty.openpty()

        self.__get_window_size(sys.stdin.fileno())
        self.__set_window_size(slave)

        pid = os.fork()

        idle_intervals = 0

        if pid == 0:
            os.setsid()
            os.close(master)
            os.dup2(slave, 0)
            os.dup2(slave, 1)
            os.dup2(slave, 2)
            os.close(slave)

            fcntl.ioctl(0, termios.TIOCSCTTY, 0)

            self.__program.execute()
            os.exit(1)
        else:
            os.close(slave)

            self.__master = master

            term = termios.tcgetattr(0)
            tty.setraw(0)
            try:
                while True:

                    try:
                        ready, _, _ = select.select([0, master], [], [], 60)

                        if len(ready) == 0:
                            idle_intervals += 1

                            if idle_intervals >= self.__idle_time:
                                break

                        for f in ready:
                            if f == 0:
                                text = os.read(0, self.read_size)
                                idle_intervals = 0
                                atomic_write(master, text)
                            elif f == master:
                                text = os.read(master, self.read_size)
                                atomic_write(1, text)
                                self.__write(text)
                    except InterruptedError:
                        continue
                    except OSError:
                        break
                os.close(master)
                os.waitpid(pid, 0)
            finally:
                termios.tcsetattr(0, termios.TCSAFLUSH, term)
                for writer in self.__writers:
                    writer.close()
