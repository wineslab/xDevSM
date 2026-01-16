import ctypes
from sm_framework.py_oran.dapp.enums import *

from sm_framework.py_oran.ByteArray import ByteArray
from sm_framework.lib.library_wrapper import dApp_lib, wrap_functions

class e2sm_dapp_ind_hdr_frmt_0_t(ctypes.Structure):
    _fields_ = [
        ("ran_function_id", ctypes.c_uint32),
        ("dapp_id", ctypes.c_uint32),
    ]

class DAppIndHdr(ctypes.Structure):
    class Union(ctypes.Union):
        _fields_ = [
            ("frmt_0", e2sm_dapp_ind_hdr_frmt_0_t),
        ]

    _fields_ = [
        ("format", e2sm_dapp_ind_hdr_format_e),
        ("union", Union),
    ]


class DAppIndHdrWrapper():
    def __init__(self, byte_array: ByteArray):
        self.dapp_ind_hdr: DAppIndHdr = None
        self.byte_array = byte_array
        self.free = wrap_functions(dApp_lib, 'free_e2sm_dapp_ind_hdr', None, [ctypes.POINTER(DAppIndHdr)])
        self.decode_indication_header = wrap_functions(dApp_lib, 'dapp_dec_ind_hdr_asn', DAppIndHdr, [ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint8)])

    def decode(self) -> DAppIndHdr:
        if self.byte_array is None:
            return None
        self.dapp_ind_hdr = self.decode_indication_header(len(self.byte_array), self.byte_array)
        return self.dapp_ind_hdr

    def __del__(self):
        if self.dapp_ind_hdr is not None:
            self.free(self.dapp_ind_hdr)