from v4l2 import *
from v4l2 import __dict__ as v4l2_dict
from vivid import __dict__ as vivid_dict
from utils import *
from fcntl import ioctl
import re
import ctypes, os, sys, errno, time

class V4l2(object):
    def __init__(self, device_name):
        self.type = None
        self.memtype = V4L2_MEMORY_MMAP
        self.buffer_ = None
        self.width = 0
        self.height = 0
        self.enum_controls = False
        self.ctl_id = 0
        self.fd = None
        try:
            self.fd = open(device_name, 'r')
            print("Device %s opened." % device_name)
        except IOError as s:
            print("Error opening device '%s': %s (%d)." % (device_name, s.strerror, s.errno))
            sys.exit()

        self.buf_types = {
                V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE:(1, "Video capture mplanes", "capture-mplane"),
                V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE:(1, "Video output", "output-mplane"),
                V4L2_BUF_TYPE_VIDEO_CAPTURE:(1, "Video capture", "capture"),
                V4L2_BUF_TYPE_VIDEO_OUTPUT:(1, "Video output mplanes", "output"),
                V4L2_BUF_TYPE_VIDEO_OVERLAY:(0, "Video overlay", "overlay"),
                V4L2_BUF_TYPE_META_CAPTURE:(1, "Meta-data capture", "meta-capture")
                }

    def __del__(self):
        self.fd.close()

    def v4l2_buf_type_from_string(self, string):
        for key, value in self.buf_types:
            if value[0] and value[1] == string:
                return key
        return False


    def v4l2_buf_type_name(self, buf_type):
        if buf_type in self.buf_types.keys():
            return self.buf_types[buf_type][1] if self.buf_types[buf_type][0] else 'Private'
        else:
            return 'Unknown'

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
                print("unable to query control %#010x: %s (%d)" % (id, m.strerror, m.errno))
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
            if (query.type != V4L2_CTRL_TYPE_INTEGER64 and
                    query.type != V4L2_CTRL_TYPE_STRING):
                old = v4l2_control()
                old.id = query.id
                try:
                    ioctl(self.fd, VIDIOC_G_CTRL, old)
                    ctrl.value = old.value
                    return 0
                except IOError as m:
                    ctrl.value = old.value
            if not self.enum_controls:
                print("unable to get control %#010x: %s (%d)." % (query.id, s.strerror, s.errno))
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
            print("unable to set control %#010x" % id)
        else:
            if not is_64 and query.type != V4L2_CTRL_TYPE_STRING:
                old = v4l2_control()
                old.id = id
                old.value = val
            try:
                ioctl(self.fd, VIDIOC_S_CTRL, old)
            except IOError:
                val = old.value
                print("unable to set control %#010x" % id)
            print("Control %#010x set to %#x, is %#x" % (id, old_val, val))

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

    def v4l2_query_menu(self, query, value):
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

    def _get_ctrl_name(self, id):
        val = {}
        if id in v4l2_dict.values():
            val = v4l2_dict
        elif id in vivid_dict.values():
            val = vivid_dict
        for ctrl, _id in val.items():
            if _id == id:
                return ctrl
        return "unknown"


    def v4l2_print_control(self, id, full=True):
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
            if self.enum_controls:
                ctrl = self._get_ctrl_name(query.id)
                print('%-40s %#010x\t"%s"' % (ctrl, query.id, qname))
            else:
                print("--- %s (class %#010x) ---" %(qname, query.id))
            return True
        if self.get_control(query, ctrl) == -1:
            val = 'n/a'
        elif query.type == V4L2_CTRL_TYPE_INTEGER64:
            val =  ctrl.value64
        elif query.type == V4L2_CTRL_TYPE_STRING:
            val = ctrl.string.decode() if isinstance(ctrl.string, bytes) else ctrl.string
        else:
            val = ctrl.value


        if self.enum_controls:
            ctrl = self._get_ctrl_name(query.id)
            print('%-40s %#010x\t"%s"' % (ctrl, query.id, qname))
            return True
        elif full:
            print("control %#010x '%s' min %d max %d step %d default %d current %s."
                    % (query.id, qname, query.minimum, query.maximum,
                        query.step, query.default_value, str(val)))
        else:
            print("control %#010x current %s." % (query.id, str(val)))

        if query.type == V4L2_CTRL_TYPE_STRING:
            pass # TODO free ctrl.string

        if not full:
            return True
        if query.type == V4L2_CTRL_TYPE_MENU or query.type == V4L2_CTRL_TYPE_INTEGER_MENU:
            self.v4l2_query_menu(query, ctrl.value)
        return True

    def v4l2_list_controls(self):
        nctrls = 0
        while self.v4l2_print_control(self.ctl_id | V4L2_CTRL_FLAG_NEXT_CTRL):
            nctrls += 1

        if nctrls:
            print("%u control%s found." % (nctrls, "s" * bool(nctrls - 1)))
        else:
            print("No control found.")