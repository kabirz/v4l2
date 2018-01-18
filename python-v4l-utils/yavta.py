#!/usr/bin/env python

from v4l2 import *
from fcntl import *
import ctypes
import sys

class video:
    def __init__(self, deviceName):
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
        has_mplane = ("with" if caps & (V4L2_CAP_VIDEO_CAPTURE_MPLANE | V4L2_CAP_VIDEO_OUTPUT_MPLANE) else "without")
        mplane =  has_video + has_meta + has_capture + has_output + has_mplane
        print("Device `%s' on `%s' (driver '%s') supports%s%s%s%s %s mplanes.",
		(self.cap.card, self.cap.bus_info, self.cap.driver, mplane))



        print caps


def get_options():
    pass
def main():
    pass

if __name__ == "__main__":
    main()
