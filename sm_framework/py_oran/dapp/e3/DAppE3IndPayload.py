import ctypes
from sm_framework.py_oran.dapp.enums import *

from sm_framework.py_oran.ByteArray import ByteArray
from sm_framework.lib.library_wrapper import dApp_lib, wrap_functions

class spectrum_sm_report_t(ctypes.Structure):
    _fields_ = [
        ("prb_count", ctypes.c_long),
        ("prbs", ctypes.POINTER(ctypes.c_uint16)),
    ]

class DAppE3IndPayload(ctypes.Structure):
    
    class Union(ctypes.Union):
        _fields_ = [
            ("spectrum", spectrum_sm_report_t),
        ]

    _fields_ = [
        ("type", dapp_e3_sm_type_e),
        ("u", Union),
    ]

class DAppE3IndPayloadWrapper():
    def __init__(self, ran_func_id: ctypes.c_uint32, byte_array: ByteArray):
        self.ran_function_id = ran_func_id
        self.byte_array = byte_array
        self.dapp_e3_ind_payload: DAppE3IndPayload = None
        self.decode_e3_ind_payload = wrap_functions(dApp_lib, 'dapp_dec_e3_indication', ctypes.c_bool, [ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(DAppE3IndPayload)])


    def decode(self) -> DAppE3IndPayload:
        if self.byte_array is None:
            return None
        
        # print(self.byte_array.len)
        # print(len(self.byte_array))
        payload = DAppE3IndPayload()

        ok = self.decode_e3_ind_payload(self.ran_function_id, self.byte_array.buf, self.byte_array.len, ctypes.byref(payload))
        
        if not ok:
            return None

        self.dapp_e3_ind_payload = payload
        return payload

    def get_spectrum_report(self) -> list:
        if self.dapp_e3_ind_payload is None:
            print("DApp E3 Indication Payload is None, cannot get spectrum report")
            return None
        if self.dapp_e3_ind_payload.type.value != dapp_e3_sm_type_e.DAPP_E3_SM_SPECTRUM:
            print("DApp E3 Indication Payload type is not SPECTRUM, cannot get spectrum report {}".format(self.dapp_e3_ind_payload.type.value))
            return None
        prb_count = self.dapp_e3_ind_payload.u.spectrum.prb_count
        prbs_ptr = self.dapp_e3_ind_payload.u.spectrum.prbs
        prbs = []
        for i in range(prb_count):
            prbs.append(prbs_ptr[i])
        return prbs
    
    # def __del__(self):
    #     if self.dapp_e2_ind_payload is not None:
    #         self.free(self.dapp_e2_ind_payload)