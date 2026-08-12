import ctypes
from xdevsm.sm_framework.py_oran.dapp.enums import *

from xdevsm.sm_framework.py_oran.ByteArray import ByteArray
from xdevsm.sm_framework.lib.library_wrapper import dApp_lib, wrap_functions


class spectrum_sm_control_t(ctypes.Structure):
    _fields_ = [
        ("prb_count", ctypes.c_long),
        ("blockedPRBs", ctypes.POINTER(ctypes.c_uint16)),
    ]

class DAppE3CtrlPayload(ctypes.Structure):
    class Union(ctypes.Union):
        _fields_ = [
            ("spectrum", spectrum_sm_control_t),
        ]

    _fields_ = [
        ("type", dapp_e3_sm_type_e),
        ("u", Union),
    ]

class DAppE3CtrlPayloadWrapper():
    def __init__(self, dapp_type: dapp_e3_sm_type_e):
        self.dapp_e3_ctrl_payload = DAppE3CtrlPayload()
        self.dapp_e3_ctrl_payload.type = dapp_type
        self._blocked_prbs_array = None
        self.encode_e3_spectrum_payload = wrap_functions(dApp_lib, 'dapp_enc_e3_control', ctypes.c_bool, [ctypes.c_uint32, ctypes.POINTER(DAppE3CtrlPayload), ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)), ctypes.POINTER(ctypes.c_size_t)])
        
    def set_spectrum_control(self, blocked_prbs: list):
        self.dapp_e3_ctrl_payload.u.spectrum = spectrum_sm_control_t()
        self.dapp_e3_ctrl_payload.u.spectrum.prb_count = len(blocked_prbs)
        if blocked_prbs == 0 :
            return
        blocked_prbs_array_type = ctypes.c_uint16 * len(blocked_prbs)
        self._blocked_prbs_array = blocked_prbs_array_type()

        for i, prb in enumerate(blocked_prbs):
            self._blocked_prbs_array[i] = prb

        self.dapp_e3_ctrl_payload.u.spectrum.blockedPRBs = self._blocked_prbs_array
        

    def encode(self) -> ByteArray:
        byte_array = ByteArray()

        out_buf = ctypes.POINTER(ctypes.c_uint8)()
        out_size = ctypes.c_size_t()

        success = self.encode_e3_spectrum_payload(
            1,
            self.dapp_e3_ctrl_payload,
            ctypes.byref(out_buf),    
            ctypes.byref(out_size)    
        )

        if not success:
            raise Exception("Failed to encode DApp E3 Control Payload")

        byte_array.buf = out_buf
        byte_array.len = out_size.value

        return byte_array
        
        
        
