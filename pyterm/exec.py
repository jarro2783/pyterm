import os

class ExecWriter:
    def __init__(self, program, *args):
        reader, writer = os.pipe2(0)
        pid = os.fork()

        if pid == 0:
            os.close(writer)
            os.close(1)
            os.close(2)
            os.dup2(reader, 0)

            os.execlp(program, program, *args)

            os.exit(1)
        else:
            os.close(reader)
            self.__pipe = writer

    def write(self, s):
        os.write(self.__pipe, s)
