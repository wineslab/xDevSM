import ctypes
import numpy as np

from sm_framework.py_oran.dapp.enums import *

from sm_framework.py_oran.ByteArray import ByteArray
from sm_framework.lib.library_wrapper import dApp_lib, wrap_functions

class e2sm_dapp_act_def_frmt_1_t(ctypes.Structure):
    _fields_ = []

class DAppActionDef(ctypes.Structure):

    class Union(ctypes.Union):
        _fields_ = [
            ("frmt_1", e2sm_dapp_act_def_frmt_1_t),
        ]

    _fields_ = [
        ("ric_style_type", ctypes.c_uint32),
        ("format", e2sm_dapp_action_def_format_e),
        ("union", Union),
    ]

class DAppActionDefWrapper():
    def __init__(self):
        self.dapp_function_def: DAppActionDef = DAppActionDef()
        self.encode_function_definition = wrap_functions(dApp_lib, 'dapp_enc_action_def_asn', ByteArray, [ctypes.POINTER(DAppActionDef)])

    def encode(self) -> ByteArray:
        if self.dapp_function_def is None:
            # print("DApp function definition is None skipping encoding")
            return None
        action_def_enc = self.encode_function_definition(self.dapp_function_def)
        return action_def_enc


    def create_dummy_action_def(self):
        self.dapp_function_def.ric_style_type = 1
        self.dapp_function_def.format = e2sm_dapp_action_def_format_e.FORMAT_1_E2SM_DAPP_ACTION_DEF
        # No fields to fill in frmt_1 for now
