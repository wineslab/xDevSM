import numpy as np

# osc xappframe
from ricxappframe.xapp_frame import rmr
from ricxappframe.e2ap.asn1 import ControlRequestMsg

# xDevSM modules
from rc.rc_control_base import RCControlBase
from sm_framework.py_oran.rc import RCFunctionDef as funcdef
from sm_framework.py_oran.rc import RCControlReq as ctrlReq

class RadioBearerControl(RCControlBase):
    """
    Radio Bearer Control Xapp
    """
    
    def __init__(self, address, drb_id, qos_flow_id, qos_flow_mapping_indication):
        super().__init__(address, entrypoint=None)
        self.drb_id = drb_id
        self.qos_flow_id = qos_flow_id
        self.qos_flow_mapping_indication = qos_flow_mapping_indication

    
    def set_drb_id(self, drb_id):
        self.drb_id = drb_id
    
    def set_qos_flow_id(self, qos_flow_id):
        self.qos_flow_id = qos_flow_id
    
    def set_qos_flow_mapping_indication(self, qos_flow_mapping_indication):
        self.qos_flow_mapping_indication = qos_flow_mapping_indication
    

    def generate_send_control_request(self, e2_node_id, ran_func_dsc: funcdef.RCFuncDef, ue_id=None):
        if ue_id is None:
            self.logger.info("[warn] using mock ue_id")
            ue_id = self.get_mock_ue_id()
            # ue_id = self.get_mock_du_ue_id()
        
        if not ran_func_dsc.ctrl:
            # TODO Add error message
            return
        ctrl_descr = ran_func_dsc.ctrl.contents 
        style = None
        style = next(
        (
            s for s in ctrl_descr.seq_ctrl_style[:ctrl_descr.sz_seq_ctrl_style]
            if bytes(np.ctypeslib.as_array(s.name.buf, shape=(s.name.len,))).decode('utf-8') == "Radio Bearer Control"),None
        )
        
        if style is None:
            self.logger.error("Radio Bearer Control style not supported in {}".format(e2_node_id))
            return

        self.logger.info("Radio Bearer supported generating message")

        self.wrapper.generate_radio_bearer_control_msg(style=style,ue_id=ue_id, 
                                                        drb_id=self.drb_id, 
                                                        qos_flow_id=self.qos_flow_id, 
                                                        qos_flow_mapping_indication=self.qos_flow_mapping_indication)
        self.wrapper.print_ctrl_req()

        rc_ctrl_req_enc = self.wrapper.encode()
        
        hdr_byte_array = rc_ctrl_req_enc.hdr_encoded.to_bytes()
        ctrl_msg_byte_array = rc_ctrl_req_enc.msg_encoded.to_bytes()

        self.logger.info("hdr encoded: {}".format(hdr_byte_array))
        self.logger.info("ctrl encoded: {}".format(ctrl_msg_byte_array))
        self.send_control_request_rmr(e2_node_id=e2_node_id,
                                      control_header=hdr_byte_array,
                                      control_message=ctrl_msg_byte_array)

        