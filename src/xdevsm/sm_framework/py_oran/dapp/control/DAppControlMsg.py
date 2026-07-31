import ctypes
from xdevsm.sm_framework.py_oran.dapp.enums import *

from xdevsm.sm_framework.py_oran.ByteArray import ByteArray
from xdevsm.sm_framework.lib.library_wrapper import dApp_lib, wrap_functions


class e2sm_dapp_ctrl_msg_frmt_1_t(ctypes.Structure):
    _fields_ = [
        ("data_size", ctypes.c_uint32),
        ("data", ctypes.POINTER(ctypes.c_uint8)),
    ]


class DAppControlMsg(ctypes.Structure):

    class Union(ctypes.Union):
        _fields_ = [
            ("frmt_1", e2sm_dapp_ctrl_msg_frmt_1_t),
        ]

    _fields_ = [
        ("format", e2sm_dapp_ctrl_msg_e),
        ("union", Union),
    ]

# class DAppControlMsgWrapper():
#     def __init__(self, format):
#         if format != e2sm_dapp_ctrl_msg_e.FORMAT_0_E2SM_DAPP_CTRL_MSG:
#             return
#         self.dapp_ctrl_msg: DAppControlMsg = DAppControlMsg()
#         self.dapp_ctrl_msg.format = format
        
#     #     self.encode_control_message = wrap_functions(dApp_lib, 'dapp_enc_ctrl_msg_asn', ByteArray, [ctypes.POINTER(DAppControlMsg)])

#     # def encode(self) -> ByteArray:
#     #     if self.dapp_ctrl_msg is None:
#     #         # print("DApp control message is None skipping encoding")
#     #         return None
#     #     ctrl_msg_enc = self.encode_control_message(self.dapp_ctrl_msg)
#     #     return ctrl_msg_enc

#     def create_format_0_ctrl_msg(self, data: ByteArray):
#         if self.dapp_ctrl_msg.format != e2sm_dapp_ctrl_msg_e.FORMAT_0_E2SM_DAPP_CTRL_MSG:
#             print("ERROR IN FORMAT TYPE FOR DApp Control Message")
#             return
#         self.dapp_ctrl_msg.union.frmt_0.data_size = data.len
#         self.dapp_ctrl_msg.union.frmt_0.data = data.buf


