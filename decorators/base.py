from handlers.I_xDevSM_xapp import BasexDevSMXapp


class BaseXDevSMWrapper(BasexDevSMXapp):
    """
    Base class for XDevSM decorators.
    This class can be extended to create specific decorators for XDevSM.
    """

    def __init__(self, xapp_handler: BasexDevSMXapp, logger, http_server):
        self._xapp_handler = xapp_handler
        self.outer_handle = self.handle
        self.logger = logger
        self.server = http_server

    
    def send(self, *args, **kwargs):
        self._xapp_handler.send(*args, **kwargs)

    def handle(self, xapp, summary, sbuf):
        self._xapp_handler.handle(xapp, summary, sbuf)

    def terminate(self, signum, frame):
        self._xapp_handler.terminate(signum, frame)

    def get_ran_function_description(self, json_ran_info):
        self._xapp_handler.get_ran_function_description(json_ran_info)

