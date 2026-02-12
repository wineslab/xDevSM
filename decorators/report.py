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
        

        self.subscription_id = {}

        self.__ext_sub_failed_callback = None
        self.__ind_msg_callback = None
    
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

        self.decode_message(indm.function_id, ba_ind_header, ba_ind_msg)
    
    @abstractmethod
    def decode_message(self, function_id, ba_ind_header, ba_ind_msg):
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
        self.subscription_id[gnb.inventory_name] = response_json["SubscriptionId"]
        self.logger.info("[xAppReportService] Got the subscription reponse, my subscription id for gnb {} is: {}".format(gnb.inventory_name, self.subscription_id))

        return status

    def handle(self, xapp, summary, sbuf):
        self._xapp_handler.handle(xapp, summary, sbuf)
    
    def send(self, *args, **kwargs):
        self._xapp_handler.send(*args, **kwargs)
    
    def terminate(self, signum, frame):
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

    def remove_sub_id(self, sub_id: str):
        to_remove = None
        for key in self.subscription_id.keys():
            if self.subscription_id[key] == sub_id:
                to_remove = key
                break
        
        if to_remove is None:
            self.logger.error("subscription id not found")
        else:
            del self.subscription_id[to_remove]
    
    def subs_response_cb(self, name, path, data, ctype):
        response = ricrest.initResponse()
        response['payload'] = ("{}")
        response_json = json.loads(data)
        self.logger.info(response_json)
        if len(response_json["SubscriptionInstances"][0]["ErrorCause"]) > 0 and response_json["SubscriptionInstances"][0]["ErrorCause"] != " ":
            self.logger.info("Error for subscription: {} removing it from the pool reasons: {}".format(response_json['SubscriptionId'], response_json["SubscriptionInstances"][0]["ErrorCause"]))
            self.remove_sub_id(response_json['SubscriptionId'])
            if not self.__ext_sub_failed_callback is None:
                self.__ext_sub_failed_callback(response_json)
        else:
            self.logger.info("called response handler subscription successfull! Response: {}".format(response_json))
            response['payload'] = json.dumps(response_json)
        
        return response


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