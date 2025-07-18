from rc.rc_control_base import RCControlBase

from sm_framework.py_oran.rc import RCFunctionDef as funcdef


class RadioResourceAllocationControl(RCControlBase):
    """
    Radio Resource Allocation Control Xapp
    """
    
    def __init__(self, address, ):
        super().__init__(address, entrypoint=None)
        self.service_style_name = "Radio Resource Allocation Control"

    def generate_control_request(self, ue_id):
        # self.wrapper.generate_radio_resource_allocation_control_frmt_1()
        pass


    def logic(self):
        self.run(thread=True)
        pass