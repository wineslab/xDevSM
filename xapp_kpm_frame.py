import os
import signal
import json
import requests
import sys
import copy
from typing import Tuple

# osc xappframe
from ricxappframe.xapp_frame import RMRXapp, rmr
from ricxappframe.subsclient.models.event_trigger_definition import EventTriggerDefinition
from ricxappframe.e2ap.asn1 import IndicationMsg
from ricxappframe.util.constants import Constants
import ricxappframe.xapp_rest as ricrest
from mdclogpy import Level


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


class XappKpmFrame(RMRXapp):

    def __init__(self, address):
        self.rmr_port = 4560
    
        super().__init__(default_handler=self.__default_handler, rmr_port=self.rmr_port, post_init=self._post_init, rmr_wait_for_ready=True)
        
        self.logger.set_level(Level.DEBUG)

        self.address = address        
        self.subscription_id = {}

        # Getting ports from config file
        messaging_format = self._config_data.get("messaging")
        self.http_port, self.rmr_svc_port = self.loading_ports(messaging_format)
        if self.http_port is None:
            self.logger.error("http port not found: setting default to 8080")
            self.http_port = 8080
        # TODO --> This cannot be made dynamic right now. We should change where the config file is read            
        # elif self.rmr_port is None: 
        #     self.logger.error("rmr port not found: setting default to 4560")
        #     self.rmr_port = 4560
        elif self.rmr_svc_port is None: 
            self.logger.error("rmr svc port not found: setting default to 4561")
            self.rmr_svc_port = 4561
        
        self.logger.info("http port: {}, rmr port: {}, rmr svc port: {}".format(self.http_port, self.rmr_port, self.rmr_svc_port))

        # Getting plt namespace
        self.pltnamespace = os.environ.get("PLT_NAMESPACE")
        if self.pltnamespace is None:
            self.pltnamespace = Constants.DEFAULT_PLT_NS
        
        # getting xapp name
        self.xapp_name = self._config_data.get("name")

        # Getting app namespace
        self.app_namespace = self._config_data.get("APP_NAMESPACE")
        if self.app_namespace is None:
            self.app_namespace = Constants.DEFAULT_XAPP_NS


        self.uri_subscriptions = Values.GENERAL_PATH.format(self.pltnamespace, Values.SUBSCRIPTION_SERVICE, self.pltnamespace, Values.SUBSCRIPTION_PORT) + "/ric/v1/subscriptions"

        # Subscriber
        self.subscriber = subscribe.NewSubscriber(uri=self.uri_subscriptions, rmr_port=self.rmr_port)

        # HTTP Server: create the thread HTTP server and set the uri handler callbacks
        self.server = ricrest.ThreadedHTTPServer(self.address, self.http_port)

        self.__ind_msg_callback = None
        self.__sub_failed_callback = None

        self.server.handler.add_handler(self.server.handler, "GET", "config", "/ric/v1/config", self.__config_get_handler)
        self.server.handler.add_handler(self.server.handler, "GET", "healthAlive", "/ric/v1/health/alive", self.__healthy_get_alive_handler)
        self.server.handler.add_handler(self.server.handler, "GET", "healthReady", "/ric/v1/health/ready", self.__healthyGetReadyHandler)

        signal.signal(signal.SIGINT, self.terminate)
        signal.signal(signal.SIGTERM, self.terminate)

        # start the server
        self.server.start()

        self.e2mgr_link = Values.GENERAL_PATH.format(self.pltnamespace, Values.E2MGR_SERVICE, self.pltnamespace, Values.E2MGR_PORT) + "/v1/nodeb/"

        # self.logger.info("Initializing xApp")

        os.environ["RMR_SRC_ID"] = self.xapp_name
        os.environ["RMR_LOG_VLEVEL"] = str(4)
        os.environ["RMR_RTG_SVC"] = str(self.rmr_svc_port)

        self.kpm_func_def_wrapper = KpmFunctionDef.KpmFuncDefArrWrapper(hex="")

    def __config_get_handler(self, name, path, data, ctype):
        response = ricrest.initResponse()
        response['payload'] = json.dumps(self._config_data)
        return response
    
    def __healthy_get_alive_handler(self, name, path, data, ctype): 
        response = ricrest.initResponse()
        response['payload'] = ("{'status': 'alive'}")
        return response
    
    def __healthyGetReadyHandler(self, name, path, data, ctype):
        response = ricrest.initResponse()
        response['payload'] = ("{'status': 'ready'}")
        return response
    
    def _post_init(self, xapp):
        xapp.logger.info("xApp Initialized")

    def __default_handler(self, xapp, summary, sbuf):

        xapp.logger.info("received: {}".format(summary))

        if summary[rmr.RMR_MS_MSG_TYPE] == Values.RIC_INDICATION:
            self._handle_indication(xapp, summary) # FIXME maybe better with a private method 
        elif summary[rmr.RMR_MS_MSG_TYPE] == Values.RIC_ERROR_INDICATION:
            xapp.logger.error("Error in indication message")
        else:
            xapp.logger.info("not recognized message received")
        
        xapp.rmr_free(sbuf)
    

    def get_ran_info(self, e2node):
        """
        Get E2Node related info. Used to get RAN function description

        Parameters:
        ----------
        gnb (json obj): E2 node

        Returns:
        ----------
        json object containing E2 node related information
        """
        self.logger.info("Getting gnb {} info".format(e2node.inventory_name))
        uri_e2_mgr = self.e2mgr_link + e2node.inventory_name

        response = requests.get(uri_e2_mgr)
        return response.json()

    def get_ran_function_description(self, json_ran_info, ran_func_id=2) -> KpmFunctionDef.KpmFuncDefArr:
        """
        Get decoded ran function description
        Parameters:
        ----------
        json_ran_info (json obj): json object obtained when by the get_ran_info function
        ran_func_id(int): by default is 2 (kpm)

        Returns:
        ----------
        KpmFuncDefArrWrapper - wrapper of KpmFunctionDef object managing memory deallocation
        """
        if not json_ran_info:
            self.logger.info("json_ran_info object None value not admitted!")
            return

        for ran_func in json_ran_info["gnb"]["ranFunctions"]: 
            if ran_func["ranFunctionId"] == ran_func_id:
                # selecting kpm action
                ran_function_definition = ran_func["ranFunctionDefinition"]
                break
        self.logger.info(ran_function_definition)
        # Decoding RAN function Definition
        self.kpm_func_def_wrapper.set_hex(hex=ran_function_definition)
        # func_def_obj = KpmFunctionDef.decode(hex=ran_function_definition)
        func_def_obj = self.kpm_func_def_wrapper.decode()
        return func_def_obj

    def _handle_indication(self, xapp, summary):
        
        indm = IndicationMsg()

        # decoding E2AP
        indm.decode(summary[rmr.RMR_MS_PAYLOAD])

        ba_ind_header = utility.get_c_byte_array_from_py_byte_string(indm.indication_header)
        ba_ind_msg = utility.get_c_byte_array_from_py_byte_string(indm.indication_message)
        
        if ba_ind_msg is None:
            # information not decoded correctly
            return
        
        print(ba_ind_header)
        # Indication hdr - decoding E2SM
        ind_hdr_mgr = KpmIndicationHdr.KpmIndHdrWrapper(ba_ind_header)
        decoded_ind_hdr = ind_hdr_mgr.decode()
        if decoded_ind_hdr is None:
            xapp.logger.info("indication header not decoded correctly")
            return
        xapp.logger.debug("indication header encoded: {}, indication header encoded ba: {}, indication header format decoded: {}".format(
            indm.indication_header, ba_ind_header, decoded_ind_hdr.type.value
        ))

        # Indication msg - decoding E2SM
        ind_msg_mgr = KpmIndicationMsg.KpmIndMsgWrapper(ba_ind_msg)
        decoded_ind_msg = ind_msg_mgr.decode()

        if self.__ind_msg_callback is None:
            xapp.logger.info("No indication message callback registered - printing default information")
            xapp.logger.debug("indication header encoded: {}, indication header encoded ba: {}, indication header format decoded: {}".format(
                indm.indication_header, ba_ind_header, decoded_ind_hdr.type.value
            ))
            decoded_ind_msg.print_meas_info(xapp.logger)
        else:
            self.__ind_msg_callback(decoded_ind_hdr, decoded_ind_msg, summary['meid'])

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
    
    def subscribe(self, gnb, ev_trigger: Tuple[int, float], func_def: dict, action_type=Values.ACTION_TYPE, ran_period_ms=1000, sst=1, sd=0):

        self.logger.info("Preparing subscription for gnb: {}".format(gnb.inventory_name))
        

        if self.subscriber.ResponseHandler(self.subs_response_cb, self.server) is not True:
            self.logger.error("Error when trying to set the subscription reponse callback")

        # encoding event trigger
        encoded_ev_trig = function_definition_builder.ev_trigger_encoder(period_ev_trig=ev_trigger[1])

        self.logger.info("event trigger encoded: {}".format(encoded_ev_trig.byte_array_to_tuple()))
        
        actions = []
        # encoding action defintion
        encoded_actions_def = function_definition_builder.action_encoder(action_def_dict=func_def, gran_period_ms=ran_period_ms, sst=sst, sd=sd)

        for index, key in enumerate(encoded_actions_def.keys()):
            value = encoded_actions_def[key].byte_array_to_tuple()
            self.logger.info("actions encoded: {}".format(value))

            action = self.subscriber.ActionToBeSetup(action_id=1,
                                                    action_type=action_type,
                                                    action_definition=value,
                                                    subsequent_action=self.subscriber.SubsequentAction(subsequent_action_type="continue", time_to_wait="w5ms"))
            actions.append(action)
        
        if len(actions) == 0:
            self.logger.info("No action built!")
            return
        subscription_detail = self.subscriber.SubscriptionDetail(event_triggers=encoded_ev_trig.byte_array_to_tuple(),
                                                                  action_to_be_setup_list=actions,
                                                                  xapp_event_instance_id=12345)
        client_endpoint = self.subscriber.SubscriptionParamsClientEndpoint(host="service-{}-{}-http.{}".format(self.app_namespace, self.xapp_name, self.app_namespace), # make it as a parameter 
                                                                       http_port=self.http_port, 
                                                                       rmr_port=self.rmr_port)
        subsDirective = self.subscriber.SubscriptionParamsE2SubscriptionDirectives(2, 2, True)
        

        
        self.logger.info("POST request for subscription to {}".format(self.uri_subscriptions))
        subscription_params = self.subscriber.SubscriptionParams(subscription_id=None,
                                        client_endpoint=client_endpoint,
                                        meid=gnb.inventory_name,                          
                                        ran_function_id=2,
                                        e2_subscription_directives=subsDirective,
                                        subscription_details=[subscription_detail])
        self.logger.info(subscription_params)
        data, reason, status = self.subscriber.Subscribe(subs_params=subscription_params)
        response_json = json.loads(data)
        self.logger.info("reason:{}".format(reason))
        self.logger.info("subscription reponse {}".format(response_json))
        self.subscription_id[gnb.inventory_name] = response_json["SubscriptionId"]
        self.logger.info("Got the subscription reponse, my subscription id for gnb {} is: {}".format(gnb.inventory_name, self.subscription_id))

        # freeing memory
        # ByteArray.free(ctypes.byref(encoded_action_def))

        return status

    def get_ue_id(self, ue_meas_report: KpmIndicationMsg.ue_id_e2sm_t) -> int:
        if ue_meas_report.type.value == ue_id_e2sm_e.GNB_UE_ID_E2SM:
            gnb_mono = ue_meas_report.union.gnb
            if gnb_mono.ran_ue_id: 
                return gnb_mono.ran_ue_id.contents.value
        elif ue_meas_report.type.value == ue_id_e2sm_e.GNB_DU_UE_ID_E2SM:
            gnb_du = ue_meas_report.union.gnb_du
            if gnb_du.ran_ue_id:
                return gnb_du.ran_ue_id.contents.value
        elif ue_meas_report.type.value == ue_id_e2sm_e.GNB_CU_UP_UE_ID_E2SM:
            gnb_cu = ue_meas_report.union.gnb_cu_up
            if gnb_cu.ran_ue_id:
                return gnb_cu.ran_ue_id.contents.value
        else:
            self.logger.error("format not supported ({})".format(ue_meas_report.type.value))
    


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
    
    def get_app_namespace(self):
        """
        Returns:
        ----------
        app namespace
        """
        return self.app_namespace
    
    def get_pltnamespace(self):
        """
        Returns:
        ----------
        plt namespace
        """
        return self.pltnamespace
    
    def get_xapp_name(self):
        """
        Returns:
        ----------
        xapp name
        """
        return self.xapp_name
    
    def loading_ports(self, messaging_format):
        http_port = None
        rmr_port = None
        rmr_svc_port = None
        for el in messaging_format["ports"]:
            if el["name"] == "http":
                http_port = el["port"]
            elif el["name"] == "rmrdata":
                rmr_port = el["port"]
            elif el["name"] == "rmrroute":  
                rmr_svc_port = el["port"]
            else:
                self.logger.error("Port not recognized")
        
        return http_port, rmr_svc_port
    

    def terminating_xapp(self):
        self.logger.info("Received termination signal")
        if self.subscription_id is None:
            self.logger.info("Not subscribed - terminating...")
        else:
            for key in self.subscription_id.keys():
                self.logger.info("Unsubscribing from gnb: {}, subid: {}, DELETE {}".format(key, self.subscription_id[key], self.uri_subscriptions))
                # self.subscriber.Unsubscribe(subs_id=str(self.subscription_id[key]))#-- not supported in oai
        self.stop() #-- to fix registration
        self.logger.info("Bye!")
        # sys.exit()

    def terminate(self, signum, frame):
        self.terminating_xapp()

    def logic(self):
        pass
