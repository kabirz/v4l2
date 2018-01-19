import ctypes
from v4l2 import VIDEO_MAX_PLANES
PROT_NONE           = 0x1
PROT_READ           = 0x2
PROT_WRITE          = 0x4
MAP_ANON            = 0x1
MAP_ANONYMOUS       = MAP_ANON
MAP_FIXED           = 0x2
MAP_HASSEMAPHORE    = 0x4
MAP_INHERIT         = 0x8
MAP_NOCORE          = 0x10
MAP_NOSYNC          = 0x20
MAP_PREFAULT_READ   = 0x40
MAP_PRIVATE         = 0x80
MAP_SHARED          = 0x100
MAP_STACK           = 0x200
MAP_FAILED          = 0
MS_ASYNC            = 0x1
MS_SYNC             = 0x2
MS_INVALIDATE       = 0x3


buffer_fill_mode = ctypes.c_int
(
    BUFFER_FILL_NONE,
    BUFFER_FILL_FRAME,
    BUFFER_FILL_PADDING,
) = [0, 1, 2]

class buffer(ctypes.Structure):
    _fields_ = [
        ('idx', ctypes.c_uint),
        ('padding', ctypes.c_uint * VIDEO_MAX_PLANES),
        ('size', ctypes.c_uint * VIDEO_MAX_PLANES),
        ('mem', ctypes.c_void_p * VIDEO_MAX_PLANES),
    ]