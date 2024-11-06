import os
import signal
import time
import requests
import json

# osc xappframe
from ricxappframe.xapp_frame import RMRXapp, rmr
from mdclogpy import Level
import ricxappframe.xapp_rest as ricrest

# utility
from utils.constants import Values

# sm framework
import sm_framework.py_oran.rc.RCFunctionDef as RCFunctionDef

class XappRCFrame(RMRXapp):

    def __init__(self, xapp_name, address, port, entrypoint=None):
        print("to be defined")
        self.address = address
        self.port = port
        self.xapp_name = xapp_name

        self.rc_function_def_wrapper = RCFunctionDef.RCFuncDefWrapper(hex="") 

        # HTTP Server: create the thread HTTP server and set the uri handler callbacks
        self.server = ricrest.ThreadedHTTPServer(self.address, self.port)

        self.server.handler.add_handler(self.server.handler, "GET", "config", "/ric/v1/config", self.__config_get_handler)
        self.server.handler.add_handler(self.server.handler, "GET", "healthAlive", "/ric/v1/health/alive", self.__healthy_get_alive_handler)
        self.server.handler.add_handler(self.server.handler, "GET", "healthReady", "/ric/v1/health/ready", self.__healthyGetReadyHandler)

        signal.signal(signal.SIGINT, self.terminating_xapp)
        signal.signal(signal.SIGTERM, self.terminating_xapp)

        # start the server
        self.server.start()

        os.environ["RMR_SRC_ID"] = xapp_name
        os.environ["RMR_LOG_VLEVEL"] = str(4)
        os.environ["RMR_RTG_SVC"] = "4561"


        self.e2mgr_link = Values.GENERAL_PATH.format(Values.PLT_NAMESPACE, Values.E2MGR_SERVICE, Values.E2MGR_PORT) + "/v1/nodeb/"

        super().__init__(default_handler=self.__default_handler, rmr_port=4560, post_init=self._post_init, rmr_wait_for_ready=True)
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

        # if summary[rmr.RMR_MS_MSG_TYPE] == Values.RIC_INDICATION:
        #     self._handle_indication(xapp, summary) # FIXME maybe better with a private method 
        # elif summary[rmr.RMR_MS_MSG_TYPE] == Values.RIC_ERROR_INDICATION:
        #     xapp.logger.error("Error in indication message")
        # else:
        #     xapp.logger.info("not recognized message received")
        
        xapp.rmr_free(sbuf)

    def _default_entrypoint(self):
        while True:
            time.sleep(1)

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
    
    def get_ran_function_description(self, json_ran_info, ran_func_id=3) -> RCFunctionDef.RCFuncDef:
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

    def send_control_request(self):
        # TODO
        pass
    
    def terminating_xapp(self, signum, frame):
        self.xapp_shutdown()


    def logic():
        pass