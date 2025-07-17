import os
import signal
import requests
import json
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

class RCControlBase(RMRXapp):
    def __init__(self, address, entrypoint=None):

        self.rmr_port = 4560

        super().__init__(default_handler=self.__default_handler, rmr_port=self.rmr_port, post_init=self._post_init, rmr_wait_for_ready=True)
        
        self.logger.set_level(Level.DEBUG)

        self.address = address

        self.rc_function_def_wrapper = funcdef.RCFuncDefWrapper(hex="") 
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
        else:
            self.logger.info("http port: {}, rmr port: {}, rmr svc port: {}".format(self.http_port, self.rmr_port, self.rmr_svc_port))

        # Getting plt namespace
        self.pltnamespace = os.environ.get("PLT_NAMESPACE")
        if self.pltnamespace is None:
            self.pltnamespace = Constants.DEFAULT_PLT_NS

        self.xapp_name = self._config_data.get("name")

        # Getting app namespace
        self.app_namespace = self._config_data.get("APP_NAMESPACE")
        if self.app_namespace is None:
            self.app_namespace = Constants.DEFAULT_XAPP_NS


        # HTTP Server: create the thread HTTP server and set the uri handler callbacks
        self.server = ricrest.ThreadedHTTPServer(self.address, self.http_port)

        self.server.handler.add_handler(self.server.handler, "GET", "config", "/ric/v1/config", self.__config_get_handler)
        self.server.handler.add_handler(self.server.handler, "GET", "healthAlive", "/ric/v1/health/alive", self.__healthy_get_alive_handler)
        self.server.handler.add_handler(self.server.handler, "GET", "healthReady", "/ric/v1/health/ready", self.__healthyGetReadyHandler)

        signal.signal(signal.SIGINT, self.terminating_xapp)
        signal.signal(signal.SIGTERM, self.terminating_xapp)

        # start the server
        self.server.start()

        os.environ["RMR_SRC_ID"] = self.xapp_name
        os.environ["RMR_LOG_VLEVEL"] = str(4)
        os.environ["RMR_RTG_SVC"] = str(self.rmr_svc_port)


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
            # TODO Add invocation of control ack handler
            xapp.logger.info("Received control ack")
        elif summary[rmr.RMR_MS_MSG_TYPE] == Values.RIC_CONTROL_FAILURE:
            xapp.logger.error("Received failure ack")
        
        xapp.rmr_free(sbuf)