#!/usr/bin/env python

import sys
from optparse import OptionParser

parser = OptionParser(
        usage="%s [-c|-f|-F] [ARGS]  deviceName"% sys.argv[0],
        )
_help='Buffer type ("capture", "output", "capture-mplane" or "output-mplane").'
parser.add_option('-B', '--buffer-type', dest="buf_type",
        type='string',  help=_help, metavar="b")
parser.add_option('-c', '--capture', dest="capture",
        type='int', help="Capture frames.", metavar="n")
parser.add_option('-C', '--check-overrun', action="store_true", dest="fill_pad",
        help="Verify dequeued frames for buffer overrun.")
parser.add_option('-d', '--delay', action="store", dest="delay", metavar="ms",
        type='int', help="Delay (in ms) before requeuing buffers.")
parser.add_option('-f', '--format', dest="info", metavar="fmt",
        type='string', help="Set the video format.")
_help = '''Read/write frames from/to disk For video capture devices, the first '#' character in the file name is expanded to the frame sequence number. The default file name is 'frame-#.bin'.'''
parser.add_option('-F', '--file', dest="file", metavar="file",
        type='string',help=_help)
parser.add_option('-i', '--input', action="store", dest="input",metavar="input",
        type='int', help="Select the video input.")
parser.add_option('-I', '--fill-frames', action="store_true", dest="fill_frames",
        help="Fill frames with check pattern before queuing them.")
parser.add_option('-l', '--list-controls', action="store_true", dest="list_controls",
        help="List available controls.")
parser.add_option('-n', '--nbufs', dest="nbufs", metavar="nbufs",
        type='int', help="Set the number of video buffers.")
parser.add_option('-p', '--pause', action="store_true", dest="pause",
        help="Pause before starting the video stream.")
parser.add_option('-q', '--quality', dest="quality", metavar="quality",
        type='int', help="MJPEG quality (0-100).")
parser.add_option('-r', '--get-control', dest="ctrl", metavar="ctrl",
        type='string', help="Get control 'ctrl'.")
parser.add_option('-R', '--realtime', dest="rt", metavar="rt",
        type='int', help="Enable realtime RR scheduling.")
parser.add_option('-s', '--size', dest="size", metavar="size",
        type='string', help="Set the frame size.")
parser.add_option('-t', '--time-per-frame', dest="time_per_frame", metavar="time-per-frame",
        type='string', help="num/denom, Set the time per frame (eg. 1/25 = 25 fps).")
parser.add_option('-u', '--userptr', action='store_true', dest="memtype",
        help="Use the user pointers streaming method.")
parser.add_option('-w', '--set-control', dest="control", metavar="ctrl value",
        type='int', nargs=2, help="Set control 'ctrl' to 'value'.")
parser.add_option('-m', '--menu', action='store_true', dest="menu",
        default=False, help="Print control menu.")
parser.add_option('--enum-controls', action='store_true', dest="enum_controls",
        default=False, help="Print control menu.")
parser.add_option('--buffer-size',  dest="buffer_size", metavar="buffer-size",
        type='int', help="Buffer size in bytes.")
parser.add_option('--enum-formats', action="store_true", dest="enum_formats",
        help="Enumerate formats.")
parser.add_option('--enum-inputs', action="store_true", dest="enum_inputs",
        help="Enumerate inputs.")
parser.add_option('--fd', dest="fd", metavar="fd", type='int',
        help="Use a numeric file descriptor insted of a device.")
fields = (
        "any",
        "none",
        "top",
        "bottom",
        "interlaced",
        "seq-tb",
        "seq-bt",
        "alternate",
        "interlaced-tb",
        "interlaced-bt",
)
parser.add_option('--field', choices=fields, dest="field", metavar="field",
        help="Interlaced format field order.")
parser.add_option('--log-status', action="store_true", dest="log_status",
        help="Log device status.")
parser.add_option('--no-query',action="store_true", dest="no_query",
        help="Don't query capabilities on open.")
parser.add_option('--offset', dest="userptr_offset", metavar="offset",
        type='int', help="User pointer buffer offset from page start.")
parser.add_option('--premultiplied', action="store_true", dest="fmt_flags",
        help="Color components are premultiplied by alpha valuen.")
parser.add_option('--queue-late', action="store_true", dest="queue_late",
        help="Queue buffers after streamon, not before.")
parser.add_option('--requeue-last', action="store_true", dest="requeue_last",
        help="Requeue the last buffers before streamoff.")
parser.add_option('--timestamp-source', choices=("soe","eof"), dest="src", metavar="src",
        help="Set timestamp source on output buffers [eof, soe].")
parser.add_option('--skip', dest="skip", metavar="skip-num",
        type=(int), help="Skip the first n frames.")
parser.add_option('--sleep-forever', action="store_true", dest="sleep_forever",
        help="Sleep forever after configuring the device.")
parser.add_option('--stride', action="store_true", dest="stride",
        help="Line stride in bytes.")
