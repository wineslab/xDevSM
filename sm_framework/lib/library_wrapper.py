import ctypes


def wrap_functions(library, funcname, restype, argtypes):
    """
    Simplify wrapping ctypes functions.

    Parameters
    ----------
    library: ctypes.CDLL
        libary path to be used
    funcname: str
        Name of library method
    restype: class
        Name of ctypes class; e.g., c_char_p
    argtypes: list
        List of ctypes classes; e.g., [ c_char_p, int ]

    Returns
    -------
    _FuncPointer:
        Pointer to C library function
    """
    func = library.__getattr__(funcname)
    func.restype = restype
    func.argtypes = argtypes
    return func


wrapper = ctypes.CDLL('libsm_framework.so')
kpm_lib = ctypes.CDLL('libkpm_sm.so')