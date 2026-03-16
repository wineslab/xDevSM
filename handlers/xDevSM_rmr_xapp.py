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
from utils.utility import write_routing_table

# xDevSM imports
from handlers.I_xDevSM_xapp import BasexDevSMXapp

class xDevSMRMRXapp(RMRXapp, BasexDevSMXapp):
    def __init__(self, address, xapp_name=None, entrypoint=None, route_file=None):
        self.rmr_port = 4560
        self._handler = None        
        super().__init__(default_handler=self._dispatch_event, rmr_port=self.rmr_port, post_init=self._post_init, rmr_wait_for_ready=True)
        
        self.logger.set_level(Level.DEBUG)

        self.xapp_name = xapp_name if xapp_name else self._config_data.get("name")
        self.address = address
        
        self.shutdown = None

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

        # Setting routes
        if route_file is None:
            route_file = "./config/uta_rtg.rt"
    
        write_routing_table(self.xapp_name, self.app_namespace, self.rmr_port, route_file)


        # HTTP Server: create the thread HTTP server and set the uri handler callbacks
        self.server = ricrest.ThreadedHTTPServer(self.address, self.http_port)

        self.server.handler.add_handler(self.server.handler, "GET", "config", "/ric/v1/config", self.__config_get_handler)
        self.server.handler.add_handler(self.server.handler, "GET", "healthAlive", "/ric/v1/health/alive", self.__healthy_get_alive_handler)
        self.server.handler.add_handler(self.server.handler, "GET", "healthReady", "/ric/v1/health/ready", self.__healthyGetReadyHandler)

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
    
    def register_handler(self, handler):
        self._handler = handler

    def register_shutdown(self, shutdown):
        """
        Register a shutdown function to be called on termination.
        This is particularly useful fo cleaning up resources or stopping services gracefully. (e.g., influxdb close)
        """
        self.shutdown = shutdown

    def _dispatch_event(self, xapp, summary, sbuf):
        xapp.logger.info("[xDevSMRMRXapp] dispatching event")
        if self._handler is not None:
            self._handler(xapp, summary, sbuf)
        else:        
            self.handle(xapp, summary, sbuf)

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
        uri_e2_mgr = self.e2mgr_link + e2node.inventory_name

        response = requests.get(uri_e2_mgr)
        return response.json()
    

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

    def get_selected_e2node_info(self, e2node_inventory_name=None):
        """
        Returns:
        ----------
        selected gnb, gnb info
        """
        selected_gnb = None
        gnb_info = None

        gnb_list = self.get_list_gnb_ids()

        if len(gnb_list) == 0:
            self.logger.info("[xDevSMRMRXapp] no gnb available")
            return None, None

        if not e2node_inventory_name:
            # This logic considers each gnb available for that RIC
            self.logger.info("[xDevSMRMRXapp] selecting the first gnb connected")
        else:
            # This logic only considers the passed gnb
            self.logger.info("[xDevSMRMRXapp] querying status of passed gnb {}".format(e2node_inventory_name))

        for index, gnb in enumerate(gnb_list):
            if e2node_inventory_name and gnb.inventory_name != e2node_inventory_name:
                continue

            gnb_info = self.get_ran_info(e2node=gnb)

            if gnb_info["connectionStatus"] != "CONNECTED":
                self.logger.info("[xDevSMRMRXapp] E2 node {} not connected! Skipping...".format(gnb.inventory_name))
                continue

            selected_gnb = gnb
            break

        if selected_gnb is None:
            if not e2node_inventory_name:
                self.logger.info("[xDevSMRMRXapp] No gnb connected")
            else:
                self.logger.info("[xDevSMRMRXapp] Passed gnb {} not connected".format(e2node_inventory_name))
            return None, None
        else:
            self.logger.info("[xDevSMRMRXapp] selected gnb {}".format(gnb.inventory_name))

        return selected_gnb, gnb_info

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
    

    def handle(self, xapp, summary, sbuf):
        self.logger.info("[xDevSMRMRXapp] Recevied handle message Event")
        xapp.rmr_free(sbuf)
    
    def send(self, *args, **kwargs):
        self.logger.info("[xDevSMRMRXapp] Recevied Sending message Event")

    def get_ran_function_description(self, json_ran_info):
        self.logger.info("[xDevSMRMRXapp] Recevied get_ran_function_description Event")
    
    def terminate(self, signum, frame):
        self.logger.info("[xDevSMRMRXapp] Received termination signal")
        self.stop()
        if self.shutdown is not None:
            self.shutdown()
        else:
            self.logger.info("[xDevSMRMRXapp] No shutdown function registered")
        self.logger.info("[xDevSMRMRXapp] Bye!")
