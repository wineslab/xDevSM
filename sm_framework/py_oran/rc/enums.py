import ctypes


class ran_parameter_def_type_e(ctypes.c_uint):
    LIST_RAN_PARAMETER_DEF_TYPE = 0
    STRUCTURE_RAN_PARAMETER_DEF_TYPE = 1
    END_RAN_PARAMETER_DEF_TYPE = 2


class e2sm_rc_ctrl_hdr_e(ctypes.c_uint):
  FORMAT_1_E2SM_RC_CTRL_HDR = 0
  FORMAT_2_E2SM_RC_CTRL_HDR = 1
  END_E2SM_RC_CTRL_HDR = 2 


class gnb_type_id_e(ctypes.c_uint):
    GNB_TYPE_ID = 0
    END_TYPE_ID = 1


class ng_enb_type_id_e(ctypes.c_int):
    MACRO_NG_ENB_TYPE_ID = 0
    SHORT_MACRO_NG_ENB_TYPE_ID = 1
    LONG_MACRO_NG_ENB_TYPE_ID = 2

    END_NG_ENB_TYPE_ID = 3

class ng_ran_node_type_id_e(ctypes.c_int):
    GNB_GLOBAL_TYPE_ID = 0
    NG_ENB_GLOBAL_TYPE_ID = 1

    END_GLOBAL_TYPE_ID = 2

class enb_type_id_e(ctypes.c_int):
    MACRO_ENB_TYPE_ID = 0
    HOME_ENB_TYPE_ID = 1
    SHORT_MACRO_ENB_TYPE_ID = 2
    LONG_MACRO_ENB_TYPE_ID = 3

    END_ENB_TYPE_ID = 4

class ue_id_e2sm_e(ctypes.c_int):
    GNB_UE_ID_E2SM = 0
    GNB_DU_UE_ID_E2SM = 1
    GNB_CU_UP_UE_ID_E2SM = 2
    NG_ENB_UE_ID_E2SM = 3
    NG_ENB_DU_UE_ID_E2SM = 4
    EN_GNB_UE_ID_E2SM = 5
    ENB_UE_ID_E2SM = 6
    
    END_UE_ID_E2SM = 7

class ric_ctrl_decision_e(ctypes.c_int):
    ACCEPT_RIC_CTRL_DECISION = 0 
    REJECT_RIC_CTRL_DECISION = 1

    END_RIC_CTRL_DECISION = 2

class ric_ctrl_dec_ctrl_hdr_frmt_2_e(ctypes.c_int):
    ACCEPT_RIC_CTRL_DEC_CTRL_HDR_FRMT_2 = 0 
    REJECT_RIC_CTRL_DEC_CTRL_HDR_FRMT_2 = 1

    END_RIC_CTRL_DEC_CTRL_HDR_FRMT_2 = 3

class e2sm_rc_ctrl_hdr_e(ctypes.c_int):
    FORMAT_1_E2SM_RC_CTRL_HDR = 0
    FORMAT_2_E2SM_RC_CTRL_HDR = 1
    
    END_E2SM_RC_CTRL_HDR = 2

class ran_parameter_val_type_e(ctypes.c_int):
    ELEMENT_KEY_FLAG_TRUE_RAN_PARAMETER_VAL_TYPE = 0
    ELEMENT_KEY_FLAG_FALSE_RAN_PARAMETER_VAL_TYPE = 1
    STRUCTURE_RAN_PARAMETER_VAL_TYPE = 2
    LIST_RAN_PARAMETER_VAL_TYPE = 3

    END_RAN_PARAMETER_VAL_TYPE = 4

class ran_parameter_value_e(ctypes.c_int):
    BOOLEAN_RAN_PARAMETER_VALUE = 0
    INTEGER_RAN_PARAMETER_VALUE = 1
    REAL_RAN_PARAMETER_VALUE = 2
    BIT_STRING_RAN_PARAMETER_VALUE = 3
    OCTET_STRING_RAN_PARAMETER_VALUE = 4
    PRINTABLESTRING_RAN_PARAMETER_VALUE = 5

    END_RAN_PARAMETER_VALUE = 6

class e2sm_rc_ctrl_msg_e(ctypes.c_int):
    FORMAT_1_E2SM_RC_CTRL_MSG = 0
    FORMAT_2_E2SM_RC_CTRL_MSG = 1

    END_E2SM_RC_CTRL_MSG = 2