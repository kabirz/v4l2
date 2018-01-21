import ctypes

_IOC_NRBITS     = 8
_IOC_TYPEBITS   = 8
_IOC_SIZEBITS   = 14
_IOC_DIRBITS    = 2

_IOC_NRMASK     = (1 << _IOC_NRBITS) - 1
_IOC_TYPEMASK   = (1 <<_IOC_TYPEBITS) - 1
_IOC_SIZEMASK   = (1 << _IOC_SIZEBITS) - 1
_IOC_DIRMASK    = (1 << _IOC_DIRBITS) - 1


_IOC_NRSHIFT    = 0
_IOC_TYPESHIFT  = _IOC_NRSHIFT + _IOC_NRBITS
_IOC_SIZESHIFT  = _IOC_TYPESHIFT + _IOC_TYPEBITS
_IOC_DIRSHIFT   = _IOC_SIZESHIFT + _IOC_SIZEBITS


_IOC_NONE       = 0
_IOC_WRITE      = 1
_IOC_READ       = 2

def _IOC(dir_, type_, nr, size):
    return (
            ctypes.c_int32(dir_ << _IOC_DIRSHIFT).value |
            ctypes.c_int32(ord(type_) << _IOC_TYPESHIFT).value |
            ctypes.c_int32(nr << _IOC_NRSHIFT).value |
            ctypes.c_int32(size << _IOC_SIZESHIFT).value)

def _IOC_TYPECHECK(t):
    return ctypes.sizeof(t)

def _IO(type_, nr):
    return _IOC(_IOC_NONE, type_, nr, 0)

def _IOR(type_, nr, size):
    return _IOC(_IOC_READ, type_, nr, _IOC_TYPECHECK(size))

def _IOW(type_, nr, size):
    return _IOC(_IOC_WRITE, type_, nr, _IOC_TYPECHECK(size))

def _IOWR(type_, nr, size):
    return _IOC(_IOC_READ | _IOC_WRITE, type_, nr, _IOC_TYPECHECK(size))

def _IOR_BAD(type_, nr, size):
    return _IOC(_IOC_READ, type_, nr, _IOC_TYPECHECK(size))

def _IOW_BAD(type_, nr, size):
    return _IOC(_IOC_WRITE, type_, nr, _IOC_TYPECHECK(size))

def _IOWR_BAD(type_, nr, size):
    return _IOC(_IOC_READ | _IOC_WRITE, type_, nr, _IOC_TYPECHECK(size))

def _IOC_DIR(nr):
    return ctypes.c_int32(nr >> _IOC_DIRSHIFT).value & _IOC_DIRMASK

def _IOC_TYPE(nr):
    return ctypes.c_int32(nr >> _IOC_TYPESHIFT).value & _IOC_TYPESHIFT

def _IOC_NR(nr):
    return ctypes.c_int32(nr >> _IOC_NRSHIFT).value & _IOC_NRMASK

def _IOC_SIZE(nr):
    return ctypes.c_int32(nr >> _IOC_SIZESHIFT).value & _IOC_SIZEMASK

IOC_IN          = _IOC_WRITE << _IOC_DIRSHIFT
IOC_OUT         =  _IOC_READ << _IOC_DIRSHIFT
IOC_INOUT       = (_IOC_WRITE | _IOC_READ) << _IOC_DIRSHIFT
IOCSIZE_MASK    = _IOC_SIZEMASK << _IOC_SIZESHIFT
IOCSIZE_SHIFT   = _IOC_SIZESHIFT

