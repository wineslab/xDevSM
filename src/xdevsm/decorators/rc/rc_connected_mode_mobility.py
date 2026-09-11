from xdevsm.decorators.control import xAppControlService
import xdevsm.sm_framework.py_oran.rc.RCFunctionDef as funcdef
import xdevsm.sm_framework.py_oran.rc.RCControlReq as ctrlReq


class ConnectedModeMobilityControl(xAppControlService):
    """
    Connected Mode Mobility Control Decorator
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
                 plmn_identity,
                 nr_cell_id=None,
                 ue_id_type=None,
                 ue_id=None):

        super().__init__(xapp_handler, logger, server, xapp_name, rmr_port, http_port, mrc, pltnamespace, app_namespace, ue_id_type, ue_id)
        self.service_style_name = "Connected mode mobility control"
        self.function_id = 3
        self.plmn_identity = plmn_identity
        self.nr_cell_id = nr_cell_id

        self.function_def_wrapper = funcdef.RCFuncDefWrapper(hex="")
        self.service_model_wrapper = ctrlReq.RCControlReqWrapper()

    
    def set_plmn_identity(self, plmn_identity):
        self.plmn_identity = plmn_identity
    
    def set_nr_cell_id(self, nr_cell_id):
        self.nr_cell_id = nr_cell_id

    def generate_control_request(self, ue_id_struct=None, control_action_id=1):
        if ue_id_struct is None:
            if not self.ue_id_type:
                self.logger.info("[ConnectedModeMobilityControl] using mock ue_id")
                ue_id_struct = self.get_mock_ue_id(ran_ue_id=self.ue_id)
            else:
                self.logger.info("[ConnectedModeMobilityControl] using mock du_ue_id")
                ue_id_struct = self.get_mock_du_ue_id(ran_ue_id=self.ue_id)

        if control_action_id == 1:  # Handover Control
            self.service_model_wrapper.generate_connected_mode_mobility_control_frmt_1(self.style,
                                                                         ue_id=ue_id_struct, 
                                                                         plmn_identity=self.plmn_identity, 
                                                                         nr_cell_id=self.nr_cell_id)
        else:
            self.logger.error("[RCConnectedModeMobilityControl] xDevSM does not support control action ID: {}".format(control_action_id))