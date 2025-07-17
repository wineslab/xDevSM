import os
import signal
import json
import requests

from mdclogpy import Level

# osc xappframe
from ricxappframe.xapp_frame import RMRXapp, rmr
from ricxappframe.util.constants import Constants
import ricxappframe.xapp_rest as ricrest

# utility
from utils.constants import Values

# sm framework
import sm_framework.py_oran.rc.RCFunctionDef as funcdef


class BaseRMRXapp(RMRXapp):
    def __init__(self, address, entrypoint=None):
        self.rmr_port = 4560

        super().__init__(default_handler=self.handle, rmr_port=self.rmr_port, post_init=self._post_init, rmr_wait_for_ready=True)
        
        self.logger.set_level(Level.DEBUG)

        self.xapp_name = self._config_data.get("name")
        self.address = address

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
            self.logger.info("http port: {}, rmr svc port: {}".format(self.http_port, self.rmr_svc_port))
        
        self.logger.info("http port: {}, rmr port: {}, rmr svc port: {}".format(self.http_port, self.rmr_port, self.rmr_svc_port))

        # Getting plt namespace
        self.pltnamespace = os.environ.get("PLT_NAMESPACE")
        if self.pltnamespace is None:
            self.pltnamespace = Constants.DEFAULT_PLT_NS


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
        os.environ["RMR_RTG_SVC"] = str(self.rmr_svc_port)

        self.e2mgr_link = Values.GENERAL_PATH.format(self.pltnamespace, Values.E2MGR_SERVICE, self.pltnamespace, Values.E2MGR_PORT) + "/v1/nodeb/"
    
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
    
    def get_ran_function_description(self, json_ran_info):
        pass

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
    

    def terminating_xapp(self, signum, frame):
        self.logger.info("Received termination signal")
        self.xapp_shutdown()
        self.logger.info("Bye!")
    

    def handle(self, xapp, summary, sbuf):
        pass

    def logic():
        pass