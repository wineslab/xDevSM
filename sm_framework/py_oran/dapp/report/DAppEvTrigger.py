import ctypes

from sm_framework.py_oran.dapp.enums import *
from sm_framework.py_oran.ByteArray import ByteArray
from sm_framework.lib.library_wrapper import dApp_lib, wrap_functions

class e2sm_dapp_ev_trg_frmt_1_t(ctypes.Structure):
    _fields_ = []

class DAppEvTrigger(ctypes.Structure):

    class Union(ctypes.Union):
        _fields_ = [
            ("frmt_1", e2sm_dapp_ev_trg_frmt_1_t),
        ]

    _fields_ = [
        ("format", e2sm_dapp_ev_trigger_format_e),
        ("union", Union),
    ]

class DAppEvTriggerWrapper():
    def __init__(self):
        self.dapp_ev_trigger: DAppEvTrigger = DAppEvTrigger()
        self.encode_event_trigger = wrap_functions(dApp_lib, 'dapp_enc_event_trigger_asn', ByteArray, [ctypes.POINTER(DAppEvTrigger)])

    def encode(self) -> ByteArray:
        if self.dapp_ev_trigger is None:
            # print("Event trigger byte array is None skipping decoding")
            return None
        dapp_ev_trigger_enc = self.encode_event_trigger(self.dapp_ev_trigger)
        return dapp_ev_trigger_enc
    

    def create_dummy_ev_trigger(self):
        self.dapp_ev_trigger.format = e2sm_dapp_ev_trigger_format_e.FORMAT_1_E2SM_DAPP_EV_TRIGGER_FORMAT
        # No fields to fill in frmt_1 for now
