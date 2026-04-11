import json

# osc xappframe
from ricxappframe.xapp_frame import rmr
from ricxappframe.e2ap.asn1 import IndicationMsg
import ricxappframe.xapp_rest as ricrest

# utility
import utils.xapp_sub as subscribe
from utils.constants import Values
import utils.utility as utility


# xDevSM decorators
from decorators.report import xAppReportService

# xDevSM sm framework
from sm_framework.py_oran.ByteArray import ByteArray
import sm_framework.py_oran.dapp.report.DAppIndicationHdr as DAppIndicationHdr
import sm_framework.py_oran.dapp.report.DAppIndicationMsg as DAppIndicationMsg
import sm_framework.py_oran.dapp.e3.DAppE3IndPayload as DAppE3IndPayload
import sm_framework.py_oran.dapp.report.DAppActionDef as DAppActionDef
import sm_framework.py_oran.dapp.report.DAppEvTrigger as DAppEvTrigger
import sm_framework.py_oran.dapp.report.DAppFunctionDef as dappfuncdef



class DAppReport(xAppReportService):
    """
    DApp Report decorator class
    """
    def __init__(self,
                xapp_handler,
                logger,
                server,
                xapp_name,
                rmr_port,
                http_port,
                pltnamespace,
                app_namespace):
        super().__init__(xapp_handler, logger, server, xapp_name, rmr_port, http_port, pltnamespace, app_namespace)
        
        # TODO do we have specific parameters for report decorator?
        self.sm_func_wrapper = dappfuncdef.DAppFunctionDefWrapper(hex="")
        self.function_id = 255  # DApp function ID
        
    
    
    def handle(self, xapp, summary, sbuf):
        xapp.logger.info("[DAppReport] received: {}".format(summary))
        if summary[rmr.RMR_MS_MSG_TYPE] == Values.RIC_INDICATION:
            xapp.logger.info("[DAppReport] Handling DApp Report Request message")
            self._handle_indication(xapp, summary)
        elif summary[rmr.RMR_MS_MSG_TYPE] == Values.RIC_ERROR_INDICATION:
            xapp.logger.info("[DAppReport] Error in Indication message")
        self._xapp_handler.handle(xapp, summary, sbuf)
    
    
    def decode_message(self, function_id, ba_ind_header, ba_ind_msg, meid):
        """
        decode DApp Report indication message
        """
        self.logger.info("[DAppReport] E2AP Decoded function id: {}".format(function_id))
        if function_id != self.function_id:
            self.logger.info("[DAppReport] received indication for different function id: {}".format(function_id))
            return
        
        # Decoding DApp Indication Header
        dapp_ind_hdr_wrapper = DAppIndicationHdr.DAppIndHdrWrapper(byte_array=ba_ind_header)
        dapp_ind_hdr = dapp_ind_hdr_wrapper.decode()


        if dapp_ind_hdr is None or dapp_ind_hdr.format.value != DAppIndicationHdr.e2sm_dapp_ind_hdr_format_e.FORMAT_0_E2SM_DAPP_IND_HDR:
            self.logger.error("[DAppReport] Decoded DApp Indication Header is None, skipping processing")
            return

        self.logger.info("[DAppReport] Decoded DApp Indication Header: ran_function_id={}, dapp_id={}".format(dapp_ind_hdr.union.frmt_0.ran_function_id,dapp_ind_hdr.union.frmt_0.dapp_id))

        # Decoding DApp Indication Message
        dapp_ind_msg_wrapper = DAppIndicationMsg.DAppIndicationMsgWrapper(byte_array=ba_ind_msg)
        dapp_ind_msg = dapp_ind_msg_wrapper.decode()
        self.logger.info("[DAppReport] Decoded DApp Indication Message: decoded")

        if dapp_ind_msg.format.value != DAppIndicationMsg.e2sm_dapp_ind_msg_format_e.FORMAT_1_E2SM_DAPP_IND_MSG and dapp_ind_msg.format.value != DAppIndicationMsg.e2sm_dapp_ind_msg_format_e.FORMAT_2_E2SM_DAPP_IND_MSG:
            self.logger.error("[DAppReport] DApp Indication Message format not supported")
            return


        # Decoding DApp E3 Indication Payload based on format 1 <- this now should be done outside
        # prb_blocked = dapp_ind_msg_wrapper.get_data_format_1()
        # dapp_e3_ind_payload_wrapper = DAppE3IndPayload.DAppE3IndPayloadWrapper(ran_func_id=dapp_ind_hdr.union.frmt_0.ran_function_id, byte_array=prb_blocked)
        # dapp_e3_ind_payload_wrapper.decode()
        # self.logger.info("[DAppReport] Decoded DApp E3 Indication Payload: decoded")
        
       
        ind_msg_callback = self.get_indication_msg_callback()
        if ind_msg_callback is not None:
            ind_msg_callback(dapp_ind_hdr, dapp_ind_msg, meid)
        else:
            self.logger.warning("[DAppReport] No indication message callback registered, skipping processing")

    
    def subscribe(self, gnb, ev_trigger: DAppEvTrigger.DAppEvTrigger=None, action_def: DAppActionDef.DAppActionDef=None):
        """
        This method sends a subscription request to the RIC for the given gnb
        Parameters:
        ----------
        gnb: Gnb object
            The gnb to which send the subscription
        ev_trigger: DAppEvTrigger object
            The event trigger definition
        action_def: DAppFunctionDef object
            The action definition
        """
        
        if ev_trigger is None:
            self.logger.info("[DAppReport] Event trigger is None build a default one")
            ev_trigger = DAppEvTrigger.DAppEvTriggerWrapper()
            ev_trigger.create_dummy_ev_trigger()
        
        if action_def is None:
            self.logger.info("[DAppReport] Action definition is None build a default one")
            action_def = DAppActionDef.DAppActionDefWrapper()
            action_def.create_dummy_action_def()

        # encoding event trigger
        ev_trigger_enc = ev_trigger.encode()
        self.logger.info("[DAppReport] Event trigger encoded: {}".format(ev_trigger_enc.byte_array_to_tuple()))
        
        # encoding action definition
        action_def_enc: ByteArray = action_def.encode()
        self.logger.info("[DAppReport] Action definition encoded: {}".format(action_def_enc.byte_array_to_tuple()))
        
        # Create Action to be setup list
        action = self.subscriber.ActionToBeSetup(action_id=1,
                                                    action_type="report",
                                                    action_definition=action_def_enc.byte_array_to_tuple(),
                                                    subsequent_action=self.subscriber.SubsequentAction(subsequent_action_type="continue", time_to_wait="w5ms"))

        # sending subscription
        self.send_subscription(gnb, ev_trigger_enc, [action])

    

    

    def terminate(self, signum, frame):
        self.logger.info("[DAppReport] Terminating xApp")
        self._xapp_handler.terminate(signum, frame)