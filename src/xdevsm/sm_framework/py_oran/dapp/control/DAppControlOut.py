import ctypes
from xdevsm.sm_framework.py_oran.dapp.enums import *

from xdevsm.sm_framework.py_oran.ByteArray import ByteArray
from xdevsm.sm_framework.lib.library_wrapper import dApp_lib, wrap_functions

# Mirrors e2sm_dapp_ctrl_out_frmt_1_t in FlexRIC's
# src/sm/dapp_sm/ie/ir/e2sm_dapp_ctrl_out_frmt_1.h. Field ORDER and TYPES must
# match the libdapp_sm.so shipped beside this file -- dapp_dec_ctrl_out_asn
# returns this struct by value, so an empty mirror here does not just miss
# both fields, it misreads the whole return.
class e2sm_dapp_ctrl_out_frmt_1_t(ctypes.Structure):
    _fields_ = [
        ("timestamp_ns", ctypes.c_int64),
        ("sequence_id", ctypes.c_int64),
        # The Service Model's own account of applying the control, opaque at this
        # layer and decoded by whichever SM the control's ran_function_id names.
        # For the Spectrum SM it is an APER Spectrum-ApplyOutcomeData carrying
        # when the mask was installed and when it first went on the air.
        ("e3_control_outcome", ctypes.POINTER(ctypes.c_uint8)),
        ("e3_control_outcome_size", ctypes.c_uint32),
    ]


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


