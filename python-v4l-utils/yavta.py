#!/usr/bin/env python

import v4l2
import ctypes
import sys

enum = ctypes.c_uint
buffer_fill_mode = enum
(
        BUFFER_FILL_NONE,
        BUFFER_FILL_FRAME,
        BUFFER_FILL_PADDING,
) = range(3)

class sched_param(ctypes.Structure):
	_field_ = [
			('sched_priority', ctypes.c_int),
	]

def get_options():
	pass
def main():
	pass

if __name__ == "__main__":
	main()
