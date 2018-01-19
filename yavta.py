#!/usr/bin/env python

from v4l2 import *
from fcntl import ioctl
import yavta_help
import ctypes
import sys
import errno

(options, args) = yavta_help.parser.parse_args()


class Video:
    def __init__(self, device_name='/dev/video0'):
        if len(args) > 0:
            device_name = args[0]
        self.fd = None
        try:
            self.fd = open(device_name, 'r')
        except IOError as s:
            print("Error opening device '%s': %s (%d)." % (device_name, s.strerror, s.errno))
            sys.exit()
        self.type = None
        self.memtype = None
        self.buffer_ = None
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
        if type(self.fd) == 'file':
            self.fd.close()

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
        return False

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
        print("Device `%s' on `%s' (driver '%s') supports%s mplanes."
                % (self.cap.card, self.cap.bus_info, self.cap.driver, mplane))
        return caps

    def cap_get_buf_type(self, caps):
        if caps == V4L2_CAP_VIDEO_CAPTURE_MPLANE:
            return V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE
        elif caps == V4L2_CAP_VIDEO_OUTPUT_MPLANE:
            return V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE
        elif caps == V4L2_CAP_VIDEO_CAPTURE:
            return V4L2_BUF_TYPE_VIDEO_CAPTURE
        elif caps == V4L2_CAP_VIDEO_OUTPUT:
            return V4L2_BUF_TYPE_VIDEO_OUTPUT
        elif caps == V4L2_CAP_META_CAPTURE:
            return V4L2_BUF_TYPE_META_CAPTURE
        else:
            print("Device supports neither capture nor output.")
            return -1

    def query_control(self, id, query):
        query.id = id
        try:
            ioctl(self.fd, VIDIOC_QUERYCTRL, query)
        except IOError as m :
            print("unable to query control 0x%8.8x: %s" % (id, m))
            return -m.errno
        return 0

    def get_control(self, query, ctrl):
        ctrls = v4l2_ext_controls()
        ctrls.count = 1
        ctrls.controls = ctypes.pointer(ctrl)
        ctrl.id = query.id

        if query.type == V4L2_CTRL_TYPE_STRING:
            ctrl.string = ctypes.cast(ctypes.create_string_buffer(query.maxinum + 1), ctypes.c_char_p)
            ctrl.size = query.maxinum + 1

        try:
            ioctl(self.fd, VIDIOC_G_EXT_CTRLS, ctrls)
            return 0
        except IOError as s:
            if(query.type != V4L2_CTRL_TYPE_INTEGER64 and
                    query.type != V4L2_CTRL_TYPE_STRING and
                    (s.error == errno.EINVAL or s.error == errno.ENOTTY)):
                old = v4l2_control()
                old.id = query.id
                ret = ioctl(self.fd, VIDIOC_G_CTRL, old)
                if ret != -1:
                    ctrl.value = old.value
                    return 0
            else:
                print("unable #to get control 0x%8.8x: %s (%d)." % (query.id, s.strerror, s.errno))
                return -1
        return 0

    def set_control(self, id, val):
        ctrls = v4l2_ext_controls()
        ctrl = v4l2_ext_control()
        query = v4l2_queryctrl()
        old_val = val

        if self.query_control(id, query):
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
        ret = ioctl(self.fd, VIDIOC_S_EXT_CTRLS, ctrls)
        if ret == -1:
            val = ctrl.value64 if is_64 else ctrl.value
        elif not is_64 and query.type != V4L2_CTRL_TYPE_STRING:
            old = v4l2_control()
            old.id = id
            old.value = val
            ret = ioctl(self.fd, VIDIOC_S_CTRL, old)
            if ret != -1:
                val = old.value
        if ret == -1:
            print("unable to set control 0x%8.8x" % id)
            return
        print("Control 0x%08x set to %x, is %x" % (id, old_val, val))

    def video_query_menu(self, query, value):
        menu = v4l2_querymenu()
        for i in range(query.minimum, query.maximum + 1):
            menu.index = i
            menu.id = query.id
            ret = ioctl(self.fd, VIDIOC_QUERYMENU, menu)
            if ret < 0:
                continue
            if query.type == V4L2_CTRL_TYPE_MENU:
                print("  %u: %.32s%s" % (menu.index, menu.name, " (*)" if menu.index == value else ""))
            else:
                print("  %u: %lld%s" % (menu.index, menu.name, " (*)" if menu.index == value else ""))

    def video_print_control(self, id, full=True):
        ctrl = v4l2_ext_control()
        query = v4l2_queryctrl()
        ret = self.query_control(id, query)
        if ret < 0:
            return ret
        if query.flags & V4L2_CTRL_FLAG_DISABLED:
            return query.id
        if query.type == V4L2_CTRL_TYPE_CTRL_CLASS:
            print("--- %s (class 0x%08x) ---" %(query.name, query.id))
            return query.id
        if self.get_control(query, ctrl) == -1:
            return -1
        if query.type == V4L2_CTRL_TYPE_INTEGER64:
            val =  ctrl.value64
        elif query.type == V4L2_CTRL_TYPE_STRING:
            val = ctrl.string
        else:
            val = ctrl.value

        if full:
            print("control 0x%08x `%s' min %d max %d step %d default %d current %s."
                    % (query.id, query.name, query.minimum, query.maximum,
                        query.step, query.default_value, str(val)))
        else:
            print("control 0x%08x current %s." % (query.id, str(val)))

        if query.type == V4L2_CTRL_TYPE_STRING:
            pass # TODO free ctrl.string

        if not full:
            return query.id
        if query.type == V4L2_CTRL_TYPE_MENU or query.type == V4L2_CTRL_TYPE_INTEGER_MENU:
            self.video_query_menu(query, ctrl.value)
        return query.id


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
    dev = Video()
    if options.ctrl:
        try:
            id_ = str_to_int(options.ctrl)
        except ValueError:
            try:
                id_ = vic[options.ctrl]
            except KeyError:
                print("'%s' is not a right v4l2 control id." % options.ctrl)
                return

        dev.video_print_control(id_)


if __name__ == "__main__":
    main()
