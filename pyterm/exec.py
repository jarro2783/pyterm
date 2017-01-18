import os
import sys
import tty

class ExecWriter:
    """Writes to the standard input of a program."""
    def __init__(self, program, *args):
        """Initialise with the program to watch with arguments."""

        for argument in args:
            if not isinstance(argument, str):
                raise TypeError("Arguments to exec should be a string")

        reader, writer = os.pipe2(0)
        pid = os.fork()

        if pid == 0:
            os.close(writer)
            os.close(1)
            os.close(2)
            os.dup2(reader, 0)

            os.execlp(program, program, *args)

            sys.exit(1)
        else:
            os.close(reader)
            self.__pipe = writer
            self.__pid = pid

    def write(self, s):
        """Write data to the program."""
        written = 0
        while written != len(s):
            written += os.write(self.__pipe, s[written:])

    def close(self):
        os.close(self.__pipe)
        os.waitpid(self.__pid, 0)

class ExecWatcher:
    """Watches the standard output of a program."""
    def __init__(self, program, args):
        """Creates an ExecWatcher which will run program with args."""
        self.__program = program
        self.__args = args

    def watch(self):
        """Watches the specified program and prints to standard out."""
        reader, writer = os.pipe2(0)

        pid = os.fork()

        # In the child
        if pid == 0:
            tty.setraw(0)
            os.close(reader)
            os.close(2)

            os.dup2(writer, 1)

            os.execlp(self.__program, self.__program, *self.__args)

            sys.exit(1)
        else:
            os.close(writer)

            while True:
                result = os.read(reader, 1024)
                if len(result) == 0:
                    break
                sys.stdout.write(result.decode('utf-8'))

            os.waitpid(pid, 0)
