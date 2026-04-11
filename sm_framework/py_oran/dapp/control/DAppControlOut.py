import ctypes
from sm_framework.py_oran.dapp.enums import *

from sm_framework.py_oran.ByteArray import ByteArray
from sm_framework.lib.library_wrapper import dApp_lib, wrap_functions

class e2sm_dapp_ctrl_out_frmt_1_t(ctypes.Structure):
    _fields_ = []


class DAppControlOut(ctypes.Structure):

    class Union(ctypes.Union):
        _fields_ = [
            ("frmt_1", e2sm_dapp_ctrl_out_frmt_1_t),
        ]

    _fields_ = [
        ("format", e2sm_dapp_ctrl_out_e),
        ("union", Union),
    ]

# TODO need fixing
class DAppControlOutWrapper():
    def __init__(self, byte_array: ByteArray):
        self.dapp_ctrl_out: DAppControlOut = None
        # TODO free function missing in library
        # self.free = wrap_functions(dApp_lib, 'free_e2sm_dapp_ctrl_out', None, [ctypes.POINTER(DAppControlOut)])
        self.byte_array = byte_array
        self.decode_control_output = wrap_functions(dApp_lib, 'dapp_dec_ctrl_out_asn', DAppControlOut, [ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint8)])

    def decode(self) -> DAppControlOut:
        if self.byte_array is None:
            return None
        self.dapp_ctrl_out = self.decode_control_output(len(self.byte_array), self.byte_array)
        return self.dapp_ctrl_out

    # def __del__(self):
    #     if self.dapp_ctrl_out is not None:
    #         self.free(self.dapp_ctrl_out)


