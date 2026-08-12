import ctypes

from xdevsm.sm_framework.py_oran.dapp.control import DAppControlHdr as hdr
from xdevsm.sm_framework.py_oran.dapp.control import DAppControlMsg as ctrl

from xdevsm.sm_framework.py_oran.ByteArray import ByteArray
from xdevsm.sm_framework.lib.library_wrapper import dApp_lib, wrap_functions


class DAppControlReq(ctypes.Structure):
    _fields_ = [
        ("hdr", hdr.DAppControlHdr),
        ("msg", ctrl.DAppControlMsg),  # Union for the various data types
    ]

class DAppControlReqEncoded(ctypes.Structure):
    _fields_ = [
        ("hdr_encoded", ByteArray),
        ("msg_encoded", ByteArray)
    ]

class DAppControlReqWrapper():
    def __init__(self):
        self.dapp_ctrl_req = DAppControlReq()
        self._payload_ref = None
        self.encode_control_header = wrap_functions(dApp_lib, 'dapp_enc_ctrl_hdr_asn', ByteArray, [ctypes.POINTER(hdr.DAppControlHdr)])
        self.encode_control_message = wrap_functions(dApp_lib, 'dapp_enc_ctrl_msg_asn', ByteArray, [ctypes.POINTER(ctrl.DAppControlMsg)])
        

    def encode(self) -> DAppControlReqEncoded:
        dapp_ctrl_req_enc = DAppControlReqEncoded()
        dapp_ctrl_req_enc.hdr_encoded = self.encode_control_header(self.dapp_ctrl_req.hdr)
        dapp_ctrl_req_enc.msg_encoded = self.encode_control_message(self.dapp_ctrl_req.msg)
        return dapp_ctrl_req_enc
    
    def generate_control_req_frmt_1(self, ran_function_id: int, dapp_id: int, payload: ByteArray):
        self._payload_ref = payload
        self.dapp_ctrl_req.hdr = hdr.DAppControlHdr()
        self.dapp_ctrl_req.hdr.format = hdr.e2sm_dapp_ctrl_hdr_e.FORMAT_1_E2SM_DAPP_CTRL_HDR
        self.dapp_ctrl_req.hdr.union.frmt_1 = hdr.e2sm_dapp_ctrl_hdr_frmt_1_t()
        self.dapp_ctrl_req.hdr.union.frmt_1.ran_function_id = ran_function_id
        self.dapp_ctrl_req.hdr.union.frmt_1.dapp_id = dapp_id
        self.dapp_ctrl_req.msg = ctrl.DAppControlMsg()
        self.dapp_ctrl_req.msg.format = ctrl.e2sm_dapp_ctrl_msg_e.FORMAT_1_E2SM_DAPP_CTRL_MSG
        self.dapp_ctrl_req.msg.union.frmt_1 = ctrl.e2sm_dapp_ctrl_msg_frmt_1_t()
        self.dapp_ctrl_req.msg.union.frmt_1.data_size = self._payload_ref.len
        self.dapp_ctrl_req.msg.union.frmt_1.data = self._payload_ref.buf