#!/usr/bin/env python3

import pyterm

prog = pyterm.ExecProgram("nethack", '-u', 'dufus')
writer = pyterm.FileWriter("output.tty")
capture = pyterm.Capture(prog, writers = [writer])


capture.run()
