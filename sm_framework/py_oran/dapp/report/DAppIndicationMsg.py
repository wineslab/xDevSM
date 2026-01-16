import ctypes
from sm_framework.py_oran.dapp.enums import *

from sm_framework.py_oran.ByteArray import ByteArray
from sm_framework.lib.library_wrapper import dApp_lib, wrap_functions


class e2sm_dapp_ind_msg_frmt_0_t(ctypes.Structure):
    _fields_ = [
        ("data_size", ctypes.c_size_t),
        ("data", ctypes.POINTER(ctypes.c_uint8)),
    ]

class DAppIndicationMsg(ctypes.Structure):

    class Union(ctypes.Union):
        _fields_ = [
            ("frmt_0", e2sm_dapp_ind_msg_frmt_0_t),
        ]

    _fields_ = [
        ("format", e2sm_dapp_ind_msg_format_e),
        ("union", Union),
    ]


class DAppIndicationMsgWrapper():
    def __init__(self, byte_array: ByteArray):
        self.byte_array = byte_array
        self.dapp_ind_msg: DAppIndicationMsg = None
        self.free = wrap_functions(dApp_lib, 'free_e2sm_dapp_ind_msg', None, [ctypes.POINTER(DAppIndicationMsg)])
        self.decode_indication_message = wrap_functions(dApp_lib, 'dapp_dec_ind_msg_asn', DAppIndicationMsg, [ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint8)])

    def decode(self) -> DAppIndicationMsg:
        if self.byte_array is None:
            # print("Message byte array is None skipping decoding")
            return None
        self.dapp_ind_msg = self.decode_indication_message(len(self.byte_array), self.byte_array)
        return self.dapp_ind_msg

    def get_data_format_0 (self) -> ByteArray:
        if self.dapp_ind_msg is None:
            print("DApp Indication Message is None, cannot get data")
            return None
        if self.dapp_ind_msg.format.value != e2sm_dapp_ind_msg_format_e.FORMAT_0_E2SM_DAPP_IND_MSG:
            print("DApp Indication Message format is not FORMAT_0, cannot get data {}".format(self.dapp_ind_msg.format.value))
            return None
        frmt_0 = self.dapp_ind_msg.union.frmt_0

        if not frmt_0.data or frmt_0.data_size == 0:
            print("DApp Indication Message FORMAT_0 contains no data")
            return None

        return ByteArray(
            len=frmt_0.data_size,
            buf=frmt_0.data
        )

    def __del__(self):
        if self.dapp_ind_msg is not None:
            self.free(self.dapp_ind_msg)