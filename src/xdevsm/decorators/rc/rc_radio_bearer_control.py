# import base decorator
from xdevsm.decorators.control import xAppControlService
import xdevsm.sm_framework.py_oran.rc.RCFunctionDef as funcdef
import xdevsm.sm_framework.py_oran.rc.RCControlReq as ctrlReq

class RadioBearerControl(xAppControlService):
    """
    Radio Bearer Control Decorator
    """
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
                 # control parameters
                 drb_id,
                 qos_flow_id,
                 qos_flow_mapping_indication,
                 ue_id_type=None,
                 ue_id=None):
        super().__init__(xapp_handler, logger, server, xapp_name, rmr_port, http_port, mrc, pltnamespace, app_namespace, ue_id_type, ue_id)
        self.service_style_name = "Radio Bearer Control"
        # Fixed for RC Service Model
        self.function_id = 3

        self.drb_id = drb_id
        self.qos_flow_id = qos_flow_id
        self.qos_flow_mapping_indication = qos_flow_mapping_indication

        # Setting enc/dec wrappers - These are actually part of the RC Service Model
        # Maybe it could be generalized
        self.function_def_wrapper = funcdef.RCFuncDefWrapper(hex="")
        self.service_model_wrapper = ctrlReq.RCControlReqWrapper()

    
    def set_drb_id(self, drb_id):
        self.drb_id = drb_id
    
    def set_qos_flow_id(self, qos_flow_id):
        self.qos_flow_id = qos_flow_id
    
    def set_qos_flow_mapping_indication(self, qos_flow_mapping_indication):
        self.qos_flow_mapping_indication = qos_flow_mapping_indication
    
    # def set_ue_id(self, ue_id_type, ue_id):
    #     self.ue_id_type = ue_id_type
    #     self.ue_id = ue_id

    def generate_control_request(self, ue_id_struct=None,control_action_id=1):
        if ue_id_struct is None:
            if not self.ue_id_type:
                self.logger.info("[RCRadioBearerControl] using mock ue_id")
                ue_id_struct = self.get_mock_ue_id(ran_ue_id=self.ue_id)
            else:
                self.logger.info("[RCRadioBearerControl] using mock du_ue_id")
                ue_id_struct = self.get_mock_du_ue_id(ran_ue_id=self.ue_id)

        if control_action_id == 2: # QoS flow mapping configuration
            self.service_model_wrapper.generate_radio_bearer_control_msg(style=self.style,
                                                                        ue_id=ue_id_struct, 
                                                                        drb_id=self.drb_id, 
                                                                        qos_flow_id=self.qos_flow_id, 
                                                                        qos_flow_mapping_indication=self.qos_flow_mapping_indication)
        else:
            self.logger.error("[RadioBearerControl] xDevSM does not support control action ID: {}".format(control_action_id))

    def logic(self):
        self.run(thread=True)
        pass