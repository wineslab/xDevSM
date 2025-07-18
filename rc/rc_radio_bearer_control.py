import numpy as np


# xDevSM modules
from rc.rc_control_base import RCControlBase
from sm_framework.py_oran.rc import RCFunctionDef as funcdef

class RadioBearerControl(RCControlBase):
    """
    Radio Bearer Control Xapp
    """
    
    def __init__(self, address, drb_id, qos_flow_id, qos_flow_mapping_indication):
        super().__init__(address, entrypoint=None)
        self.service_style_name = "Radio Bearer Control"
        self.drb_id = drb_id
        self.qos_flow_id = qos_flow_id
        self.qos_flow_mapping_indication = qos_flow_mapping_indication

    
    def set_drb_id(self, drb_id):
        self.drb_id = drb_id
    
    def set_qos_flow_id(self, qos_flow_id):
        self.qos_flow_id = qos_flow_id
    
    def set_qos_flow_mapping_indication(self, qos_flow_mapping_indication):
        self.qos_flow_mapping_indication = qos_flow_mapping_indication
    
    def generate_control_request(self, ue_id=None):
        self.wrapper.generate_radio_bearer_control_msg(style=self.style,
                                                       ue_id=ue_id, 
                                                        drb_id=self.drb_id, 
                                                        qos_flow_id=self.qos_flow_id, 
                                                        qos_flow_mapping_indication=self.qos_flow_mapping_indication)
        
    def logic(self):
        self.run(thread=True)
        pass