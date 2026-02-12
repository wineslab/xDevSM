# xDevSM decorators
from decorators.control import xAppControlService

# xDevSM sm framework
from sm_framework.py_oran.ByteArray import ByteArray
from sm_framework.py_oran.dapp.control.DAppControlReq import DAppControlReqWrapper 
from sm_framework.py_oran.dapp.e3.DAppE3CtrlPayload import DAppE3CtrlPayloadWrapper
import sm_framework.py_oran.dapp.report.DAppFunctionDef as dappfuncdef
from xDevSM.sm_framework.py_oran.dapp.enums import dapp_e3_sm_type_e

class DAppPrbMaskControl(xAppControlService):
    """
    DApp Control decorator class
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
                # Control parameters
                dapp_id=None,
                prbs_to_block=None
                ):
        super().__init__(xapp_handler, logger, server, xapp_name, rmr_port, http_port, mrc, pltnamespace, app_namespace)

        # SM Parameters
        self.function_id = 255  # DApp function ID
        self.ran_function_id = 1 # DApp E3 function ID
        self.style = 1
        self.service_style_name = "DAPP-CONTROL-STYLE-1"

        # Setting enc/dec wrappers
        self.function_def_wrapper = dappfuncdef.DAppFunctionDefWrapper(hex="")
        self.service_model_wrapper = DAppControlReqWrapper()

        # Control parameters
        self.dapp_id = dapp_id
        self.prbs_to_block = prbs_to_block
        self.payload_enc = None
        if self.prbs_to_block is not None:
            self.set_payload(self.prbs_to_block)

    def set_dapp_id(self, dapp_id: int):
        self.dapp_id = dapp_id
    
    def set_payload(self, prbs_to_block: list):
        if(len(prbs_to_block) == 0):
            self.logger.error("[DAppPrbMaskControl] No PRBs to block, control message will be generated with empty PRB list")
            return
        self.prb_to_block = prbs_to_block
        payload = DAppE3CtrlPayloadWrapper(dapp_e3_sm_type_e.DAPP_E3_SM_SPECTRUM)
        payload.set_spectrum_control(self.prb_to_block)
        self.payload_enc = payload.encode()

    def handle(self, xapp, summary, sbuf):
        # handle should be done based on the control message type, not supported for dApps
        super().handle(xapp, summary, sbuf)
    

    def generate_control_request(self, control_action_id=1):
        # TODO do we need any check on the action id?
        self.service_model_wrapper.generate_control_req_frmt_0(ran_function_id=self.ran_function_id,
                                                               dapp_id=self.dapp_id,
                                                               payload=self.payload_enc)