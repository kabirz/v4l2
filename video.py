from videodev2 import *
from utils import *
from fcntl import ioctl
import ctypes, sys, errno, time
from v4l2Dev import V4l2
Print = sys.stdout.write

class Video(V4l2):
    def __init__(self, device_name='/dev/video0', **kwargs):
        super(Video, self).__init__(device_name, **kwargs)
        self.num_planes = 0
        self.width = 0
        self.height = 0
        self.fill_mode = BUFFER_FILL_NONE
        self.mp = ctypes.CDLL('libc.so.6')
        self.mp.mmap.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int)
        self.mp.mmap.restype = ctypes.c_void_p
        self.mp.munmap.argtypes = (ctypes.c_void_p, ctypes.c_int)
        self.plane_fmt = {}
        self.cap = v4l2_capability()
        ioctl(self.fd, VIDIOC_QUERYCAP, self.cap)

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
        print("Device '%s' on '%s' (driver '%s') supports%s mplanes." % (card, bus_info, driver, mplane))
        return caps

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
            print("Video format: %s (%#010x) %ux%u field %s, %u planes:" %
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
            print("Meta-data format: %s (%#010x) buffer size %u\n" %
                  (v4l2_format_name(fmt.fmt.meta.dataformat), fmt.fmt.meta.dataformat,
                   fmt.fmt.meta.buffersize))
        else:
            self.width = fmt.fmt.pix.width
            self.height = fmt.fmt.pix.height
            self.num_planes = 1

            self.plane_fmt[0] = v4l2_plane_pix_format()
            self.plane_fmt[0].bytesperline = fmt.fmt.pix.bytesperline
            self.plane_fmt[0].sizeimage = fmt.fmt.pix.sizeimage if fmt.fmt.pix.bytesperline else 0

            print("Video format: %s (%#010x) %ux%u (stride %u) field %s buffer size %u." %
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
            print("Video format set: %s (%010x) %ux%u field %s, %u planes: " %
                  (v4l2_format_name(fmt.fmt.pix_mp.pixelformat), fmt.fmt.pix_mp.pixelformat,
                   fmt.fmt.pix_mp.width, fmt.fmt.pix_mp.height, v4l2_field_name(fmt.fmt.pix_mp.field),
                   fmt.fmt.pix_mp.num_planes))

            for i in range(fmt.fmt.pix_mp.num_planes):
                print(" * Stride %u, buffer size %u." %
                      (fmt.fmt.pix_mp.plane_fmt[i].bytesperline,
                       fmt.fmt.pix_mp.plane_fmt[i].sizeimage))
        elif self.video_is_meta():
            print("Meta-data format: %s (%010x) buffer size %u." %
                  (v4l2_format_name(fmt.fmt.meta.dataformat), fmt.fmt.meta.dataformat,
                   fmt.fmt.meta.buffersize))
        else:
            print("Video format set: %s (%010x) %ux%u (stride %u) field %s buffer size %u." %
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
                print("Warning: driver returned wrong ival pixel format %#010x." % ival.pixel_format)
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
                print("Warning: driver returned wrong frame pixel format %#010x." % frame.pixel_format)

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

            print("\tFormat %u: %s (%#010x)" % (i, v4l2_format_name(fmt.pixelformat), fmt.pixelformat))
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

    def video_get_input(self):
        _input = ctypes.c_uint()
        try:
            ioctl(self.fd, VIDIOC_G_INPUT, _input)
            return _input.value
        except IOError as m:
            print("Unable to get current input: %s (%d)." % (m.strerror, m.errno))
            return -m.errno

    def video_set_input(self, input_):
        _input = ctypes.c_uint()
        _input.value = input_
        try:
            return ioctl(self.fd, VIDIOC_S_INPUT, _input)
        except IOError as m:
            print("Unable to select input %u: %s (%d)." % (input_,m.strerror, m.errno))
            return -m.errno
