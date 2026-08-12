import json
from typing import Tuple

from xdevsm.decorators.base import BaseXDevSMWrapper

# osc xappframe
from ricxappframe.xapp_frame import rmr
from ricxappframe.subsclient.models.event_trigger_definition import EventTriggerDefinition
from ricxappframe.e2ap.asn1 import IndicationMsg
import ricxappframe.xapp_rest as ricrest

# xDevSM decorators
from xdevsm.decorators.report import xAppReportService

# utility
import xdevsm.utils.xapp_sub as subscribe
from xdevsm.utils.constants import Values
import xdevsm.utils.utility as utility

# sm framework
import xdevsm.sm_framework.py_oran.kpm.function_definition_builder as function_definition_builder
import xdevsm.sm_framework.py_oran.kpm.KpmIndicationHdr as KpmIndicationHdr
import xdevsm.sm_framework.py_oran.kpm.KpmIndicationMsg as KpmIndicationMsg
import xdevsm.sm_framework.py_oran.kpm.KpmFunctionDef as KpmFunctionDef
from xdevsm.sm_framework.py_oran.kpm.enums import ue_id_e2sm_e

class XappKpmFrame(xAppReportService):
    """
    KPM Report decorator class
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

        self.sm_func_wrapper = KpmFunctionDef.KpmFuncDefArrWrapper(hex="")

        self.function_id = 2  # KPM function ID

    def handle(self, xapp, summary, sbuf):
        xapp.logger.debug("[XappKpmFrame] received: {}".format(summary))
        if summary[rmr.RMR_MS_MSG_TYPE] == Values.RIC_INDICATION:
            self._handle_indication(xapp, summary)
        elif summary[rmr.RMR_MS_MSG_TYPE] == Values.RIC_ERROR_INDICATION:
            xapp.logger.error("[XappKpmFrame] Error in indication message")
        else:
            xapp.logger.debug("[XappKpmFrame] not recognized kpm message type: {}".format(summary[rmr.RMR_MS_MSG_TYPE]))
        self._xapp_handler.handle(xapp, summary, sbuf)


    
    def decode_message(self, function_id, ba_ind_header, ba_ind_msg, meid, sub_id):

        # Indication hdr - decoding E2SM
        self.logger.info("[XappKpmFrame] E2AP Decoded function id: {}".format(function_id))
        if function_id != self.function_id:
            self.logger.info("[XappKpmFrame] received indication for different function id: {}".format(function_id))
            return
        
        ind_hdr_mgr = KpmIndicationHdr.KpmIndHdrWrapper(ba_ind_header)
        decoded_ind_hdr = ind_hdr_mgr.decode()

        if decoded_ind_hdr is None:
            self.logger.error("[XappKpmFrame] Decoded indication header is None")
            return

        # Indication msg - decoding E2SM
        ind_msg_mgr = KpmIndicationMsg.KpmIndMsgWrapper(ba_ind_msg)
        decoded_ind_msg = ind_msg_mgr.decode()
        self.logger.info("[XappKpmFrame] Indication message decoded successfully")

        ind_msg_callback = self.get_indication_msg_callback()
        if ind_msg_callback is None:
            self.logger.info("[XappKpmFrame] No indication message callback registered - printing default information")
            self.logger.debug("[XappKpmFrame] indication header encoded ba: {}, indication header format decoded: {}".format(
                ba_ind_header, decoded_ind_hdr.type.value
            ))
            decoded_ind_msg.print_meas_info(self.logger)
        else:
            ind_msg_callback(decoded_ind_hdr, decoded_ind_msg, meid, sub_id)
    

    def subscribe(self, gnb, ev_trigger: Tuple[int, float], func_def: dict, action_type=Values.ACTION_TYPE, ran_period_ms=1000, sst=1, sd=0):
        """
        This method sends a subscription request to the RIC for the given gnb
        returns sub_id 
        the sub_id is what callers need to correlate later indications with this specific subscription.
        """

        self.logger.info("[XappKpmFrame] Preparing subscription for gnb: {}".format(gnb.inventory_name))
        

        if self.subscriber.ResponseHandler(self.subs_response_cb, self.server) is not True:
            self.logger.error("Error when trying to set the subscription reponse callback")

        # encoding event trigger
        encoded_ev_trig = function_definition_builder.ev_trigger_encoder(period_ev_trig=ev_trigger[1])

        self.logger.info("[XappKpmFrame] event trigger encoded: {}".format(encoded_ev_trig.byte_array_to_tuple()))
        
        actions = []
        # encoding action defintion
        encoded_actions_def = function_definition_builder.action_encoder(action_def_dict=func_def, gran_period_ms=ran_period_ms, sst=sst, sd=sd)

        for index, key in enumerate(encoded_actions_def.keys()):
            value = encoded_actions_def[key].byte_array_to_tuple()
            self.logger.info("[XappKpmFrame] actions encoded: {}".format(value))

            action = self.subscriber.ActionToBeSetup(action_id=1,
                                                    action_type=action_type,
                                                    action_definition=value,
                                                    subsequent_action=self.subscriber.SubsequentAction(subsequent_action_type="continue", time_to_wait="w5ms"))
            actions.append(action)
        
        if len(actions) == 0:
            self.logger.info("[XappKpmFrame] No action built!")
            return None

        result = self.send_subscription(gnb, encoded_ev_trig, actions)
        if result is None:
            return None
        # send_subscription returns (status, sub_id); the sub_id is what callers
        # need to correlate later indications with this specific subscription.
        _, sub_id = result
        return sub_id
    
    def get_ue_id(self, ue_meas_report: KpmIndicationMsg.ue_id_e2sm_t) -> int:
        if ue_meas_report.type.value == ue_id_e2sm_e.GNB_UE_ID_E2SM:
            gnb_mono = ue_meas_report.union.gnb
            if gnb_mono.ran_ue_id: 
                return gnb_mono.ran_ue_id.contents.value
        elif ue_meas_report.type.value == ue_id_e2sm_e.GNB_DU_UE_ID_E2SM:
            gnb_du = ue_meas_report.union.gnb_du
            if gnb_du.ran_ue_id:
                return gnb_du.ran_ue_id.contents.value
            else:
                return gnb_du.gnb_cu_ue_f1ap
        elif ue_meas_report.type.value == ue_id_e2sm_e.GNB_CU_UP_UE_ID_E2SM:
            gnb_cu = ue_meas_report.union.gnb_cu_up
            if gnb_cu.ran_ue_id:
                return gnb_cu.ran_ue_id.contents.value
            else:
                return gnb_cu.gnb_cu_cp_ue_e1ap
        else:
            self.logger.error("[XappKpmFrame] format not supported ({})".format(ue_meas_report.type.value))


    def terminate(self, signum, frame):
        # Per-service-model teardown hook. The base xAppReportService already
        # unsubscribes this frame's subscriptions and delegates termination down
        # the chain; override here if KPM ever needs extra cleanup.
        super().terminate(signum, frame)

    def get_subscription_id(self, inventory_name: str):
        """
        Parameters:
        ----------
        inventory_name (str): gnb inventory name

        Returns:
        ----------
        subscription id for that gnb
        """
        return self.subscription_id[inventory_name]

