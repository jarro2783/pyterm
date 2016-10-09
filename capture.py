#!/usr/bin/env python3

import pyterm
import sys

prog = pyterm.ExecProgram("nethack", '-u', 'dufus')
writer = pyterm.FileWriter("output.tty")
net = pyterm.ExecWriter("termrecord_client", "-host", "localhost",
    "-port", "34234", "-user", "dufus", "-send")
capture = pyterm.Capture(prog, writers = [writer, net])


capture.run()

print("Press enter")
sys.stdin.readline()
