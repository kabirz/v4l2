#!/usr/bin/env python

from v4l2 import *
from utils import *
from fcntl import ioctl
import yavta_help
import re
import ctypes, os, sys, errno, time

(options, args) = yavta_help.parser.parse_args()

Print = sys.stdout.write
class Video:
    def __init__(self, device_name='/dev/video0'):
        if len(args) > 0:
            device_name = args[0]
        self.fd = None
        try:
            self.fd = open(device_name, 'r')
            print("Device %s opened." % device_name)
        except IOError as s:
            print("Error opening device '%s': %s (%d)." % (device_name, s.strerror, s.errno))
            sys.exit()
        self.type = None
        self.memtype = V4L2_MEMORY_MMAP
        self.buffer_ = None
        self.width = 0
        self.height = 0
        self.num_planes = 0
        self.fill_mode = BUFFER_FILL_NONE
        self.mp = ctypes.CDLL('libc.so.6')
        self.mp.mmap.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int)
        self.mp.mmap.restype = ctypes.c_void_p
        self.mp.munmap.argtypes = (ctypes.c_void_p, ctypes.c_int)
        self.plane_fmt = {}
        self.ctl_id = 0
        self.cap = v4l2_capability()
        ioctl(self.fd, VIDIOC_QUERYCAP, self.cap)
        self.buf_types = {
                V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE:(1, "Video capture mplanes", "capture-mplane"),
                V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE:(1, "Video output", "output-mplane"),
                V4L2_BUF_TYPE_VIDEO_CAPTURE:(1, "Video capture", "capture"),
                V4L2_BUF_TYPE_VIDEO_OUTPUT:(1, "Video output mplanes", "output"),
                V4L2_BUF_TYPE_VIDEO_OVERLAY:(0, "Video overlay", "overlay"),
                V4L2_BUF_TYPE_META_CAPTURE:(1, "Meta-data capture", "meta-capture")
                }

    def __del__(self):
        try:
            self.video_get_format()
            self.fd.close()
        except Exception:
            pass

    def video_is_mplane(self):
        return (self.type == V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE or
                self.type == V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE)

    def video_is_meta(self):
        return self.type == V4L2_BUF_TYPE_META_CAPTURE

    def video_is_capture(self):
        return (self.type == V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE or
                self.type == V4L2_BUF_TYPE_VIDEO_CAPTURE or
                self.type == V4L2_BUF_TYPE_META_CAPTURE)

    def video_is_output(self):
        return (self.type == V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE or
                self.type == V4L2_BUF_TYPE_VIDEO_OUTPUT)

    def v4l2_buf_type_from_string(self, string):
        for item in self.buf_types.items():
            if item[1][0] and item[1][2] == string:
                return item[0]
        return -1

    def v4l2_buf_typename(self, buf_type):
        return (self.buf_types[buf_type][1] if self.buf_types.has_key(buf_type) else
                'Private' if buf_type == V4L2_BUF_TYPE_PRIVATE else
                'Unknown')

    def video_querycap(self):
        caps = (self.cap.device_caps if self.cap.capabilities & V4L2_CAP_DEVICE_CAPS
                else self.cap.capabilities)
        has_video = (" video," if (caps & (V4L2_CAP_VIDEO_CAPTURE_MPLANE | V4L2_CAP_VIDEO_CAPTURE |
                                           V4L2_CAP_VIDEO_OUTPUT_MPLANE | V4L2_CAP_VIDEO_OUTPUT)) else "")
        has_meta = (" meta-data," if caps & V4L2_CAP_META_CAPTURE else "")
        has_capture = (" capture," if caps & (V4L2_CAP_VIDEO_CAPTURE_MPLANE | V4L2_CAP_VIDEO_CAPTURE | V4L2_CAP_META_CAPTURE) else "")
        has_output = (" output," if caps & (V4L2_CAP_VIDEO_OUTPUT_MPLANE | V4L2_CAP_VIDEO_OUTPUT) else "")
        has_mplane = (" with" if caps & (V4L2_CAP_VIDEO_CAPTURE_MPLANE | V4L2_CAP_VIDEO_OUTPUT_MPLANE) else " without")
        mplane =  has_video + has_meta + has_capture + has_output + has_mplane
        card = self.cap.card
        bus_info = self.cap.bus_info
        driver = self.cap.driver
        if isinstance(self.cap.card, bytes):
            card = self.cap.card.decode()
            bus_info = self.cap.bus_info.decode()
            driver = self.cap.driver.decode()
        print("Device `%s' on `%s' (driver '%s') supports%s mplanes." % (card, bus_info, driver, mplane))
        return caps

    def cap_get_buf_type(self, caps):
        if caps & V4L2_CAP_VIDEO_CAPTURE_MPLANE:
            return V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE
        elif caps & V4L2_CAP_VIDEO_OUTPUT_MPLANE:
            return V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE
        elif caps & V4L2_CAP_VIDEO_CAPTURE:
            return V4L2_BUF_TYPE_VIDEO_CAPTURE
        elif caps & V4L2_CAP_VIDEO_OUTPUT:
            return V4L2_BUF_TYPE_VIDEO_OUTPUT
        elif caps & V4L2_CAP_META_CAPTURE:
            return V4L2_BUF_TYPE_META_CAPTURE
        else:
            print("Device supports neither capture nor output.")
            return -1

    def query_control(self, id, query):
        query.id = id
        try:
            ioctl(self.fd, VIDIOC_QUERYCTRL, query)
        except IOError as m :
            if m.errno != errno.EINVAL:
                print("unable to query control 0x%8.8x: %s (%d)" % (id, m.strerror, m.errno))
            return False
        else:
            self.ctl_id = query.id
            return True


    def get_control(self, query, ctrl):
        ctrls = v4l2_ext_controls()
        ctrls.count = 1
        ctrls.controls = ctypes.pointer(ctrl)
        ctrl.id = query.id

        if query.type == V4L2_CTRL_TYPE_STRING:
            ctrl.string = ctypes.cast(ctypes.create_string_buffer(query.maximum + 1), ctypes.c_char_p)
            ctrl.size = query.maximum + 1

        try:
            ioctl(self.fd, VIDIOC_G_EXT_CTRLS, ctrls)
            return 0
        except IOError as s:
            if(query.type != V4L2_CTRL_TYPE_INTEGER64 and
                    query.type != V4L2_CTRL_TYPE_STRING):
                old = v4l2_control()
                old.id = query.id
                try:
                    ioctl(self.fd, VIDIOC_G_CTRL, old)
                    ctrl.value = old.value
                    return 0
                except IOError as m:
                    ctrl.value = old.value
            print("unable to get control 0x%8.8x: %s (%d)." % (query.id, s.strerror, s.errno))
            return -1

    def set_control(self, args):
        id, val = args
        ctrls = v4l2_ext_controls()
        ctrl = v4l2_ext_control()
        query = v4l2_queryctrl()
        old_val = val

        if not self.query_control(id, query):
            return

        is_64 = query.type == V4L2_CTRL_TYPE_INTEGER64
        ctrls.ctrl_class = V4L2_CTRL_ID2CLASS(id)
        ctrls.count = 1
        ctrls.controls = ctypes.pointer(ctrl)
        ctrl.id = id
        if is_64:
            ctrl.value64 = val
        else:
            ctrl.value = val
        try:
            ioctl(self.fd, VIDIOC_S_EXT_CTRLS, ctrls)
        except IOError:
            val = ctrl.value64 if is_64 else ctrl.value
            print("unable to set control 0x%8.8x" % id)
        else:
            if not is_64 and query.type != V4L2_CTRL_TYPE_STRING:
                old = v4l2_control()
                old.id = id
                old.value = val
            try:
                ioctl(self.fd, VIDIOC_S_CTRL, old)
            except IOError:
                val = old.value
                print("unable to set control 0x%8.8x" % id)
            print("Control 0x%08x set to %x, is %x" % (id, old_val, val))
    def video_get_format(self):
        fmt = v4l2_format()
        fmt.type = self.type
        try:
            ioctl(self.fd, VIDIOC_G_FMT, fmt)
        except IOError as m:
            print("Unable to get format: %s (%d)." % (m.strerror, m.errno))
            return False
        if self.video_is_mplane():
            self.width = fmt.fmt.pix_mp.width
            self.height = fmt.fmt.pix_mp.height
            self.num_planes = fmt.fmt.pix_mp.num_planes
            print("Video format: %s (%08x) %ux%u field %s, %u planes:" %
                  (v4l2_format_name(fmt.fmt.pix_mp.pixelformat), fmt.fmt.pix_mp.pixelformat,
                   fmt.fmt.pix_mp.width, fmt.fmt.pix_mp.height,
                   v4l2_field_name(fmt.fmt.pix_mp.field),
                   fmt.fmt.pix_mp.num_planes))
            for i in range(fmt.fmt.pix_mp.num_planes):
                self.plane_fmt[i].bytesperline = fmt.fmt.pix_mp.plane_fmt[i].bytesperline
                self.plane_fmt[i].sizeimage = (fmt.fmt.pix_mp.plane_fmt[i].sizeimage
                                               if fmt.fmt.pix_mp.plane_fmt[i].bytesperline
                                               else 0)
                print(" * Stride %u, buffer size %u" %
                      (fmt.fmt.pix_mp.plane_fmt[i].bytesperline,fmt.fmt.pix_mp.plane_fmt[i].sizeimage))
        elif self.video_is_meta():
            self.width = 0
            self.height = 0
            self.num_planes = 1
            print("Meta-data format: %s (%08x) buffer size %u\n" %
                  (v4l2_format_name(fmt.fmt.meta.dataformat), fmt.fmt.meta.dataformat,
                   fmt.fmt.meta.buffersize))
        else:
            self.width = fmt.fmt.pix.width
            self.height = fmt.fmt.pix.height
            self.num_planes = 1

            self.plane_fmt[0] = v4l2_plane_pix_format()
            self.plane_fmt[0].bytesperline = fmt.fmt.pix.bytesperline
            self.plane_fmt[0].sizeimage = fmt.fmt.pix.sizeimage if fmt.fmt.pix.bytesperline else 0

            print("Video format: %s (%08x) %ux%u (stride %u) field %s buffer size %u" %
                  (v4l2_format_name(fmt.fmt.pix.pixelformat), fmt.fmt.pix.pixelformat,
                   fmt.fmt.pix.width, fmt.fmt.pix.height, fmt.fmt.pix.bytesperline,
                   v4l2_field_name(fmt.fmt.pix_mp.field),
                   fmt.fmt.pix.sizeimage))
        return True

    def video_set_format(self, w, h, format, stride, buffer_size, field, flags):
        fmt = v4l2_format()
        fmt.type = self.type

        if self.video_is_mplane():
            info = v4l2_format_by_fourcc(format)
            fmt.fmt.pix_mp.width = w
            fmt.fmt.pix_mp.height = h
            fmt.fmt.pix_mp.pixelformat = format
            fmt.fmt.pix_mp.field = field
            fmt.fmt.pix_mp.num_planes = info.n_planes
            fmt.fmt.pix_mp.flags = flags

            for i in range(fmt.fmt.pix_mp.num_planes):
                fmt.fmt.pix_mp.plane_fmt[i].bytesperline = stride
                fmt.fmt.pix_mp.plane_fmt[i].sizeimage = buffer_size
        elif self.video_is_meta():
            fmt.fmt.meta.dataformat = format
            fmt.fmt.meta.buffersize = buffer_size
        else:
            fmt.fmt.pix.width = w
            fmt.fmt.pix.height = h
            fmt.fmt.pix.pixelformat = format
            fmt.fmt.pix.field = field
            fmt.fmt.pix.bytesperline = stride
            fmt.fmt.pix.sizeimage = buffer_size
            fmt.fmt.pix.priv = V4L2_PIX_FMT_PRIV_MAGIC
            fmt.fmt.pix.flags = flags

        try:
            ioctl(self.fd, VIDIOC_S_FMT, fmt)
        except IOError as m:
            print("Unable to set format: %s (%d)." % (m.strerror, m.errno))
            return -m.errno

        if self.video_is_mplane():
            print("Video format set: %s (%08x) %ux%u field %s, %u planes: " %
                  (v4l2_format_name(fmt.fmt.pix_mp.pixelformat), fmt.fmt.pix_mp.pixelformat,
                   fmt.fmt.pix_mp.width, fmt.fmt.pix_mp.height, v4l2_field_name(fmt.fmt.pix_mp.field),
                   fmt.fmt.pix_mp.num_planes))

            for i in range(fmt.fmt.pix_mp.num_planes):
                print(" * Stride %u, buffer size %u" %
                      (fmt.fmt.pix_mp.plane_fmt[i].bytesperline,
                       fmt.fmt.pix_mp.plane_fmt[i].sizeimage))
        elif self.video_is_meta():
            print("Meta-data format: %s (%08x) buffer size %u" %
                  (v4l2_format_name(fmt.fmt.meta.dataformat), fmt.fmt.meta.dataformat,
                   fmt.fmt.meta.buffersize))
        else:
            print("Video format set: %s (%08x) %ux%u (stride %u) field %s buffer size %u" %
                  (v4l2_format_name(fmt.fmt.pix.pixelformat), fmt.fmt.pix.pixelformat,
                   fmt.fmt.pix.width, fmt.fmt.pix.height, fmt.fmt.pix.bytesperline,
                   v4l2_field_name(fmt.fmt.pix.field), fmt.fmt.pix.sizeimage))
        return 0

    def video_set_framerate(self, time_per_frame):
        parm = v4l2_streamparm()
        parm.type = self.type

        try:
            ioctl(self.fd, VIDIOC_G_PARM, parm)
        except IOError as m:
            print("Unable to get frame rate: %s (%d)." % (s.strerror, s.errno))
            return -m.errno

        print("Current frame rate: %u/%u" %
              (parm.parm.capture.timeperframe.numerator,
               parm.parm.capture.timeperframe.denominator))

        print("Setting frame rate to: %u/%u" % (time_per_frame.numerator, time_per_frame.denominator))

        parm.parm.capture.timeperframe.numerator = time_per_frame.numerator
        parm.parm.capture.timeperframe.denominator = time_per_frame.denominator

        try:
            ioctl(self.fd, VIDIOC_S_PARM, parm)
        except IOError as m:
            print("Unable to set frame rate: %s (%d)." % (m.strerror, m.errno))
            return -m.errno

        try:
            ioctl(self.fd, VIDIOC_G_PARM, parm)
        except IOError as m:
            print("Unable to get frame rate: %s (%d)." % (m.strerror, m.errno))
            return -m.errno

        print("Frame rate set: %u/%u" %
              (parm.parm.capture.timeperframe.numerator,
               parm.parm.capture.timeperframe.denominator))
        return 0

    def video_buffer_mmap(self, buffer, v4l2buf):
        length = 0
        offset = 0
        for i in range(self.num_planes):
            if self.video_is_mplane():
                length = v4l2buf.m.planes[i].length
                offset = v4l2buf.m.planes[i].m.mem_offset
            else:
                length = v4l2buf.length
                offset = v4l2buf.m.offset

            buffer.mem[i] = self.mp.mmap(0, length, PROT_READ | PROT_WRITE,
                                         MAP_SHARED, self.fd.fileno(), offset)

            if buffer.mem[i] == MAP_FAILED:
                print("Unable to map buffer %u/%u." % (buffer.idx, i))
                return -1
            buffer.size[i] = length
            buffer.padding[i] = 0

            print("Buffer %u/%u mapped at address %s." % (buffer.idx, i, buffer.mem[i]))

        return 0

    def video_buffer_munmap(self, buffer):
        for i in range(self.num_planes):
            ret = self.mp.munmap(buffer.mem[i], buffer.size[i])
            if ret < 0:
                print("Unable to unmap buffer %u/%u." % (buffer.idx, i))
            buffer.mem[i] = MAP_FAILED
        return 0

    def video_buffer_alloc_userptr(self, buffer, v4l2buf, offset, padding):
        length = 0
        for i in range(self.num_planes):
            if self.video_is_mplane():
                length = v4l2buf.m.planes[i].length
            else:
                length = v4l2buf.length

            buffer.mem[i] = ctypes.create_string_buffer(length + offset + padding)
            if buffer.mem[i] == 0:
                print("Unable to allocate buffer %u/%u" % (buffer.idx, i))
                return -errno.ENOMEM

            buffer.mem[i] += offset
            buffer.size[i] = length
            buffer.padding[i] = padding

            print("Buffer %u/%u allocated at address %s." % (buffer.idx, i, buffer.mem[i]))
        return 0

    def video_buffer_free_userptr(self, buffer):
        for i in range(self.num_planes):
            pass #free(buffer->mem[i])
            buffer.mem[i] = MAP_FAILED

    def video_buffer_fill_userptr(self, buffer, v4l2buf):
        if not self.video_is_mplane():
            v4l2buf.m.userptr = buffer.mem[0]
            return
        for i in range(self.num_planes):
            v4l2buf.m.planes[i].m.userptr = buffer.mem[i]

    def get_ts_flags(self, flags, ts_type, ts_source):
        fg = flags & V4L2_BUF_FLAG_TIMESTAMP_MASK
        ts_type = ("unk" if fg == V4L2_BUF_FLAG_TIMESTAMP_UNKNOWN else
                    "mono" if fg == V4L2_BUF_FLAG_TIMESTAMP_MONOTONIC else
                    "copy" if fg == V4L2_BUF_FLAG_TIMESTAMP_COPY else
                    "inv")
        fg = flags & V4L2_BUF_FLAG_TSTAMP_SRC_MASK
        ts_source = ("EoF" if fg == V4L2_BUF_FLAG_TSTAMP_SRC_EOF else
                        "SoE" if fg == V4L2_BUF_FLAG_TSTAMP_SRC_SOE else
                        "inv")

    def video_queue_buffer(self, index, fill):
        buf = v4l2_buffer()
        planes = v4l2_plane() * VIDEO_MAX_PLANES

        buf.index = index
        buf.type = self.type
        buf.memory = self.memtype

        if self.video_is_output():
            buf.flags = self.buffer_output_flags
        if self.timestamp_type == V4L2_BUF_FLAG_TIMESTAMP_COPY:
            ts= time.time()
            buf.timestamp.tv_sec = int(ts)
            buf.timestamp.tv_usec = int((ts - int(ts))*10**9)

        if self.video_is_mplane():
            buf.m.planes = planes
            buf.length = self.num_planes

        if self.memtype == V4L2_MEMORY_USERPTR:
            if self.video_is_mplane():
                for i in range(self.num_planes):
                    buf.m.planes[i].m.userptr = self.buffers[index].mem[i]
                    buf.m.planes[i].length = self.buffers[index].size[i]
            else:
                buf.m.userptr = self.buffers[index].mem[0]
                buf.length = self.buffers[index].size[0]

        for i in range(self.num_planes):
            if self.video_is_output():
                if self.video_is_mplane():
                    buf.m.planes[i].bytesused = self.patternsize[i]
                else:
                    buf.bytesused = self.patternsize[i]

            #memcpy(dev->buffers[buf.index].mem[i], dev->pattern[i],dev->patternsize[i]);
            else:
                if fill & BUFFER_FILL_FRAME:
                    pass #memset(dev->buffers[buf.index].mem[i], 0x55,    dev->buffers[index].size[i]);
                if fill & BUFFER_FILL_PADDING:
                    pass #memset(dev->buffers[buf.index].mem[i] + dev->buffers[index].size[i], 0x55, dev->buffers[index].padding[i]);

        try:
            ioctl(self.fd, VIDIOC_QBUF, buf)
        except IOError as m:
            print("Unable to queue buffer: %s (%d)." % (m.strerror, m.errno))
            return -m.errno

    def video_enable(self, enable):
        type = self.type
        try:
            ioctl(self.fd, VIDIOC_STREAMON if enable else VIDIOC_STREAMOFF, type)
        except IOError as m:
            print("Unable to %s streaming: %s (%d)." %("start" if enable else "stop", m.strerror, m.errno))
            return -m.errno
        return 0

    def video_query_menu(self, query, value):
        menu = v4l2_querymenu()
        for i in range(query.minimum, query.maximum + 1):
            menu.index = i
            menu.id = query.id
            try:
                ioctl(self.fd, VIDIOC_QUERYMENU, menu)
            except (OSError, IOError):
                continue
            item = ""
            if query.type == V4L2_CTRL_TYPE_MENU:
                item = menu.name
                if isinstance(menu.name, bytes):
                    item = item.decode()
            else:
                item = str(menu.value)
            print("  %u: %.32s%s" % (menu.index, item, " (*)" if menu.index == value else ""))

    def video_print_control(self, id, full=True):
        ctrl = v4l2_ext_control()
        query = v4l2_queryctrl()
        if not self.query_control(id, query):
            return False
        qname = query.name
        if isinstance(qname, bytes):
            qname = qname.decode()
        if query.flags & V4L2_CTRL_FLAG_DISABLED:
            return True
        if query.type == V4L2_CTRL_TYPE_CTRL_CLASS:
            print("--- %s (class 0x%08x) ---" %(qname, query.id))
            return True
        if self.get_control(query, ctrl) == -1:
            val = 'n/a'
        elif query.type == V4L2_CTRL_TYPE_INTEGER64:
            val =  ctrl.value64
        elif query.type == V4L2_CTRL_TYPE_STRING:
            val = ctrl.string.decode() if isinstance(ctrl.string, bytes) else ctrl.string
        else:
            val = ctrl.value

        if full:
            print("control 0x%08x '%s' min %d max %d step %d default %d current %s."
                    % (query.id, qname, query.minimum, query.maximum,
                        query.step, query.default_value, str(val)))
        else:
            print("control 0x%08x current %s." % (query.id, str(val)))

        if query.type == V4L2_CTRL_TYPE_STRING:
            pass # TODO free ctrl.string

        if not full:
            return True
        if query.type == V4L2_CTRL_TYPE_MENU or query.type == V4L2_CTRL_TYPE_INTEGER_MENU:
            self.video_query_menu(query, ctrl.value)
        return True

    def video_list_controls(self):
        nctrls = 0
        while self.video_print_control(self.ctl_id | V4L2_CTRL_FLAG_NEXT_CTRL):
            nctrls += 1

        if nctrls:
            print("%u control%s found." % (nctrls, "s" if nctrls > 1 else ""))
        else:
            print("No control found.")
    def video_enum_frame_intervals(self, pixelformat, width, height):
        ival = v4l2_frmivalenum()
        i = 0
        while True:
            ival.index = i
            ival.pixel_format = pixelformat
            ival.width = width
            ival.height = height
            try:
                ioctl(self.fd, VIDIOC_ENUM_FRAMEINTERVALS, ival)
            except IOError:
                break

            if i != ival.index:
                print("Warning: driver returned wrong ival index %u." % ival.index)
            if pixelformat != ival.pixel_format:
                print("Warning: driver returned wrong ival pixel format %08x." % ival.pixel_format)
            if width != ival.width:
                print("Warning: driver returned wrong ival width %u." % ival.width)
            if height != ival.height:
                print("Warning: driver returned wrong ival height %u." % ival.height)

            if i:
                Print(", ")

            if ival.type == V4L2_FRMIVAL_TYPE_DISCRETE:
                Print("%u/%u" % (ival.discrete.numerator, ival.discrete.denominator))
            if ival.type == V4L2_FRMIVAL_TYPE_CONTINUOUS:
                Print("%u/%u - %u/%u" %
                      (ival.stepwise.min.numerator,
                       ival.stepwise.min.denominator,
                       ival.stepwise.max.numerator,
                       ival.stepwise.max.denominator))
                return
            if ival.type == V4L2_FRMIVAL_TYPE_STEPWISE:
                Print("%u/%u - %u/%u (by %u/%u)" %
                      (ival.stepwise.min.numerator,
                       ival.stepwise.min.denominator,
                       ival.stepwise.max.numerator,
                       ival.stepwise.max.denominator,
                       ival.stepwise.step.numerator,
                       ival.stepwise.step.denominator))
                return
            i += 1
    def video_enum_frame_sizes(self, pixelformat):
        frame = v4l2_frmsizeenum()
        i = 0
        while True:
            frame.index = i
            frame.pixel_format = pixelformat
            try:
                ioctl(self.fd, VIDIOC_ENUM_FRAMESIZES, frame)
            except IOError:
                break
            if i != frame.index:
                print("Warning: driver returned wrong frame index %u." % frame.index)
            if pixelformat != frame.pixel_format:
                print("Warning: driver returned wrong frame pixel format %08x." % frame.pixel_format)

            if frame.type == V4L2_FRMSIZE_TYPE_DISCRETE:
                Print("\tFrame size: %ux%u (" % (frame.discrete.width, frame.discrete.height))
                self.video_enum_frame_intervals(frame.pixel_format, frame.discrete.width, frame.discrete.height)
                print(")")
            elif frame.type == V4L2_FRMSIZE_TYPE_CONTINUOUS:
                Print("\tFrame size: %ux%u - %ux%u (" %
                      (frame.stepwise.min_width,
                       frame.stepwise.min_height,
                       frame.stepwise.max_width,
                       frame.stepwise.max_height))
                self.video_enum_frame_intervals(frame.pixel_format, frame.stepwise.max_width, frame.stepwise.max_height)
                print(")")
            elif frame.type == V4L2_FRMSIZE_TYPE_STEPWISE:
                Print("\tFrame size: %ux%u - %ux%u (by %ux%u) (" %
                      (frame.stepwise.min_width,
                       frame.stepwise.min_height,
                       frame.stepwise.max_width,
                       frame.stepwise.max_height,
                       frame.stepwise.step_width,
                       frame.stepwise.step_height))
                self.video_enum_frame_intervals(frame.pixel_format, frame.stepwise.max_width, frame.stepwise.max_height)
                print(")")
            i += 1
    def video_enum_formats(self, type):
        fmt = v4l2_fmtdesc()
        i = 0
        while True:
            fmt.index = i
            fmt.type = type
            try:
                ioctl(self.fd, VIDIOC_ENUM_FMT,fmt)
            except IOError:
                break
            if i != fmt.index:
                print("Warning: driver returned wrong format index %u." % fmt.index)
            if type != fmt.type:
                print("Warning: driver returned wrong format type %u." % fmt.type)

            print("\tFormat %u: %s (%08x)" % (i, v4l2_format_name(fmt.pixelformat), fmt.pixelformat))
            print("\tType: %s (%s)" % (self.buf_types[fmt.type][1], fmt.type))
            print("\tName: %.32s" % fmt.description.decode() if isinstance(fmt.description, bytes) else fmt.description)
            self.video_enum_frame_sizes(fmt.pixelformat)
            Print('\n')
            i += 1

    def video_enum_inputs(self):
        input = v4l2_input()
        i = 0
        while True:
            input.index = i
            try:
                ioctl(self.fd, VIDIOC_ENUMINPUT, input)
            except IOError:
                break

            if i != input.index:
                print("Warning: driver returned wrong input index %u." % input.index)

            print("\tInput %u: %s." % (i, input.name.decode() if isinstance(input.name, bytes) else input.name))
            i += 1
        Print('\n')

