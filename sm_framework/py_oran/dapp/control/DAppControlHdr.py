import ctypes
from sm_framework.py_oran.dapp.enums import *

from sm_framework.py_oran.ByteArray import ByteArray
from sm_framework.lib.library_wrapper import dApp_lib, wrap_functions



class e2sm_dapp_ctrl_hdr_frmt_1_t(ctypes.Structure):
    _fields_ = [
        ("ran_function_id", ctypes.c_uint32),
        ("dapp_id", ctypes.c_uint32),
    ]

class DAppControlHdr(ctypes.Structure):

    class Union(ctypes.Union):
        _fields_ = [
            ("frmt_1", e2sm_dapp_ctrl_hdr_frmt_1_t),
        ]

    _fields_ = [
        ("format", e2sm_dapp_ctrl_hdr_e),
        ("union", Union),
    ]

# class DAppControlHdrWrapper():
#     def __init__(self, format):
#         self.dapp_ctrl_hdr: DAppControlHdr = DAppControlHdr()
#         self.dapp_ctrl_hdr.format = format
        
#         # self.free = wrap_functions(dApp_lib, 'free_e2sm_dapp_ctrl_hdr', None, [ctypes.POINTER(DAppControlHdr)])
#     #     self.encode_control_header = wrap_functions(dApp_lib, 'dapp_enc_ctrl_hdr_asn', ByteArray, [ctypes.POINTER(DAppControlHdr)])

#     # def encode(self) -> ByteArray:
#     #     if self.dapp_ctrl_hdr is None:
#     #         # print("DApp control header is None skipping encoding")
#     #         return None
#     #     ctrl_hdr_enc = self.encode_control_header(self.dapp_ctrl_hdr)
#     #     return ctrl_hdr_enc
    
#     def create_format_0_ctrl_hdr(self, ran_function_id: int, dapp_id: int):
#         if self.dapp_ctrl_hdr.format != e2sm_dapp_ctrl_hdr_e.FORMAT_0_E2SM_DAPP_CTRL_HDR:
#             print("ERROR IN FORMAT TYPE FOR DApp Control Header")
#             return
#         self.dapp_ctrl_hdr.union.frmt_0.ran_function_id = ran_function_id
#         self.dapp_ctrl_hdr.union.frmt_0.dapp_id = dapp_id