# import base decorator
from decorators.rc.rc_control_base import RCControlBase

class RadioBearerControl(RCControlBase):
    """
    Radio Bearer Control Decorator
    """
    def __init__(self, 
                 xapp_handler, 
                 logger, 
                 server, 
                 xapp_name, 
                 rmr_port,
                 mrc, 
                 http_port, 
                 pltnamespace, 
                 app_namespace,
                 # control parameters
                 drb_id, 
                 qos_flow_id, 
                 qos_flow_mapping_indication):
        super().__init__(xapp_handler, logger, server, xapp_name, rmr_port,mrc, http_port, pltnamespace, app_namespace)
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
    
    def generate_control_request(self, ue_id=None, control_action_id=1):

        if control_action_id == 2: # QoS flow mapping configuration
            self.wrapper.generate_radio_bearer_control_msg(style=self.style,
                                                        ue_id=ue_id, 
                                                            drb_id=self.drb_id, 
                                                            qos_flow_id=self.qos_flow_id, 
                                                            qos_flow_mapping_indication=self.qos_flow_mapping_indication)
        else:
            self.logger.error("[RadioBearerControl] xDevSM does not support control action ID: {}".format(control_action_id))

    def logic(self):
        self.run(thread=True)
        pass