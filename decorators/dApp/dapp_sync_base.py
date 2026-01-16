from abc import abstractmethod
from decorators.base import BaseXDevSMWrapper

import sm_framework.py_oran.dapp.report.DAppFunctionDef as dappfuncdef

class DAppSyncBase(BaseXDevSMWrapper):
    def __init__(self, xapp_handler, logger, server, xapp_name, rmr_port, http_port, pltnamespace, app_namespace):
        super().__init__(xapp_handler, logger, server)
        self.xapp_name = xapp_name
        self.rmr_port = rmr_port
        self.http_port = http_port
        self.pltnamespace = pltnamespace
        self.app_namespace = app_namespace

        self.dapp_function_def_wrapper = dappfuncdef.DAppFunctionDefWrapper(hex="")
     
    def get_ran_function_description(self, json_ran_info):
        """
        Get decoded ran function description
        Parameters:
        ----------
        json_ran_info (json obj): json object obtained when by the get_ran_info function

        """
        if not json_ran_info:
            self.logger.info("[DAppSyncBase] json_ran_info object None value not admitted!")
            return

        for ran_func in json_ran_info["gnb"]["ranFunctions"]: 
            if ran_func["ranFunctionId"] == 255:
                # selecting rc action
                ran_function_definition = ran_func["ranFunctionDefinition"]
                break
        self.logger.info(ran_function_definition)
        # Decoding RAN function Definition
        self.dapp_function_def_wrapper.set_hex(hex=ran_function_definition)
        
        func_def_obj = self.dapp_function_def_wrapper.decode()
        
        return func_def_obj