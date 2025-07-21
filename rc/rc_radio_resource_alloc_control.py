from rc.rc_control_base import RCControlBase

from sm_framework.py_oran.rc import RCFunctionDef as funcdef


class RadioResourceAllocationControl(RCControlBase):
    """
    Radio Resource Allocation Control Xapp
    """
    
    def __init__(self, address, plmn_identity, sst, sd, min_prb_policy_ratio, max_prb_policy_ratio, dedicated_prb_policy_ratio):
        super().__init__(address, entrypoint=None)
        self.service_style_name = "Radio Resource Allocation Control"
        self.plmn_identity = plmn_identity
        self.sst = sst
        self.sd = sd
        self.min_prb_policy_ratio = min_prb_policy_ratio
        self.max_prb_policy_ratio = max_prb_policy_ratio
        self.dedicated_prb_policy_ratio = dedicated_prb_policy_ratio

    def set_plmn_identity(self, plmn_identity):
        self.plmn_identity = plmn_identity
    
    def set_sst(self, sst):
        self.sst = sst
    
    def set_sd(self, sd):
        self.sd = sd
    
    def set_min_prb_policy_ratio(self, min_prb_policy_ratio):
        self.min_prb_policy_ratio = min_prb_policy_ratio
    
    def set_max_prb_policy_ratio(self, max_prb_policy_ratio):
        self.max_prb_policy_ratio = max_prb_policy_ratio
    
    def set_dedicated_prb_policy_ratio(self, dedicated_prb_policy_ratio):
        self.dedicated_prb_policy_ratio = dedicated_prb_policy_ratio

    def generate_control_request(self, ue_id, control_action_id=6):

        if control_action_id == 6: # Slice-level PRB quota
            self.wrapper.generate_radio_resource_allocation_control_frmt_1(self.style,
                                                                        ue_id=ue_id,
                                                                        plmn_identity=self.plmn_identity,
                                                                        sst=self.sst,
                                                                        sd=self.sd,
                                                                        min_prb=self.min_prb_policy_ratio,
                                                                        max_prb=self.max_prb_policy_ratio,
                                                                        dedicated_prb=self.dedicated_prb_policy_ratio)
        else:
            self.logger.error("xDevSM does not support control action ID: {}".format(control_action_id))


    def logic(self):
        self.run(thread=True)
        pass