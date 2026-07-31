import ctypes
from xdevsm.sm_framework.py_oran.dapp.enums import *

from xdevsm.sm_framework.py_oran.ByteArray import ByteArray
from xdevsm.sm_framework.lib.library_wrapper import dApp_lib, wrap_functions
from xdevsm.sm_framework.py_oran.dapp.report.DAppFunctionDef import dapp_e3_subscription_list_t


class e2sm_dapp_ind_msg_frmt_1_t(ctypes.Structure):
    _fields_ = [
        ("data_size", ctypes.c_size_t),
        ("data", ctypes.POINTER(ctypes.c_uint8)),
    ]


class e2sm_dapp_ind_msg_frmt_2_t(ctypes.Structure):
    _fields_ = [
        ("dapp_e3_subs", dapp_e3_subscription_list_t),
    ]

class DAppIndicationMsg(ctypes.Structure):

    class Union(ctypes.Union):
        _fields_ = [
            ("frmt_1", e2sm_dapp_ind_msg_frmt_1_t),
            ("frmt_2", e2sm_dapp_ind_msg_frmt_2_t),
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

    def get_data_format_1 (self) -> ByteArray:
        if self.dapp_ind_msg is None:
            print("DApp Indication Message is None, cannot get data")
            return None
        if self.dapp_ind_msg.format.value != e2sm_dapp_ind_msg_format_e.FORMAT_1_E2SM_DAPP_IND_MSG:
            print("DApp Indication Message format is not FORMAT_1, cannot get data {}".format(self.dapp_ind_msg.format.value))
            return None
        frmt_1 = self.dapp_ind_msg.union.frmt_1

        if not frmt_1.data or frmt_1.data_size == 0:
            print("DApp Indication Message FORMAT_1 contains no data")
            return None

        return ByteArray(
            len=frmt_1.data_size,
            buf=frmt_1.data
        )

    def get_data_format_2 (self) -> dapp_e3_subscription_list_t:
        if self.dapp_ind_msg is None:
            print("DApp Indication Message is None, cannot get data")
            return None
        if self.dapp_ind_msg.format.value != e2sm_dapp_ind_msg_format_e.FORMAT_2_E2SM_DAPP_IND_MSG:
            print("DApp Indication Message format is not FORMAT_2, cannot get data {}".format(self.dapp_ind_msg.format.value))
            return None
        frmt_2 = self.dapp_ind_msg.union.frmt_2
        return frmt_2.dapp_e3_subs
    
    def __del__(self):
        if self.dapp_ind_msg is not None:
            self.free(self.dapp_ind_msg)