import numpy as np
import ctypes

from xdevsm.decorators.base import BaseXDevSMWrapper

# osc xappframe
from ricxappframe.xapp_frame import rmr
from ricxappframe.e2ap.asn1 import ControlRequestMsg

import xdevsm.sm_framework.py_oran.kpm.KpmIndicationMsg as kpmmsg
import xdevsm.sm_framework.py_oran.rc.RCControlReq as ctrlReq
import xdevsm.sm_framework.py_oran.rc.RCControlHdr as ctrlhdr

# utility
from xdevsm.sm_framework.py_oran.dapp.control.DAppControlAck import decode_control_ack
from xdevsm.utils.constants import Values
from xdevsm._latrec.writer import tls_ring, seq_next, ctx_set, ctx_get
from xdevsm._latrec import stages
from xdevsm._latrec.stages import LATREC_ROLE as _LATREC_ROLE

class xAppControlService(BaseXDevSMWrapper):
    def __init__(self,
                xapp_handler,
                logger,
                server,
                xapp_name,
                rmr_port,
                http_port,
                mrc,
                pltnamespace,
                app_namespace,
                # UE ID parameters usually used in O-RAN Compliant control messages
                ue_id_type=None, 
                ue_id=None):
        super().__init__(xapp_handler, logger, server)
        self.xapp_name = xapp_name
        self.rmr_port = rmr_port
        self.http_port = http_port
        self._mrc = mrc
        self.pltnamespace = pltnamespace
        self.app_namespace = app_namespace
        
        # Not mandatory - parameters used only for specified controls
        self.ue_id_type = ue_id_type
        self.ue_id = ue_id

        # Ran function parameters
        self.style = None
        self.service_style_name = None
        self.function_id = -1

        # Function Definition Wrapper - data extractor from E2 manager
        self.function_def_wrapper = None

        # Service Model Wrapper - data encoding for Control Requests
        self.service_model_wrapper = None

        self.add_rmr_rule()
        self.__control_ack_handler_suc = None
        self.__control_ack_handler_fail = None

    def handle(self, xapp, summary, sbuf):
        if summary[rmr.RMR_MS_MSG_TYPE] == Values.RIC_CONTROL_ACK:
            xapp.logger.info("[xAppControlService] Received control ack")
            xapp.logger.debug("[xAppControlService] {}".format(summary))
            self._handle_control_ack_suc(xapp, summary, sbuf)
        elif summary[rmr.RMR_MS_MSG_TYPE] == Values.RIC_CONTROL_FAILURE:
            xapp.logger.error("[xAppControlService] Received failure ack")
            xapp.logger.debug("[xAppControlService] {}".format(summary))
            self._handle_control_ack_fail(xapp, summary, sbuf)
        else:
            xapp.logger.debug("[xAppControlService] This is not an RC message [{}]".format(summary[rmr.RMR_MS_MSG_TYPE]))
        self._xapp_handler.handle(xapp, summary, sbuf)    

    def get_ran_function_description(self, json_ran_info):
        """
        Get decoded ran function description
        Parameters:
        ----------
        json_ran_info (json obj): json object obtained when by the get_ran_info function

        This might be edited by subclasses to provide specific output according to the decorator needs.
        """

        if self.function_def_wrapper is None:
            self.logger.info("[xAppControlService] No function definition wrapper provided, cannot decode RAN function description")
            return
        
        if self.function_id == -1:
            self.logger.info("[xAppControlService] No function id provided, cannot decode RAN function description")
            return
        
        if not json_ran_info:
            self.logger.info("[xAppControlService] json_ran_info object None value not admitted!")
            return

        for ran_func in json_ran_info["gnb"]["ranFunctions"]: 
            if ran_func["ranFunctionId"] == self.function_id:
                # selecting rc action
                ran_function_definition = ran_func["ranFunctionDefinition"]
                break
        self.logger.info(ran_function_definition)
        # Decoding RAN function Definition
        self.function_def_wrapper.set_hex(hex=ran_function_definition)
        
        func_def_obj = self.function_def_wrapper.decode()
        return func_def_obj

    def generate_control_request(self, ue_id_struct=None, control_action_id=1, sequence_id=0):
        # defined in the subclasses -> depending on the type of control requested
        pass

    def send(self, e2_node_id, ran_func_dsc, ue_id_struct=None, control_action_id=1,
             sequence_id=0):
        """
        Sends a Control Request.

        Parameters:
        - e2_node_id: Target E2 node identifier
        - ran_func_dsc: Decoded RC function definition
        - control_action_id: ID of the control action to be performed
        - sequence_id: correlation id of the procedure this control belongs to,
          taken from the dApp report that prompted it. The RAN echoes it on the
          control outcome, so a control sent with 0 cannot be acknowledged.
        """

        if not ran_func_dsc.ctrl:
            # TODO Add error message
            return
        ctrl_descr = ran_func_dsc.ctrl.contents 
        
        # TODO to fix this for dApp
        self.style = next(
        (
            s for s in ctrl_descr.seq_ctrl_style[:ctrl_descr.sz_seq_ctrl_style]
            if bytes(np.ctypeslib.as_array(s.name.buf, shape=(s.name.len,))).decode('utf-8') == self.service_style_name),
            None
        )

        if self.style is None:
            self.logger.error("{} style not supported".format(self.service_style_name))
            return

        self.logger.info("{} style supported generating message".format(self.service_style_name))

        # ENCODE_E2SM_BEGIN: start of B5, the control decision's SM encode.
        # A fresh seq: this is the start of the policy-down leg, not a
        # continuation of whatever inbound message (if any) triggered it.
        seq = seq_next()
        ctx_set(seq)
        _lr = tls_ring(_LATREC_ROLE)
        _lr.stamp(seq, stages.ENCODE_E2SM_BEGIN)

        self.generate_control_request(ue_id_struct=ue_id_struct,
                                      control_action_id=control_action_id,
                                      sequence_id=sequence_id)

        # self.service_model_wrapper.print_ctrl_req()

        ctrl_req_enc = self.service_model_wrapper.encode()

        hdr_byte_array = ctrl_req_enc.hdr_encoded.to_bytes()
        ctrl_msg_byte_array = ctrl_req_enc.msg_encoded.to_bytes()

        self.logger.info("[xAppControlService] hdr encoded: {}".format(hdr_byte_array))
        self.logger.info("[xAppControlService] ctrl encoded: {}".format(ctrl_msg_byte_array))
        # ENCODE_E2SM_DONE: end of B5 -- hands to B6 (ENCODE_E2AP_BEGIN).
        _lr.stamp(seq, stages.ENCODE_E2SM_DONE,
                  aux=len(hdr_byte_array) + len(ctrl_msg_byte_array))
        self.send_control_request_rmr(e2_node_id=e2_node_id,
                                        control_header=hdr_byte_array,
                                        control_message=ctrl_msg_byte_array)
        

    def send_control_request_rmr(self, e2_node_id, control_header: bytes, control_message: bytes, call_process_id: bytes=b"1", requestor_id=1, control_ack_request=1, request_sequence_number=0, seq: int = None, retries: int = 100):

        # send() binds the seq it allocated; called directly, start a fresh one
        # rather than adopting whatever this thread last handled.
        if seq is None:
            seq = ctx_get() or seq_next()
        _lr = tls_ring(_LATREC_ROLE)
        # ENCODE_E2AP_BEGIN: start of B6, the E2AP framing of the control request.
        _lr.stamp(seq, stages.ENCODE_E2AP_BEGIN,
                  aux=len(control_header) + len(control_message))
        rc_ctrl_rec_msg = ControlRequestMsg()
        size, payload = rc_ctrl_rec_msg.encode(call_process_id=call_process_id,
                                               requestor_id=requestor_id,
                                               control_ack_request=control_ack_request,
                                               request_sequence_number=request_sequence_number,
                                               control_header=control_header,
                                               control_message=control_message,
                                               ran_function_id=self.function_id)

        self.logger.info("[xAppControlService] Sending Control Request Message: {} ({})".format(size, payload))
        # The alloc is outside the try: it raises BadBufferAllocation rather
        # than returning, so there would be nothing to free.
        sbuf = rmr.rmr_alloc_msg(vctx=self._mrc, size=len(payload), mtype=Values.RIC_CONTROL_REQ)
        try:
            rmr.set_payload_and_length(payload,sbuf)
            rmr.generate_and_set_transaction_id(sbuf)
            sbuf.contents.state = 0
            sbuf.contents.mtype = Values.RIC_CONTROL_REQ
            sbuf.contents.sub_id = -1
            self.logger.info("[xAppControlService] E2 node id: {}".format(e2_node_id.encode("utf8")))
            rmr.rmr_set_meid(sbuf, e2_node_id.encode("utf8"))
            # rmr_send_msg hands back a buffer for the next send: the same mbuf
            # re-armed on success, the unsent one on failure. Either way that is
            # the pointer to free, hence the rebind. Retry on a non-zero state
            # exactly as _BaseXapp.rmr_send does -- a single attempt drops the
            # control request silently on RMR_ERR_RETRY.
            for _ in range(retries):
                sbuf = rmr.rmr_send_msg(self._mrc, sbuf)
                if sbuf.contents.state == 0:
                    break
            else:
                self.logger.error(
                    "[xAppControlService] control request not sent after {} attempts (state={})".format(
                        retries, sbuf.contents.state))
            # ENCODE_E2AP_DONE: fires once the RMR send returns, matching the
            # shared catalog's own definition -- not when the encode alone
            # finishes (flexric stamps this the same way, see msg_handler_xapp.c).
            # On a failing send this now spans the retries, not one attempt.
            _lr.stamp(seq, stages.ENCODE_E2AP_DONE, aux=size)
            self.logger.info("[xAppControlService] Message Sent")
        finally:
            # RMR does not take ownership on send; without this the xApp leaks
            # one 4 KiB buffer per control request, for its whole lifetime.
            rmr.rmr_free_msg(sbuf)
    
    def _handle_control_ack_suc(self, xapp, summary, sbuf):
        self.logger.info("[xAppControlService] Handling control ack - default implementation")
        if not self.__control_ack_handler_suc:
            return
        # The callback gets the decoded acknowledge, which names the procedure it
        # answers and carries the Service Model's apply outcome. A PDU that does
        # not decode falls back to the raw RMR summary, so a handler written
        # before this existed keeps working; check `is not None` rather than
        # assuming a type.
        ack = decode_control_ack(summary.get(rmr.RMR_MS_PAYLOAD))
        self.__control_ack_handler_suc(ack if ack is not None else summary)

    def _handle_control_ack_fail(self, xapp, summary, sbuf):
        self.logger.info("[xAppControlService] Handling control failure ack - default implementation")
        if self.__control_ack_handler_fail:
            self.__control_ack_handler_fail(summary)
    

    def register_control_ack_suc_callback(self, handler):
        self.__control_ack_handler_suc = handler
    
    def register_control_ack_fail_callback(self, handler):
        self.__control_ack_handler_fail = handler
    

    def terminate(self, signum, frame):
        self.logger.info("[xAppControlService] Terminating xApp")
        self.delete_rmr_rule()

        self._xapp_handler.terminate(signum, frame)
    
    def add_rmr_rule(self):
        """
        Add RMR rule for control messages
        """
        # TODO
        self.logger.info("[xAppControlService] Adding RMR rule for control messages")
    
    def delete_rmr_rule(self):
        """
        Delete RMR rule for control messages
        """
        # TODO
        self.logger.info("[xAppControlService] Deleting RMR rule for control messages")
    
    ########## Temporary mock functions for UE ID ##########
    def get_mock_du_ue_id(self, ran_ue_id: ctypes.c_uint32) -> kpmmsg.ue_id_e2sm_t:
        ue_id = kpmmsg.ue_id_e2sm_t()
        ue_id.type = kpmmsg.ue_id_e2sm_e.GNB_DU_UE_ID_E2SM
        
        gnb_du = kpmmsg.gnb_du_e2sm_t()

        gnb_du.gnb_cu_ue_f1ap = ran_ue_id
        # gnb_du.ran_ue_id = 0 # We don't have this information in KPM messages in srs

        ue_id.union.gnb_du = gnb_du
        
        return ue_id
    
    def get_mock_ue_id(self, ran_ue_id: ctypes.c_ulong=1) -> kpmmsg.ue_id_e2sm_t:
        ue_id = kpmmsg.ue_id_e2sm_t()
        ue_id.type = ctrlhdr.ue_id_e2sm_e.GNB_UE_ID_E2SM
        
        gnb_mono = kpmmsg.gnb_e2sm_t()
        gnb_mono.amf_ue_ngap_id = 9
        
        # guami
        plmn_id = kpmmsg.e2sm_plmn_t()
        plmn_id.mcc = 1
        plmn_id.mnc = 1
        plmn_id.mnc_digit_len = 2 
        guami = kpmmsg.guami_t()
        guami.plmn_id = plmn_id
        guami.amf_region_id = 1
        guami.amf_set_id = 1
        guami.amf_ptr = 1
        gnb_mono.guami = guami

        gnb_mono.gnb_cu_ue_f1ap_lst_len = 0
        gnb_mono.gnb_cu_cp_ue_e1ap_lst_len = 0
        gnb_mono.ran_ue_id = ctypes.pointer(ctypes.c_ulong(ran_ue_id))

        # gnb_pointer = ctypes.pointer(gnb_mono)

        ue_id.union.gnb = gnb_mono

        return ue_id
    ########## ############################## ##########