def str_to_int(string):
    if string.find('0x') == 0:
        return int(string, 16)
    elif string[0] == '0':
        return int(string, 8)
    else:
        return int(string)


def get_options():
    pass


def main():
    pixelformat = V4L2_PIX_FMT_YUYV
    nframes = 0
    delay = 0
    width = 640
    height = 480
    input_ = 0
    stride = 0
    buffer_size = 0
    nbufs = 0
    fmt_flags = 0
    numerator = 0
    denominator = 0
    field = V4L2_FIELD_ANY
    dev = Video()
    if options.buf_type:
        dev.type = dev.v4l2_buf_type_from_string(options.buf_type)
        if dev.type == -1:
            print('Bad buffer type "%s"' % options.buf_type)
            sys.exit(1)
    else:
        dev.type = dev.cap_get_buf_type(dev.video_querycap())
    if options.fill_pad:
        dev.fill_mode |= BUFFER_FILL_PADDING
    elif options.fill_frames:
        dev.fill_mode |= BUFFER_FILL_FRAME
    if dev.fill_mode & BUFFER_FILL_PADDING and dev.memtype != V4L2_MEMORY_USERPTR:
        print("Buffer overrun can only be checked in USERPTR mode.")
        sys.exit(1)
    if options.capture:
        nframes = options.capture
    if options.delay:
        delay = options.delay
        if delay < 0:
            print("delay time must is a positive number")
            sys.exit(1)
    if options.file:
        file_ = options.file

    if options.input:
        input_ = options.input
    if options.nbufs:
        nbufs = options.nbufs

    if options.ctrl:
        try:
            id = str_to_int(options.ctrl)
        except ValueError:
            try:
                id = vic[options.ctrl]
            except KeyError:
                print("'%s' is not a right v4l2 control id." % options.ctrl)
                sys.exit()
        dev.video_print_control(id, False)
        sys.exit()
    if options.list_controls:
        dev.video_list_controls()
        sys.exit()
    if options.control:
        dev.set_control(options.control)
        sys.exit()
    if options.size:
        try:
            p = re.match("(\d+)x(\d+)", options.size)
            width, height = p.group(1), p.group(2)
        except Exception as m:
            print("Invalid size '%s'." % options.size)
            sys.exit(1)
    if options.time_per_frame:
        try:
            p = re.match("(\d+)/(\d+)", options.time_per_frame)
            numerator, denominator = p.group(1), p.group(2)
        except Exception as m:
            print("Invalid size '%s'." % options.time_per_frame)
            sys.exit(1)
    if options.memtype:
        dev.memtype = V4L2_MEMORY_USERPTR
    if options.buffer_size:
        buffer_size = options.buffer_size
    if options.enum_formats:
        print("- Available formats:")
        dev.video_enum_formats(V4L2_BUF_TYPE_VIDEO_CAPTURE)
        dev.video_enum_formats(V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE)
        dev.video_enum_formats(V4L2_BUF_TYPE_VIDEO_OUTPUT)
        dev.video_enum_formats(V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE)
        dev.video_enum_formats(V4L2_BUF_TYPE_VIDEO_OVERLAY)
        dev.video_enum_formats(V4L2_BUF_TYPE_META_CAPTURE)
    if options.enum_inputs:
        print("- Available inputs:")
        dev.video_enum_inputs()
    if options.info:
        if options.info == 'help':
            list_formats()
            sys.exit()
        try:
            pixelformat = fmt[options.info.upper()][0]
            if not dev.video_set_format(width, height, pixelformat,
                                        stride,buffer_size, field, fmt_flags):
                sys.exit(1)

        except KeyError as m:
            print("Unsupported video format '%s'." % m.args[0])
            sys.exit(1)

    if options.pause:
        try:
            input("Press enter to start capture\n")
        except NameError:
            raw_input("Press enter to start capture\n")


if __name__ == "__main__":
    main()
