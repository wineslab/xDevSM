import ricxappframe.subsclient as subsclient
import ricxappframe.xapp_rest as ricrest
from mdclogpy import Logger


logging = Logger(name=__name__)

class NewSubscriber():

    def __init__(self, uri, timeout=None, local_address="0.0.0.0", local_port=8088, rmr_port=4061):
        """
        init

        Parameters
        ----------
        uri: string
            xapp submgr service uri
        timeout: int
            rest method timeout
        local_address: string
            local interface IP address for rest service binding (for response handler)
        local_port: int
            local service port nunber for rest service binding (for response handler)
        rmr_port: int
            rmr port number
        """
        self.uri = uri
        self.timeout = timeout
        self.local_address = local_address
        self.local_port = local_port
        self.rmr_port = rmr_port
        self.url = "/ric/v1/subscriptions/response"
        self.serverHandler = None
        self.responseCB = None
        # Configure API
        configuration = subsclient.Configuration()
        configuration.verify_ssl = False
        configuration.host = "http://127.0.0.1:8088/"
        self.api = subsclient.ApiClient(configuration)
    

    # following methods are wrappers to hide the swagger client
    def SubscriptionParamsClientEndpoint(self, host=None, http_port=None, rmr_port=None):
        if host is None or http_port is None or rmr_port is None:
            logging.info("client end point - parameters not defined")
            return None
        else:
            client_end_point = {}
            client_end_point["Host"] = host
            client_end_point["HTTPPort"] = http_port
            client_end_point["RMRPort"] = rmr_port
            return client_end_point

    def SubscriptionParamsE2SubscriptionDirectives(self, e2_timeout_timer_value=None, e2_retry_count=None, rmr_routing_needed=None):
        e2_subscription_directives = {}
        e2_subscription_directives["E2TimeoutTimerValue"] = e2_timeout_timer_value
        e2_subscription_directives["E2RetryCount"] = e2_retry_count
        e2_subscription_directives["RMRRoutingNeeded"] = rmr_routing_needed

        return e2_subscription_directives

    def SubsequentAction(self, subsequent_action_type=None, time_to_wait=None):
        subsequent_action = {}
        # TODO missing checkings on subsequent_action_type and time_to_wait
        subsequent_action["SubsequentActionType"] = subsequent_action_type
        subsequent_action["TimeToWait"] = time_to_wait
        return subsequent_action

    def ActionToBeSetup(self, action_id=None, action_type=None, action_definition=None, subsequent_action=None):
        action_to_be_setup = {}
        action_to_be_setup["ActionID"] = action_id
        action_to_be_setup["ActionType"] = action_type
        action_to_be_setup["ActionDefinition"] = action_definition
        action_to_be_setup["SubsequentAction"] = subsequent_action
        return action_to_be_setup


    def SubscriptionDetail(self, xapp_event_instance_id=None, event_triggers=None, action_to_be_setup_list=None):
        subscription_detail = {}
        subscription_detail["XappEventInstanceId"] = xapp_event_instance_id
        subscription_detail["EventTriggers"] = event_triggers
        subscription_detail["ActionToBeSetupList"] = action_to_be_setup_list
        return subscription_detail

    def SubscriptionParams(self, subscription_id=None, client_endpoint=None, meid=None, ran_function_id=None, e2_subscription_directives=None, subscription_details=None):
        subscription_params = {}
        if subscription_id is None:
            subscription_params["SubscriptionId"] = ""
        else:
            subscription_params["SubscriptionId"] = subscription_id
        subscription_params["ClientEndpoint"] = client_endpoint
        subscription_params["Meid"] = meid
        subscription_params["RANFunctionID"] = ran_function_id
        subscription_params["E2SubscriptionDirectives"] = e2_subscription_directives
        subscription_params["SubscriptionDetails"] = subscription_details
        return subscription_params


    def Subscribe(self, subs_params):
        """
        Parameters
        ----------
        subs_params: dict
            subscription parameters
        Returns
        -------
        SubscriptionResponse
             json string of SubscriptionResponse object
        """
#        if subs_params is not None and type(subs_params) is subsclient.models.subscription_params.SubscriptionParams:
        if subs_params:
            response = self.api.request(method="POST", url=self.uri, headers=None, body=subs_params)
            return response.data, response.reason, response.status
        return None, "Input parameter is not SubscriptionParams{}", 500

    def Unsubscribe(self, subs_id=None):
        """
        Unsubscribe
            subscription remove

        Parameters
        ----------
        subs_id: int
            subscription id returned in SubscriptionResponse
        Returns
        -------
        response.reason: string
            http reason
        response.status: int
            http status code
        """
        response = self.api.request(method="DELETE", url=self.uri + "/" + subs_id, headers=None)
        return response.data, response.reason, response.status
    
    def ResponseHandler(self, responseCB=None, server=None):
        """
        ResponseHandler
            Starts the response handler and set the callback

        Parameters
        ----------
        responseCB
            Set the callback handler, if not set the the default self._responsePostHandler is used
        server: xapp_rest.ThreadedHTTPServer
            if set then the existing xapp_rest.ThreadedHTTPServer handler is used, otherwise a new will be created

        Returns
        -------
        status: boolean
            True = success, False = failed
        """
        # create the thread HTTP server
        self.serverHandler = server
        if self.serverHandler is None:
            # make the serverhandler
            self.serverHandler = ricrest.ThreadedHTTPServer(self.local_address, self.local_port)
            self.serverHandler.start()
        if self.serverHandler is not None:
            if responseCB is not None:
                self.responseCB = responseCB
            # get http handler with object reference
            self.serverHandler.handler.add_handler(self.serverHandler.handler, "POST", "response", self.url, responseCB)
            return True
        else:
            return False