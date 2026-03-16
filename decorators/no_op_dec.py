from decorators.base import BaseXDevSMWrapper

class NullDecorator(BaseXDevSMWrapper):
    """
    A no-operation decorator that does nothing.
    This can be used as a placeholder for decorators that are not yet implemented.
    """
    def __init__(self, xapp_handler):
        super().__init__(xapp_handler)

    def handle(self, xapp, summary, sbuf):
        xapp.logger.info("[NullDecorator] Received handle message Event")
    
    def send(self, *args, **kwargs):
        print("[NullDecorator] Received send message Event")
    

    def get_ran_function_description(self, json_ran_info):
        print("[NullDecorator] Received get_ran_function_description Event")
    
    def terminate(self):
        print("[NullDecorator] Terminating xApp")
    