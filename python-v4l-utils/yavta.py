#!/usr/bin/env python

from v4l2 import *
from fcntl import *
import ctypes
import sys

class video:
    def __init__(self, deviceName='/dev/video0'):
        self.fd = open(deviceName, 'rw')
        self.type_ = None
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
                };

    def __delete__(self):
        self.fd.close()

    def video_is_mplane(self):
        return (self.type_ == V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE or
                self.type_ == V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE)

    def video_is_meta(self):
        return self.type_ == V4L2_BUF_TYPE_META_CAPTURE

    def video_is_capture(self):
        return (self.type_ == V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE or
                self.type_ == V4L2_BUF_TYPE_VIDEO_CAPTURE or
                self.type_ == V4L2_BUF_TYPE_META_CAPTURE)

    def video_is_output(self):
        return (self.type_ == V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE or
                self.type_ == V4L2_BUF_TYPE_VIDEO_OUTPUT)
    def v4l2_buf_type_from_string(self, string):
        for item in self.buf_types.items():
            if item[1][0] and item[1][2] == string:
                return item[0]
        return False
    def v4l2_buf_type_name(self, buf_type):
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
        return 0


    def query_control(self, id, query):
        query.id = id
        try:
            ioctl(self.fd, VIDIOC_QUERYCTRL, query)
        except IOError, args:
            print("unable to query control 0x%8.8x: %s" % (id, args))
            return False
        return True

    def get_control(self, query, ctrl):
        ctrls = v4l2_ext_controls()
        ctrls.count = 1
        ctrls.controls = ctypes.pointer(ctrl)
        ctrl.id = query.id
        
        if query.type == V4L2_CTRL_TYPE_STRING:
            ctrl.string = ctypes.cast(ctypes.create_string_buffer(query.maxinum + 1), ctypes.c_char_p)
            ctrl.size = query.maxinum + 1

        ret = ioctl(self.fd, VIDIOC_G_EXT_CTRLS, ctrls)
        if ret == -1:
            return 0

        if query.type != V4L2_CTRL_TYPE_INTEGER64 and query.type != V4L2_CTRL_TYPE_STRING:
            old = v4l2_control()
            old.id = query.id
            ret = ioctl(self.fd, VIDIOC_G_CTRL, old)
            if ret == -1:
                ctrl.value = old.value
                return 0

        print("unable to get control 0x%8.8x." % query.id)
        return -1
    def set_control(self, id, val):
        ctrls = v4l2_ext_controls()
        ctrl = v4l2_ext_control()
        query = v4l2_queryctrl()
        old_val = val

        if query_control(id, query) < 0:
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

def get_options():
    pass
def main():
    pass

if __name__ == "__main__":
    main()
