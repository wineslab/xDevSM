from rc.rc_control_base import RCControlBase


class ConnectedModeMobilityControl(RCControlBase):
    """
    Connected Mode Mobility Control Xapp
    """

    def __init__(self, address, plmn_identity, nr_cell_id=None):
        
        super().__init__(address, entrypoint=None)
        self.service_style_name = "Connected mode mobility control"
        self.plmn_identity = plmn_identity
        self.nr_cell_id = nr_cell_id

    
    def set_plmn_identity(self, plmn_identity):
        self.plmn_identity = plmn_identity
    
    def set_nr_cell_id(self, nr_cell_id):
        self.nr_cell_id = nr_cell_id

    def generate_control_request(self, ue_id, control_action_id=1):
        if control_action_id == 1:  # Handover Control
            self.wrapper.generate_connected_mode_mobility_control_frmt_1(self.style, 
                                                                         ue_id=ue_id, 
                                                                         plmn_identity=self.plmn_identity, 
                                                                         nr_cell_id=self.nr_cell_id)
        else:
            self.logger.error("xDevSM does not support control action ID: {}".format(control_action_id))