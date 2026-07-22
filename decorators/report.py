from abc import abstractmethod
from typing import Tuple
import json

# osc frame
from ricxappframe.xapp_frame import rmr
from ricxappframe.e2ap.asn1 import IndicationMsg
import ricxappframe.xapp_rest as ricrest


# utility
import utils.xapp_sub as subscribe
from utils.constants import Values
import utils.utility as utility

# xDevSM base dec
from decorators.base import BaseXDevSMWrapper

from sm_framework.py_oran.ByteArray import ByteArray


class xAppReportService(BaseXDevSMWrapper):
    def __init__(self,
                xapp_handler,
                logger,
                server,
                xapp_name,
                rmr_port,
                http_port,
                pltnamespace,
                app_namespace):
        super().__init__(xapp_handler, logger, server)
        self.xapp_name = xapp_name
        self.rmr_port = rmr_port
        self.http_port = http_port
        self.pltnamespace = pltnamespace
        self.app_namespace = app_namespace

        # TODO do we have specific parameters for report decorator?
        
        self.function_id = -1
        
        self.uri_subscriptions = Values.GENERAL_PATH.format(self.pltnamespace, Values.SUBSCRIPTION_SERVICE, self.pltnamespace, Values.SUBSCRIPTION_PORT) + "/ric/v1/subscriptions"
        self.subscriber = subscribe.NewSubscriber(uri=self.uri_subscriptions, rmr_port=self.rmr_port)
        

        # inventory_name -> list of subscription ids. A single xApp may hold
        # several subscriptions per gNB (e.g. one per slice).
        self.subscription_id = {}
        self.sm_func_wrapper = None

        self.__ext_sub_failed_callback = None
        self.__ind_msg_callback = None
        # Fired when the async subscription response arrives and resolves the
        # submgr SubscriptionId to the RMR-side E2EventInstanceId. 
        # Handler signature: handler(submgr_sub_id, e2_event_instance_id, gnb_inv_name).
        self.__ext_sub_resolved_callback = None
        # submgr SubscriptionId -> gNB inventory_name, populated at subscribe
        # time so the async resolver can route back to the originating gNB.
        self._pending_resolutions = {}
    
    def _handle_indication(self, xapp, summary):
        """
        Base handler for DApp Reports.
        """
        indm = IndicationMsg()

        # decoding E2AP
        indm.decode(summary[rmr.RMR_MS_PAYLOAD])
        xapp.logger.info("[xAppReportService] E2AP Decoded function id: {}".format(indm.function_id))

        ba_ind_header = utility.get_c_byte_array_from_py_byte_string(indm.indication_header)
        ba_ind_msg = utility.get_c_byte_array_from_py_byte_string(indm.indication_message)

        if ba_ind_header is None or ba_ind_msg is None:
            xapp.logger.error("[xAppReportService] Indication header or message byte array is None, skipping processing")
            return

        self.decode_message(indm.function_id, ba_ind_header, ba_ind_msg, summary['meid'], summary[rmr.RMR_MS_SUB_ID])
    
    
    def get_ran_function_description(self, json_ran_info):
        """
        Get decoded ran function description
        Parameters:
        ----------
        json_ran_info (json obj): json object obtained when by the get_ran_info function

        """
        if not json_ran_info:
            self.logger.info("[xAppReportService] json_ran_info object None value not admitted!")
            return

        for ran_func in json_ran_info["gnb"]["ranFunctions"]: 
            if ran_func["ranFunctionId"] == self.function_id:
                # selecting rc action
                ran_function_definition = ran_func["ranFunctionDefinition"]
                break
        self.logger.info(ran_function_definition)
        # Decoding RAN function Definition
        self.sm_func_wrapper.set_hex(hex=ran_function_definition)
        
        func_def_obj = self.sm_func_wrapper.decode()
        
        return func_def_obj

    @abstractmethod
    def decode_message(self, function_id, ba_ind_header, ba_ind_msg, meid, sub_id):
        pass

    def send_subscription(self, gnb, ev_trigger_enc: ByteArray, actions_to_be_setup):
        
        if len(actions_to_be_setup) == 0:
            self.logger.info("[xAppReportService] No action built!")
            return
        subscription_detail = self.subscriber.SubscriptionDetail(event_triggers=ev_trigger_enc.byte_array_to_tuple(),
                                                                  action_to_be_setup_list=actions_to_be_setup,
                                                                  xapp_event_instance_id=12345)
        client_endpoint = self.subscriber.SubscriptionParamsClientEndpoint(host="service-{}-{}-http.{}".format(self.app_namespace, self.xapp_name, self.app_namespace),
                                                                       http_port=self.http_port, 
                                                                       rmr_port=self.rmr_port)
        # --- e2 subscription directives
        #  e2_timeout_timer_value: in seconds
        #  e2_retry_count: number of retries
        #  rmr_routing_needed: boolean
        subsDirective = self.subscriber.SubscriptionParamsE2SubscriptionDirectives(2, 2, True)
        

        # before sending subscription, registring callback for subscription response
        if self.subscriber.ResponseHandler(self.subs_response_cb, self.server) is not True:
            self.logger.error("Error when trying to set the subscription reponse callback")
        
        self.logger.info("[xAppReportService] POST request for subscription to {}".format(self.uri_subscriptions))
        subscription_params = self.subscriber.SubscriptionParams(subscription_id=None,
                                        client_endpoint=client_endpoint,
                                        meid=gnb.inventory_name,                          
                                        ran_function_id=self.function_id,
                                        e2_subscription_directives=subsDirective,
                                        subscription_details=[subscription_detail])
        self.logger.info(subscription_params)
        data, reason, status = self.subscriber.Subscribe(subs_params=subscription_params)
        response_json = json.loads(data)
        self.logger.info("[xAppReportService] reason:{}".format(reason))
        self.logger.info("[xAppReportService] subscription reponse {}".format(response_json))

        # The sync response only carries the submgr-issued SubscriptionId
        # (string). The actual RMR correlator (E2EventInstanceId) is delivered
        # asynchronously via subs_response_cb once E2 setup completes.
        submgr_sub_id = response_json.get("SubscriptionId")
        if submgr_sub_id is not None:
            self.subscription_id.setdefault(gnb.inventory_name, []).append(submgr_sub_id)
            self._pending_resolutions[submgr_sub_id] = gnb.inventory_name

        self.logger.info(
            "[xAppReportService] gnb={} SubscriptionId(submgr)={} - awaiting async resolution".format(
                gnb.inventory_name, submgr_sub_id))

        return status, submgr_sub_id

    def handle(self, xapp, summary, sbuf):
        self._xapp_handler.handle(xapp, summary, sbuf)
    
    def send(self, *args, **kwargs):
        self._xapp_handler.send(*args, **kwargs)
    
    def terminate(self, signum, frame):
        # xDevSM manages subscription teardown centrally: every report-based
        # decorator (KPM / dApp / CCC) deletes the subscriptions it created at
        # submgr before delegating termination down the chain. Termination is the
        # single end-of-program hook, so each service model is unsubscribed
        # exactly once, in chain order.
        self.unsubscribe_all()
        self._xapp_handler.terminate(signum, frame)

    def unsubscribe_all(self):
        """Delete every subscription this decorator currently holds at submgr."""
        tag = type(self).__name__
        if not self.subscription_id:
            self.logger.info("[{}] no active subscriptions to remove on termination".format(tag))
            return
        for inventory_name, sub_ids in self.subscription_id.items():
            for sub_id in list(sub_ids):
                self.logger.info(
                    "[{}] unsubscribing gnb={} subid={} (DELETE {})".format(
                        tag, inventory_name, sub_id, self.uri_subscriptions))
                try:
                    self.subscriber.Unsubscribe(sub_id)
                except Exception as e:
                    self.logger.error("[{}] failed to unsubscribe {}: {}".format(tag, sub_id, e))
        self.subscription_id.clear()

    def get_subscription_id(self, inventory_name: str):
        """
        Parameters:
        ----------
        inventory_name (str): gnb inventory name

        Returns:
        ----------
        list of subscription ids registered for that gnb (empty if none)
        """
        return self.subscription_id.get(inventory_name, [])

    def remove_sub_id(self, sub_id: str):
        for sub_ids in self.subscription_id.values():
            if sub_id in sub_ids:
                sub_ids.remove(sub_id)
                return
        self.logger.error("[XappReportService] subscription id not found")
    
    def subs_response_cb(self, name, path, data, ctype):
        response = ricrest.initResponse()
        response['payload'] = ("{}")
        response_json = json.loads(data)
        self.logger.info("[XappReportService] Subscription response received: {}".format(response_json))
        # self.logger.info(response_json)
        if len(response_json["SubscriptionInstances"][0]["ErrorCause"]) > 0 and response_json["SubscriptionInstances"][0]["ErrorCause"] != " ":
            self.logger.info("Error for subscription: {} removing it from the pool reasons: {}".format(response_json['SubscriptionId'], response_json["SubscriptionInstances"][0]["ErrorCause"]))
            self.remove_sub_id(response_json['SubscriptionId'])
            if not self.__ext_sub_failed_callback is None:
                self.__ext_sub_failed_callback(response_json)
        else:
            self.logger.info("called response handler subscription successfull! Response: {}".format(response_json))
            response['payload'] = json.dumps(response_json)
            # Notify the xApp that submgr_sub_id (string) is now resolved to
            # an E2EventInstanceId (int) — the latter is what RMR stamps onto
            # subsequent indications.
            submgr_sub_id = response_json.get("SubscriptionId")
            instances = response_json.get("SubscriptionInstances") or []
            e2_event_instance_id = instances[0].get("E2EventInstanceId") if instances else None
            gnb_inv = self._pending_resolutions.pop(submgr_sub_id, None)
            self.logger.info(
                "[xAppReportService] subscription resolved: submgr={} e2_event_instance_id={} gnb={}".format(
                    submgr_sub_id, e2_event_instance_id, gnb_inv))
            if e2_event_instance_id is not None and self.__ext_sub_resolved_callback is not None:
                self.__ext_sub_resolved_callback(submgr_sub_id, e2_event_instance_id, gnb_inv)

        return response


    def register_sub_resolved_callback(self, handler):
        """
        Register a callback fired when the async subscription response resolves
        a submgr SubscriptionId to its RMR-side E2EventInstanceId.

        Handler signature: handler(submgr_sub_id, e2_event_instance_id, gnb_inv_name)
        """
        self.__ext_sub_resolved_callback = handler

    def register_sub_fail_callback(self, handler):
        """
        This method registers the function to be called when received an indication message
        --------
        The handler has one parameter:
        json reponse
        """
        self.__ext_sub_failed_callback = handler
    
    def register_ind_msg_callback(self, handler):
        """
        This method registers the function to be called when received an indication message
        --------
        The handler has two parameters:
        
        decoded_ind_hdr
        
        decoded_ind_msg
        """
        self.__ind_msg_callback = handler
    
    def get_indication_msg_callback(self):
        return self.__ind_msg_callback