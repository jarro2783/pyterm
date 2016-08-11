import os
import pty
import select
import struct
import termios
import time
import tty

from .exec import ExecWriter

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

class Capture:
    read_size = 256

    def __init__(self, program, writers = []):
        self.__program = program
        self.__writers = writers

    def __write(self, s):
        for w in self.__writers:
            w.write(s)
    
    def run(self):
        master, slave = pty.openpty()

        pid = os.fork()

        if pid == 0:
            os.setsid()
            os.close(master)
            os.dup2(slave, 0)
            os.dup2(slave, 1)
            os.dup2(slave, 2)
            os.close(slave)
            self.__program.execute()
            os.exit(1)
        else:
            os.close(slave)

            term = termios.tcgetattr(0)
            tty.setraw(0)
            try:
                while True:

                    try:
                        ready, _, _ = select.select([0, master], [], [])

                        for f in ready:
                            if f == 0:
                                s = os.read(0, 1)
                                os.write(master, s)
                            elif f == master:
                                s = os.read(master, self.read_size)
                                os.write(1, s)
                                self.__write(s)
                    except OSError:
                        break
                os.waitpid(pid, 0)
            finally:
                termios.tcsetattr(0, termios.TCSAFLUSH, term)
