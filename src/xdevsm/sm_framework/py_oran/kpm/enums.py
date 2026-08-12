import ctypes

class enum_value_e(ctypes.c_uint):
    TRUE_ENUM_VALUE = 0
    END_ENUM_VALUE = 1

class meas_value_e(ctypes.c_uint):
    INTEGER_MEAS_VALUE = 0
    REAL_MEAS_VALUE = 1
    NO_VALUE_MEAS_VALUE = 2
    END_MEAS_VALUE = 3

class start_end_ind_e(ctypes.c_uint):
    START_IND = 0
    END_IND = 1
    END_START_END_IND = 2

class test_cond_type_e(ctypes.c_uint):
    GBR_TEST_COND_TYPE = 0
    AMBR_TEST_COND_TYPE = 1
    IsStat_TEST_COND_TYPE = 2
    IsCatM_TEST_COND_TYPE = 3
    DL_RSRP_TEST_COND_TYPE = 4
    DL_RSRQ_TEST_COND_TYPE = 5
    UL_RSRP_TEST_COND_TYPE = 6
    CQI_TEST_COND_TYPE = 7
    fiveQI_TEST_COND_TYPE = 8
    QCI_TEST_COND_TYPE = 9
    S_NSSAI_TEST_COND_TYPE = 10
    END_TEST_COND_TYPE_KPM_V2_01 = 11


class cond_type_e(ctypes.c_uint):
    TRUE_TEST_COND_TYPE = 0
    END_COND_TYPE_KPM_V2_01 = 1

class test_cond_e(ctypes.c_uint):
    EQUAL_TEST_COND = 0
    GREATERTHAN_TEST_COND = 1
    LESSTHAN_TEST_COND = 2
    CONTAINS_TEST_COND = 3
    PRESENT_TEST_COND = 4
    END_TEST_COND = 5

class test_cond_value_e(ctypes.c_uint):
    INTEGER_TEST_COND_VALUE = 0
    ENUMERATED_TEST_COND_VALUE = 1
    BOOLEAN_TEST_COND_VALUE = 2
    BIT_STRING_TEST_COND_VALUE = 3
    OCTET_STRING_TEST_COND_VALUE = 4
    PRINTABLE_STRING_TEST_COND_VALUE = 5
    REAL_TEST_COND_VALUE = 6
    END_TEST_COND_VALUE = 7

class ue_id_e2sm_e(ctypes.c_uint):
    GNB_UE_ID_E2SM = 0
    GNB_DU_UE_ID_E2SM = 1
    GNB_CU_UP_UE_ID_E2SM = 2
    NG_ENB_UE_ID_E2SM = 3
    NG_ENB_DU_UE_ID_E2SM = 4
    EN_GNB_UE_ID_E2SM = 5
    ENB_UE_ID_E2SM = 6
    END_UE_ID_E2SM = 7

class ng_enb_type_id_e(ctypes.c_uint):
    MACRO_NG_ENB_TYPE_ID = 0
    SHORT_MACRO_NG_ENB_TYPE_ID = 1
    LONG_MACRO_NG_ENB_TYPE_ID = 2
    END_NG_ENB_TYPE_ID = 3

class gnb_type_id_e(ctypes.c_uint):
    GNB_TYPE_ID = 0
    END_TYPE_ID = 1

class ng_ran_node_type_id_e(ctypes.c_uint):
    GNB_GLOBAL_TYPE_ID = 0
    NG_ENB_GLOBAL_TYPE_ID = 1
    END_GLOBAL_TYPE_ID = 2

class enb_type_id_e(ctypes.c_uint):
    MACRO_ENB_TYPE_ID = 0
    HOME_ENB_TYPE_ID = 1
    SHORT_MACRO_ENB_TYPE_ID = 2
    LONG_MACRO_ENB_TYPE_ID = 3
    END_ENB_TYPE_ID = 4

class matched_ue_e(ctypes.c_uint):
    NONE_MATCHED_UE = 0
    ONE_OR_MORE_MATCHED_UE = 1
    END_MATCHED_UE = 2

class format_ind_msg_e(ctypes.c_uint):
    FORMAT_1_INDICATION_MESSAGE = 0
    FORMAT_2_INDICATION_MESSAGE = 1
    FORMAT_3_INDICATION_MESSAGE = 2
    END_INDICATION_MESSAGE = 3

class meas_type_enum(ctypes.c_int):
    NAME_MEAS_TYPE = 0
    ID_MEAS_TYPE = 1
    END_MEAS_TYPE = 2

class format_action_def_e(ctypes.c_int):
    FORMAT_1_ACTION_DEFINITION = 0
    FORMAT_2_ACTION_DEFINITION = 1
    FORMAT_3_ACTION_DEFINITION = 2
    FORMAT_4_ACTION_DEFINITION = 3
    FORMAT_5_ACTION_DEFINITION = 4

    END_ACTION_DEFINITION = 5