import os
import signal
import time

from ricxappframe.xapp_frame import Xapp, rmr
from mdclogpy import Level

# utility
from utils.constants import Values


class XappRCFrame(Xapp):

    def __init__(self, xapp_name, address, port, entrypoint=None):
        print("to be defined")

        signal.signal(signal.SIGINT, self.terminating_xapp)
        signal.signal(signal.SIGTERM, self.terminating_xapp)

        os.environ["RMR_SRC_ID"] = xapp_name
        os.environ["RMR_LOG_VLEVEL"] = str(4)
        os.environ["RMR_RTG_SVC"] = "4561"

        self.e2mgr_link = Values.GENERAL_PATH.format(Values.PLT_NAMESPACE, Values.E2MGR_SERVICE, Values.E2MGR_PORT) + "/v1/nodeb/"
       
        # address and port could be used for a server rest to send command to the e2 node
        
        if entrypoint is None:
            self._entrypoint_func = entrypoint
        else:
            self._entrypoint_func = self._default_entrypoint
        
        super().__init__(entrypoint=self._entrypoint_func, rmr_port=4560, rmr_wait_for_ready=True)
        self.logger.set_level(Level.DEBUG)


        


    def _default_entrypoint(self):
        while True:
            time.sleep(1)

    def get_ran_function_desc_info(self):
        # TODO
        pass

    def send_control_request(self):
        # TODO
        pass
    
    def terminating_xapp(self):
        self.xapp_shutdown()


    def logic():
        pass