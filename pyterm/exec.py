import os
import sys

class ExecWriter:
    """Writes to the standard input of a program."""
    def __init__(self, program, *args):
        """Initialise with the program to watch with arguments."""
        reader, writer = os.pipe2(0)
        pid = os.fork()

        if pid == 0:
            os.close(writer)
            #os.close(1)
            #os.close(2)
            os.dup2(reader, 0)

            os.execlp(program, program, *args)

            sys.exit(1)
        else:
            os.close(reader)
            self.__pipe = writer

    def write(self, s):
        """Write data to the program."""
        os.write(self.__pipe, s)

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
            os.close(reader)
            os.close(0)
            os.close(2)
            os.dup2(writer, 1)

            os.execlp(self.__program, self.__program, *self.__args)

            sys.exit(1)
        else:
            os.close(writer)
            while True:
                result = reader.read()
                sys.stdout.write(result)
