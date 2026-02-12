import ctypes

class e2sm_dapp_act_def_format_e(ctypes.c_uint):
    FORMAT_0_E2SM_DAPP_ACT_DEF = 0
    END_E2SM_DAPP_ACT_DEF = 1

class e2sm_dapp_ind_hdr_format_e(ctypes.c_uint):
    FORMAT_0_E2SM_DAPP_IND_HDR = 0
    END_E2SM_DAPP_IND_HDR = 1

class e2sm_dapp_ev_trigger_format_e(ctypes.c_uint):
    FORMAT_0_E2SM_DAPP_EV_TRIGGER_FORMAT = 0
    END_E2SM_DAPP_EV_TRIGGER_FORMAT = 1

class e2sm_dapp_ind_msg_format_e(ctypes.c_uint):
    FORMAT_0_E2SM_DAPP_IND_MSG = 0
    END_E2SM_DAPP_IND_MSG = 1

class dapp_e3_sm_type_e(ctypes.c_uint):
    DAPP_E3_SM_NONE = 0
    DAPP_E3_SM_SPECTRUM = 1

class e2sm_dapp_ctrl_hdr_e(ctypes.c_uint):
    FORMAT_0_E2SM_DAPP_CTRL_HDR = 0
    END_E2SM_DAPP_CTRL_HDR = 1

class e2sm_dapp_ctrl_msg_e(ctypes.c_uint):
    FORMAT_0_E2SM_DAPP_CTRL_MSG = 0
    END_E2SM_DAPP_CTRL_MSG = 1

class e2sm_dapp_ctrl_out_e(ctypes.c_uint):
    FORMAT_0_E2SM_DAPP_CTRL_OUT = 0
    END_E2SM_DAPP_CTRL_OUT = 1