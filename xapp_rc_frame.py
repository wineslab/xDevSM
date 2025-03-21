import os
import signal
import time
import requests
import json
import sys
import ctypes

# osc xappframe
from ricxappframe.xapp_frame import RMRXapp, rmr
from ricxappframe.e2ap.asn1 import ControlRequestMsg
from ricxappframe.util.constants import Constants

from mdclogpy import Level
import ricxappframe.xapp_rest as ricrest

# utility
from utils.constants import Values

# sm framework
import sm_framework.py_oran.rc.RCFunctionDef as funcdef
import sm_framework.py_oran.rc.RCControlReq as ctrlReq
import sm_framework.py_oran.rc.RCControlHdr as ctrlhdr

class XappRCFrame(RMRXapp):

    def __init__(self, address, port, entrypoint=None):
        super().__init__(default_handler=self.__default_handler, rmr_port=4560, post_init=self._post_init, rmr_wait_for_ready=True)
        self.address = address
        self.port = port

        self.rc_function_def_wrapper = funcdef.RCFuncDefWrapper(hex="") 

         # Getting plt namespace
        self.pltnamespace = os.environ.get("PLT_NAMESPACE")
        if self.pltnamespace is None:
            self.pltnamespace = Constants.DEFAULT_PLT_NS

        self.xapp_name = self._config_data.get("name")

        # Getting app namespace
        self.app_namespace = self._config_data.get("APP_NAMESPACE")
        if self.app_namespace is None:
            self.app_namespace = Constants.DEFAULT_XAPP_NS
        # Getting app namespace
        self.app_namespace = self._config_data.get("APP_NAMESPACE")
        if self.app_namespace is None:
            self.app_namespace = Constants.DEFAULT_XAPP_NS


        # HTTP Server: create the thread HTTP server and set the uri handler callbacks
        self.server = ricrest.ThreadedHTTPServer(self.address, self.port)

        self.server.handler.add_handler(self.server.handler, "GET", "config", "/ric/v1/config", self.__config_get_handler)
        self.server.handler.add_handler(self.server.handler, "GET", "healthAlive", "/ric/v1/health/alive", self.__healthy_get_alive_handler)
        self.server.handler.add_handler(self.server.handler, "GET", "healthReady", "/ric/v1/health/ready", self.__healthyGetReadyHandler)

        signal.signal(signal.SIGINT, self.terminating_xapp)
        signal.signal(signal.SIGTERM, self.terminating_xapp)

        # start the server
        self.server.start()

        os.environ["RMR_SRC_ID"] = self.xapp_name
        os.environ["RMR_LOG_VLEVEL"] = str(4)
        os.environ["RMR_RTG_SVC"] = "4561"


        self.e2mgr_link = Values.GENERAL_PATH.format(self.pltnamespace, Values.E2MGR_SERVICE, self.pltnamespace, Values.E2MGR_PORT) + "/v1/nodeb/"

        self.logger.set_level(Level.DEBUG)

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
        if summary[rmr.RMR_MS_MSG_TYPE] == Values.RIC_CONTROL_ACK:
            xapp.logger.info("Received control ack")
            self.logger.info("Received control ack")
        # if summary[rmr.RMR_MS_MSG_TYPE] == Values.RIC_INDICATION:
        #     self._handle_indication(xapp, summary) # FIXME maybe better with a private method 
        # elif summary[rmr.RMR_MS_MSG_TYPE] == Values.RIC_ERROR_INDICATION:
        #     xapp.logger.error("Error in indication message")
        # else:
        #     xapp.logger.info("not recognized message received")
        
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
    
    def get_ran_function_description(self, json_ran_info, ran_func_id=3) -> funcdef.RCFuncDef:
        """
        Get decoded ran function description
        Parameters:
        ----------
        json_ran_info (json obj): json object obtained when by the get_ran_info function
        ran_func_id(int): by default is 3 (rc)

        Returns:
        ----------
        RCFuncDefWrapper - wrapper of RC function definition object managing memory deallocation
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
        self.rc_function_def_wrapper.set_hex(hex=ran_function_definition)
        # func_def_obj = KpmFunctionDef.decode(hex=ran_function_definition)
        func_def_obj = self.rc_function_def_wrapper.decode()
        return func_def_obj

    def send_control_request(self, e2_node_id, func_def: funcdef.RCFuncDef, ue_id: ctrlhdr.ue_id_e2sm_t=None, call_process_id: bytes=b""):
        # TODO Add function parameters
        # TODO where should we take call_process_id information
        # Creating request
        
        # Service model encoding
        wrapper = ctrlReq.RCControlReqWrapper()
        if ue_id is None:
            self.logger.info("[warn] using mock ue_id")
            ue_id = self.get_mock_ue_id()

        wrapper.gen_rc_msg(ran_func_dsc=func_def, ue_id=ue_id)
        wrapper.print_ctrl_req()
        
        rc_ctrl_req_enc = wrapper.encode()
        
        hdr_byte_array = rc_ctrl_req_enc.hdr_encoded.to_bytes()
        ctrl_msg_byte_array = rc_ctrl_req_enc.msg_encoded.to_bytes()

        self.logger.info("hdr encoded: {}".format(hdr_byte_array))
        self.logger.info("ctrl encoded: {}".format(ctrl_msg_byte_array))

        # E2AP encoding
        rc_ctrl_rec_msg = ControlRequestMsg()
        size, payload = rc_ctrl_rec_msg.encode(call_process_id=call_process_id,
                                               requestor_id=1,
                                               control_ack_request=1, # Missing
                                               request_sequence_number=0, # Missing
                                               control_header=hdr_byte_array,
                                               control_message=ctrl_msg_byte_array,
                                               ran_function_id=3)

        self.logger.info("Sending RCControlRequest Message: {} ({})".format(size, payload))
        sbuf = rmr.rmr_alloc_msg(vctx=self._mrc, size=len(payload), mtype=Values.RIC_CONTROL_REQ)
        rmr.set_payload_and_length(payload,sbuf)
        rmr.generate_and_set_transaction_id(sbuf)
        sbuf.contents.state = 0
        sbuf.contents.mtype = Values.RIC_CONTROL_REQ
        sbuf.contents.sub_id = -1
        self.logger.info("E2 node id: {}".format(e2_node_id.encode("utf8")))
        rmr.rmr_set_meid(sbuf, e2_node_id.encode("utf8"))
        sbuf = rmr.rmr_send_msg(self._mrc, sbuf)
        self.logger.info("Message Sent")
        # if sbuf.contents.state == 0:
        #     self.logger.info("freeing buffer")
        #     self.rmr_free(sbuf)
            
        
        # self.rmr_send(payload=payload, mtype=Values.RIC_CONTROL_REQ)
        
    
    def terminating_xapp(self, signum, frame):
        self.logger.info("Received termination signal")
        self.xapp_shutdown()
        self.logger.info("Bye!")
        sys.exit()

    def get_mock_ue_id(self) -> ctrlhdr.ue_id_e2sm_t:
        ue_id = ctrlhdr.ue_id_e2sm_t()
        ue_id.type = ctrlhdr.ue_id_e2sm_e.GNB_UE_ID_E2SM
        
        gnb_mono = ctrlhdr.gnb_e2sm_t()
        gnb_mono.amf_ue_ngap_id = 9
        
        # guami
        plmn_id = ctrlhdr.e2sm_plmn_t()
        plmn_id.mcc = 1
        plmn_id.mnc = 1
        plmn_id.mnc_digit_len = 2 
        guami = ctrlhdr.guami_t()
        guami.plmn_id = plmn_id
        guami.amf_region_id = 1
        guami.amf_set_id = 1
        guami.amf_ptr = 1
        gnb_mono.guami = guami

        gnb_mono.gnb_cu_ue_f1ap_lst_len = 0
        gnb_mono.gnb_cu_cp_ue_e1ap_lst_len = 0
        gnb_mono.ran_ue_id = ctypes.pointer(ctypes.c_ulong(1))

        # gnb_pointer = ctypes.pointer(gnb_mono)

        ue_id.union.gnb = gnb_mono

        return ue_id


    def logic():
        pass