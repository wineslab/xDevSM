import ctypes
import os

# Directory that ships the prebuilt Service Model encoders alongside this module.
_LIB_DIR = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    """Load a bundled ``.so`` by package-relative absolute path.

    The encoders are loaded with ``RTLD_GLOBAL`` so their symbols stay visible to
    the others: ``libsm_framework.so`` has a ``NEEDED`` dependency on
    ``libkpm_sm.so``, which must therefore be loaded (globally) first. Falling back
    to a bare-name load keeps legacy deployments working when the libraries are
    reachable through ``LD_LIBRARY_PATH`` instead (e.g. older Docker images).
    """
    path = os.path.join(_LIB_DIR, name)
    try:
        return ctypes.CDLL(path, mode=ctypes.RTLD_GLOBAL)
    except OSError:
        return ctypes.CDLL(name, mode=ctypes.RTLD_GLOBAL)


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


# Load kpm first: libsm_framework.so has a NEEDED dependency on libkpm_sm.so, so it
# must already be resolvable (as a loaded RTLD_GLOBAL library) before we load the framework.
kpm_lib = _load('libkpm_sm.so')
wrapper = _load('libsm_framework.so')
rc_lib = _load('librc_1_03.so')
dApp_lib = _load('libdapp_sm.so')