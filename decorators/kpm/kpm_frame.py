import json
from typing import Tuple

from decorators.base import BaseXDevSMWrapper

# osc xappframe
from ricxappframe.xapp_frame import rmr
from ricxappframe.subsclient.models.event_trigger_definition import EventTriggerDefinition
from ricxappframe.e2ap.asn1 import IndicationMsg
import ricxappframe.xapp_rest as ricrest

# utility
import utils.xapp_sub as subscribe
from utils.constants import Values
import utils.utility as utility

# sm framework
import sm_framework.py_oran.kpm.function_definition_builder as function_definition_builder
import sm_framework.py_oran.kpm.KpmIndicationHdr as KpmIndicationHdr
import sm_framework.py_oran.kpm.KpmIndicationMsg as KpmIndicationMsg
import sm_framework.py_oran.kpm.KpmFunctionDef as KpmFunctionDef
from sm_framework.py_oran.kpm.enums import ue_id_e2sm_e

class XappKpmFrame(BaseXDevSMWrapper):

    def __init__(self, xapp_handler, logger, server, xapp_name, rmr_port, http_port, pltnamespace, app_namespace):
        super().__init__(xapp_handler, logger, server)
        self.xapp_name = xapp_name
        self.pltnamespace = pltnamespace
        self.app_namespace = app_namespace
        self.rmr_port = rmr_port
        self.http_port = http_port

        self.subscription_id = {}
        self.kpm_func_def_wrapper = KpmFunctionDef.KpmFuncDefArrWrapper(hex="")

        # callbacks
        self.__ind_msg_callback = None
        self.__sub_failed_callback = None
        
        # Subscription info - indication
        self.uri_subscriptions = Values.GENERAL_PATH.format(self.pltnamespace, Values.SUBSCRIPTION_SERVICE, self.pltnamespace, Values.SUBSCRIPTION_PORT) + "/ric/v1/subscriptions"
        self.subscriber = subscribe.NewSubscriber(uri=self.uri_subscriptions, rmr_port=self.rmr_port)

    def handle(self, xapp, summary, sbuf):

        xapp.logger.debug("[XappKpmFrame] received: {}".format(summary))

        if summary[rmr.RMR_MS_MSG_TYPE] == Values.RIC_INDICATION:
            self._handle_indication(xapp, summary) # FIXME maybe better with a private method 
        elif summary[rmr.RMR_MS_MSG_TYPE] == Values.RIC_ERROR_INDICATION:
            xapp.logger.error("[XappKpmFrame] Error in indication message")
        else:
            xapp.logger.debug("[XappKpmFrame] not recognized kpm message type: {}".format(summary[rmr.RMR_MS_MSG_TYPE]))
        
        self._xapp_handler.handle(xapp, summary, sbuf)
        # xapp.rmr_free(sbuf)


    def get_ran_function_description(self, json_ran_info):
        """
        Get decoded ran function description
        Parameters:
        ----------
        json_ran_info (json obj): json object obtained when by the get_ran_info function

        """
        if not json_ran_info:
            return

        for ran_func in json_ran_info["gnb"]["ranFunctions"]: 
            if ran_func["ranFunctionId"] == 2:
                # selecting kpm action
                ran_function_definition = ran_func["ranFunctionDefinition"]
                break
        # Decoding RAN function Definition
        self.kpm_func_def_wrapper.set_hex(hex=ran_function_definition)
        
        func_def_obj = self.kpm_func_def_wrapper.decode()
        return func_def_obj

    def send(self, *args, **kwargs):
        """
        Send a message using the xapp's send method.
        """
        self.xapp.send(*args, **kwargs)
    
    def _handle_indication(self, xapp, summary):
        """
        Base handler for indication messages.
        """    
        indm = IndicationMsg()

        # decoding E2AP
        indm.decode(summary[rmr.RMR_MS_PAYLOAD])

        ba_ind_header = utility.get_c_byte_array_from_py_byte_string(indm.indication_header)
        ba_ind_msg = utility.get_c_byte_array_from_py_byte_string(indm.indication_message)
        
        if ba_ind_header is None:
            # information not decoded correctly
            return
        
        if ba_ind_msg is None:
            # information not decoded correctly
            return
        
        
        # Indication hdr - decoding E2SM
        ind_hdr_mgr = KpmIndicationHdr.KpmIndHdrWrapper(ba_ind_header)
        decoded_ind_hdr = ind_hdr_mgr.decode()
        if decoded_ind_hdr is None:
            xapp.logger.info("[XappKpmFrame] indication header not decoded correctly")
            return
        xapp.logger.debug("[XappKpmFrame]indication header encoded: {}, indication header encoded ba: {}, indication header format decoded: {}".format(
            indm.indication_header, ba_ind_header, decoded_ind_hdr.type.value
        ))

        # Indication msg - decoding E2SM
        ind_msg_mgr = KpmIndicationMsg.KpmIndMsgWrapper(ba_ind_msg)
        decoded_ind_msg = ind_msg_mgr.decode()

        if self.__ind_msg_callback is None:
            xapp.logger.info("[XappKpmFrame] No indication message callback registered - printing default information")
            xapp.logger.debug("[XappKpmFrame] indication header encoded: {}, indication header encoded ba: {}, indication header format decoded: {}".format(
                indm.indication_header, ba_ind_header, decoded_ind_hdr.type.value
            ))
            decoded_ind_msg.print_meas_info(xapp.logger)
        else:
            self.__ind_msg_callback(decoded_ind_hdr, decoded_ind_msg, summary['meid'])

    # External APIs
    def register_ind_msg_callback(self, handler):
        """
        This method registers the function to be called when received an indication message
        --------
        The handler has two parameters:
        
        decoded_ind_hdr
        
        decoded_ind_msg
        """
        self.__ind_msg_callback = handler
    
    def register_sub_fail_callback(self, handler):
        """
        This method registers the function to be called when received an indication message
        --------
        The handler has one parameter:
        json reponse
        """
        self.__sub_failed_callback = handler
    
    def remove_sub_id(self, sub_id: str):
        to_remove = None
        for key in self.subscription_id.keys():
            if self.subscription_id[key] == sub_id:
                to_remove = key
                break
        
        if to_remove is None:
            #xapp.logger.error("[XappKpmFrame] subscription id not found")
            print("[XappKpmFrame] subscription id not found")
            return
        else:
            del self.subscription_id[to_remove]
    

    def subscribe(self, gnb, ev_trigger: Tuple[int, float], func_def: dict, action_type=Values.ACTION_TYPE, ran_period_ms=1000, sst=1, sd=0):

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
            return
        subscription_detail = self.subscriber.SubscriptionDetail(event_triggers=encoded_ev_trig.byte_array_to_tuple(),
                                                                  action_to_be_setup_list=actions,
                                                                  xapp_event_instance_id=12345)
        client_endpoint = self.subscriber.SubscriptionParamsClientEndpoint(host="service-{}-{}-http.{}".format(self.app_namespace, self.xapp_name, self.app_namespace), # make it as a parameter 
                                                                       http_port=self.http_port, 
                                                                       rmr_port=self.rmr_port)
        subsDirective = self.subscriber.SubscriptionParamsE2SubscriptionDirectives(2, 2, True)
        

        
        self.logger.info("[XappKpmFrame] POST request for subscription to {}".format(self.uri_subscriptions))
        subscription_params = self.subscriber.SubscriptionParams(subscription_id=None,
                                        client_endpoint=client_endpoint,
                                        meid=gnb.inventory_name,                          
                                        ran_function_id=2,
                                        e2_subscription_directives=subsDirective,
                                        subscription_details=[subscription_detail])
        self.logger.info(subscription_params)
        data, reason, status = self.subscriber.Subscribe(subs_params=subscription_params)
        response_json = json.loads(data)
        self.logger.info("[XappKpmFrame] reason:{}".format(reason))
        self.logger.info("[XappKpmFrame] subscription reponse {}".format(response_json))
        self.subscription_id[gnb.inventory_name] = response_json["SubscriptionId"]
        self.logger.info("[XappKpmFrame] Got the subscription reponse, my subscription id for gnb {} is: {}".format(gnb.inventory_name, self.subscription_id))

        return status

    def subs_response_cb(self, name, path, data, ctype):
        response = ricrest.initResponse()
        response['payload'] = ("{}")
        response_json = json.loads(data)
        self.logger.info(response_json)
        if len(response_json["SubscriptionInstances"][0]["ErrorCause"]) > 0 and response_json["SubscriptionInstances"][0]["ErrorCause"] != " ":
            self.logger.info("Error for subscription: {} removing it from the pool reasons: {}".format(response_json['SubscriptionId'], response_json["SubscriptionInstances"][0]["ErrorCause"]))
            self._remove_sub_id(response_json['SubscriptionId'])
            if not self.__sub_failed_callback is None:
                self.__sub_failed_callback(response_json)
        else:
            self.logger.info("called response handler subscription successfull! Response: {}".format(response_json))
            response['payload'] = json.dumps(response_json)
       
        return response
    
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
        self.logger.info("[XappKpmFrame] Received termination signal")
        if self.subscription_id is None:
            self.logger.info("[XappKpmFrame] Not subscribed - terminating...")
        else:
            for key in self.subscription_id.keys():
                self.logger.info("[XappKpmFrame] Unsubscribing from gnb: {}, subid: {}, DELETE {}".format(key, self.subscription_id[key], self.uri_subscriptions))
        self._xapp_handler.terminate(signum, frame)


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

    def _remove_sub_id(self, sub_id: str):
        to_remove = None
        for key in self.subscription_id.keys():
            if self.subscription_id[key] == sub_id:
                to_remove = key
                break
        
        if to_remove is None:
            self.logger.error("subscription id not found")
        else:
            del self.subscription_id[to_remove]