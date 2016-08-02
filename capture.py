#!/usr/bin/env python3

import pyterm

prog = pyterm.ExecProgram("bash")
writer = pyterm.FileWriter("output.tty")
capture = pyterm.Capture(prog, writers = [writer])


capture.run()
