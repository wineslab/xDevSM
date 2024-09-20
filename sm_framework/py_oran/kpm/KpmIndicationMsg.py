import ctypes
from sm_framework.py_oran.ByteArray import ByteArray
from sm_framework.py_oran.kpm.enums import *
from sm_framework.lib.library_wrapper import wrapper, kpm_lib, wrap_functions
from mdclogpy import Logger


measurements_ids  = ['RRU.PrbTotUl', 
                    'DRB.UEThpDl', 'RRC.ConnEstabAtt.mo-VideoCall', 'RRC.ConnEstabSucc.mo-VoiceCall', 'RRU.PrbAvailDl', 
                    'DRB.RlcSduTransmittedVolumeUL_Filter', 'DRB.PdcpSduVolumeUL', 'RRC.ConnMean', 'DRB.PerDataVolumeDLDist.Bin', 'RRU.PrbUsedUl',
                    'DRB.RlcSduTransmittedVolumeDL_Filter', 'RRC.timingAdvance', 
                    'RRC.ConnEstabSucc.mo-VideoCall','DRB.PerDataVolumeULDist.Bin', 'RRC.ConnMax',
                    'DRB.UEThpUl', 'DRB.PdcpSduVolumeDL',  'RRU.PrbUsedDl', 'RRC.ConnEstabSucc.mo-Data', 'DRB.UECqiDl', 
                    'DRB.UECqiUl', 'RRC.ConnEstabAtt.mo-VoiceCall', 
                    'RRU.PrbTotDl', 'RRU.PrbAvailUl', 'RRC.ConnEstabAtt.mo-Data', 
                    'RRC.ConnEstabFailCause.NetworkReject', 
                    'DRB.PacketLossRateULDist', 'DRB.PacketSuccessRateUlgNBUu', 'DRB.RlcPacketDropRateDl', 'DRB.RlcSduTransmittedVolumeDL', 'DRB.RlcSduTransmittedVolumeUL']

class meas_record_lst_t(ctypes.Structure):
    class Union(ctypes.Union):
        _fields_ = [
            ("int_val", ctypes.c_uint32),
            ("real_val", ctypes.c_double),
            ("no_value", ctypes.c_void_p)
        ]

    _fields_ = [
        ("value", meas_value_e),  # meas_value_e
        ("union", Union)
    ]

class meas_data_lst_t(ctypes.Structure):
    _fields_ = [
        ("meas_record_len", ctypes.c_size_t),
        ("meas_record_lst", ctypes.POINTER(meas_record_lst_t)),
        ("incomplete_flag", ctypes.POINTER(enum_value_e))
    ]

class meas_type_union(ctypes.Union):
    _fields_ = [
        ("name", ByteArray),  
        ("id", ctypes.c_uint16)
    ]

class meas_type_t(ctypes.Structure):
    _fields_ = [
        ("type", meas_type_enum),
        ("value", meas_type_union)
        ]
    
class e2sm_plmn_t(ctypes.Structure):
    _fields_ = [
        ("mcc", ctypes.c_uint16),
        ("mnc", ctypes.c_uint16),
        ("mnc_digit_len", ctypes.c_uint8)
    ]

class s_nssai_e2sm_t(ctypes.Structure):
    _fields_ = [
        ("sST", ctypes.c_uint8),
        ("sD", ctypes.POINTER(ctypes.c_uint32))
    ]

class label_info_lst_t(ctypes.Structure):
    _fields_ = [
        ("noLabel", ctypes.POINTER(enum_value_e)),  # OPTIONAL
        ("plmn_id", ctypes.POINTER(e2sm_plmn_t)),    # OPTIONAL
        ("sliceID", ctypes.POINTER(s_nssai_e2sm_t)),  # OPTIONAL
        ("fiveQI", ctypes.POINTER(ctypes.c_uint8)),          # OPTIONAL
        ("qFI", ctypes.POINTER(ctypes.c_uint8)),             # OPTIONAL, INTEGER (0..63, …)
        ("qCI", ctypes.POINTER(ctypes.c_uint8)),             # OPTIONAL
        ("qCImax", ctypes.POINTER(ctypes.c_uint8)),          # OPTIONAL
        ("qCImin", ctypes.POINTER(ctypes.c_uint8)),          # OPTIONAL
        ("aRPmax", ctypes.POINTER(ctypes.c_uint8)),          # OPTIONAL, INTEGER (1.. 15, …)
        ("aRPmin", ctypes.POINTER(ctypes.c_uint8)),          # OPTIONAL, INTEGER (1.. 15, …)
        ("bitrateRange", ctypes.POINTER(ctypes.c_uint16)),   # OPTIONAL
        ("layerMU_MIMO", ctypes.POINTER(ctypes.c_uint16)),   # OPTIONAL
        ("sUM", ctypes.POINTER(enum_value_e)),        # OPTIONAL
        ("distBinX", ctypes.POINTER(ctypes.c_uint16)),       # OPTIONAL
        ("distBinY", ctypes.POINTER(ctypes.c_uint16)),       # OPTIONAL
        ("distBinZ", ctypes.POINTER(ctypes.c_uint16)),       # OPTIONAL
        ("preLabelOverride", ctypes.POINTER(enum_value_e)),  # OPTIONAL
        ("startEndInd", ctypes.POINTER(start_end_ind_e)),   # OPTIONAL
        ("min", ctypes.POINTER(enum_value_e)),             # OPTIONAL
        ("max", ctypes.POINTER(enum_value_e)),             # OPTIONAL
        ("avg", ctypes.POINTER(enum_value_e)),             # OPTIONAL
        ("ssbIndex", ctypes.POINTER(ctypes.c_uint16)),            # OPTIONAL
        ("nonGoB_beamformModeIndex", ctypes.POINTER(ctypes.c_uint16)),  # OPTIONAL
        ("mimoModeIndex", ctypes.POINTER(ctypes.c_uint8)),       # OPTIONAL, 1 = SU-MIMO, 2 = MU-MIMO
    ]

class meas_info_format_1_lst_t(ctypes.Structure):
    _fields_ = [
        ("meas_type", meas_type_t),
        ("label_info_lst_len", ctypes.c_size_t),      # [1, 2147483647]
        ("label_info_lst", ctypes.POINTER(label_info_lst_t))  # 8.3.11
    ]


class test_cond_value_t(ctypes.Structure):
    class Union(ctypes.Union):
        _fields_ = [
            ("int_value", ctypes.POINTER(ctypes.c_int64)),
            ("enum_value", ctypes.POINTER(ctypes.c_int64)),
            ("bool_value", ctypes.POINTER(ctypes.c_bool)),
            ("bit_string_value", ctypes.POINTER(ByteArray)),
            ("octet_string_value", ctypes.POINTER(ByteArray)),
            ("printable_string_value", ctypes.POINTER(ByteArray)),
            ("real_value", ctypes.POINTER(ctypes.c_double))
        ]

    _fields_ = [
        ("type", test_cond_value_e),  # 8.3.23, OPTIONAL
        ("union", Union)  # Union inside the structure
    ]

class test_info_lst_t(ctypes.Structure):
    class Union(ctypes.Union):
        _fields_ = [
            ("GBR", cond_type_e),
            ("AMBR", cond_type_e),
            ("IsStat", cond_type_e),
            ("IsCatM", cond_type_e),
            ("DL_RSRP", cond_type_e),
            ("DL_RSRQ", cond_type_e),
            ("UL_RSRP", cond_type_e),
            ("CQI", cond_type_e),
            ("fiveQI", cond_type_e),
            ("QCI", cond_type_e),
            ("S_NSSAI", cond_type_e)
        ]

    _fields_ = [
        ("test_cond_type", test_cond_type_e),
        ("union", Union),  # Union inside the structure
        ("test_cond", ctypes.POINTER(test_cond_e)),  # OPTIONAL
        ("test_cond_value", ctypes.POINTER(test_cond_value_t))  # 8.3.23, OPTIONAL
    ]

# Define the matching_condition_format_3_lst_t structure
class matching_condition_format_3_lst_t(ctypes.Structure):
    class cond_union(ctypes.Union):
        _fields_ = [
            ("label_info_lst", label_info_lst_t),  # 8.3.11
            ("test_info_lst", test_info_lst_t)     # 8.3.22
        ]

    _fields_ = [
        ("cond_type", ctypes.c_uint),  # Enum to represent the type of condition
        ("union", cond_union),  # Union to accommodate different condition types
        ("logical_OR", ctypes.POINTER(enum_value_e))  # OPTIONAL, 8.3.25
    ]

    # Constants for enum values
    LABEL_INFO = 0
    TEST_INFO = 1
    END_INFO = 2

class guami_t(ctypes.Structure):
    _fields_ = [
        ("plmn_id", e2sm_plmn_t),
        ("amf_region_id", ctypes.c_uint8),  
        ("amf_set_id", ctypes.c_uint16, 10),  
        ("amf_ptr", ctypes.c_uint16, 6)       
    ]

class e2ap_gnb_id_t(ctypes.Structure):
    _fields_ = [
        ("nb_id", ctypes.c_uint32),
        ("unused", ctypes.c_uint32)
    ]

# Define the global_gnb_id_t structure
class global_gnb_id_t(ctypes.Structure):
    class Union(ctypes.Union):
        _fields_ = [
            ("gnb_id", e2ap_gnb_id_t)
        ]
    
    _fields_ = [
        ("plmn_id", e2sm_plmn_t),
        ("type", gnb_type_id_e),
        ("union", Union)
    ]

# Define the global_ng_enb_id_t structure
class global_ng_enb_id_t(ctypes.Structure):
    class Union(ctypes.Union):
        _fields_ = [
            ("macro_ng_enb_id", ctypes.c_uint32),
            ("short_macro_ng_enb_id", ctypes.c_uint32),
            ("long_macro_ng_enb_id", ctypes.c_uint32)
        ]
    
    _fields_ = [
        ("plmn_id", e2sm_plmn_t),
        ("type", ng_enb_type_id_e),
        ("union", Union)
    ]

class global_ng_ran_node_id_t(ctypes.Structure):
    class Union(ctypes.Union):
        _fields_ = [
            ("global_gnb_id", global_gnb_id_t),    # 6.2.3.3
            ("global_ng_enb_id", global_ng_enb_id_t)   # 6.2.3.8
        ]

    _fields_ = [
        ("type", ng_ran_node_type_id_e),
        ("union", Union)
    ]

class gnb_e2sm_t(ctypes.Structure):
    _fields_ = [
        ("amf_ue_ngap_id", ctypes.c_uint64),  # AMF UE NGAP ID
        ("guami", guami_t),             # GUAMI
        ("gnb_cu_ue_f1ap_lst_len", ctypes.c_size_t),  # gNB-CU UE F1AP ID List length
        ("gnb_cu_ue_f1ap_lst", ctypes.POINTER(ctypes.c_uint32)),  # gNB-CU UE F1AP ID List
        ("gnb_cu_cp_ue_e1ap_lst_len", ctypes.c_size_t),  # gNB-CU-CP UE E1AP ID List length
        ("gnb_cu_cp_ue_e1ap_lst", ctypes.POINTER(ctypes.c_uint32)),  # gNB-CU-CP UE E1AP ID List
        ("ran_ue_id", ctypes.POINTER(ctypes.c_uint64)),  # RAN UE ID (Optional)
        ("ng_ran_node_ue_xnap_id", ctypes.POINTER(ctypes.c_uint32)),  # M-NG-RAN node UE XnAP ID
        ("global_gnb_id", ctypes.POINTER(global_gnb_id_t)),  # Global gNB ID (Optional)
        ("global_ng_ran_node_id", ctypes.POINTER(global_ng_ran_node_id_t))  # Global NG-RAN Node ID
    ]

class gnb_du_e2sm_t(ctypes.Structure):
    _fields_ = [
        ("gnb_cu_ue_f1ap", ctypes.c_uint32),  # 6.2.3.21
        ("ran_ue_id", ctypes.POINTER(ctypes.c_uint64))  # 6.2.3.25, OPTIONAL
    ]

class gnb_cu_up_e2sm_t(ctypes.Structure):
    _fields_ = [
        ("gnb_cu_cp_ue_e1ap", ctypes.c_uint32),  # 6.2.3.20
        ("ran_ue_id", ctypes.POINTER(ctypes.c_uint64))  # 6.2.3.25, OPTIONAL
    ]

class ng_enb_e2sm_t(ctypes.Structure):
    _fields_ = [
        ("amf_ue_ngap_id", ctypes.c_uint64),  # 6.2.3.16
        ("guami", guami_t),  # 6.2.3.17 
        ("ng_enb_cu_ue_w1ap_id", ctypes.POINTER(ctypes.c_uint32)),  # 6.2.3.22
        ("ng_ran_node_ue_xnap_id", ctypes.POINTER(ctypes.c_uint32)),  # 6.2.3.19
        ("global_ng_enb_id", ctypes.POINTER(global_ng_enb_id_t)),  # OPTIONAL
        ("global_ng_ran_node_id", ctypes.POINTER(global_ng_ran_node_id_t))  # Global NG-RAN Node ID
    ]

class ng_enb_du_e2sm_t(ctypes.Structure):
    _fields_ = [
        ("ng_enb_cu_ue_w1ap_id", ctypes.c_uint32)  # 6.2.3.22
    ]

class global_enb_id_t(ctypes.Structure):
    class Union(ctypes.Union):
        _fields_ = [
            ("macro_enb_id", ctypes.c_uint32),          # BIT STRING (SIZE(20))
            ("home_enb_id", ctypes.c_uint32),           # BIT STRING (SIZE(28))
            ("short_macro_enb_id", ctypes.c_uint32),    # BIT STRING (SIZE(18))
            ("long_macro_enb_id", ctypes.c_uint32)      # BIT STRING (SIZE(21))
        ]

    _fields_ = [
        ("plmn_id", e2sm_plmn_t),
        ("type", enb_type_id_e),
        ("union", Union)
    ]

class en_gnb_e2sm_t(ctypes.Structure):
    _fields_ = [
        ("enb_ue_x2ap_id", ctypes.c_uint16),  # 6.2.3.23
        ("enb_ue_x2ap_id_extension", ctypes.POINTER(ctypes.c_uint16)),  # 6.2.3.24, OPTIONAL
        ("global_enb_id", global_enb_id_t),  # 6.2.3.9
        ("gnb_cu_ue_f1ap_lst", ctypes.POINTER(ctypes.c_uint32)),  # 6.2.3.21
        ("gnb_cu_cp_ue_e1ap_lst_len", ctypes.c_size_t),  # 6.2.3.20
        ("gnb_cu_cp_ue_e1ap_lst", ctypes.POINTER(ctypes.c_uint32)),  # 6.2.3.20
        ("ran_ue_id", ctypes.POINTER(ctypes.c_uint64))  # 6.2.3.25, OPTIONAL
    ]

class e2sm_gummei_t(ctypes.Structure):
    _fields_ = [
        ("plmn_id", e2sm_plmn_t),   # e2sm_plmn_t
        ("mme_group_id", ctypes.c_uint16),  # uint16_t
        ("mme_code", ctypes.c_uint8)        # uint8_t
    ]

class enb_e2sm_t(ctypes.Structure):
    _fields_ = [
        ("mme_ue_s1ap_id", ctypes.c_uint32),  # 6.2.3.26
        ("gummei", e2sm_gummei_t),            # 6.2.3.18
        ("enb_ue_x2ap_id", ctypes.POINTER(ctypes.c_uint16)),  # 6.2.3.23, C-ifDCSetup
        ("enb_ue_x2ap_id_extension", ctypes.POINTER(ctypes.c_uint16)),  # 6.2.3.24, C-ifDCSetup
        ("global_enb_id", ctypes.POINTER(global_enb_id_t))  # 6.2.3.9, C-ifDCSetup
    ]


class ue_id_e2sm_t(ctypes.Structure):
    class Union(ctypes.Union):
        _fields_ = [
            ("gnb", gnb_e2sm_t),
            ("gnb_du", gnb_du_e2sm_t),
            ("gnb_cu_up", gnb_cu_up_e2sm_t),
            ("ng_enb", ng_enb_e2sm_t),
            ("ng_enb_du", ng_enb_du_e2sm_t),
            ("en_gnb", en_gnb_e2sm_t),
            ("enb", enb_e2sm_t)
        ]

    _fields_ = [
        ("type", ue_id_e2sm_e),
        ("union", Union)
    ]

class ue_lst_t(ctypes.Structure):
    _fields_ = [
        ("ue_lst_len", ctypes.c_size_t),  # size_t
        ("ue_lst", ctypes.POINTER(ue_id_e2sm_t))  # ue_id_e2sm_t*
    ]

class ue_id_gran_period_lst_t(ctypes.Structure):
    class Union(ctypes.Union):
        _fields_ = [
            ("no_matched_ue", enum_value_e),  # enum_value_e
            ("matched_ue_lst", ue_lst_t)  # ue_lst_t
        ]

    _fields_ = [
        ("num_matched_ue", matched_ue_e),  # matched_ue_e
        ("union", Union)  # union inside the structure
    ]


class meas_info_cond_ue_lst_t(ctypes.Structure):
    _fields_ = [
        ("meas_type", meas_type_t),  # meas_type_t
        ("matching_cond_lst_len", ctypes.c_size_t),  # size_t
        ("matching_cond_lst", ctypes.POINTER(matching_condition_format_3_lst_t)),  # matching_condition_format_3_lst_t*
        ("ue_id_matched_lst_len", ctypes.c_size_t),  # size_t
        ("ue_id_matched_lst", ctypes.POINTER(ue_id_e2sm_t)),  # ue_id_e2sm_t*
        ("ue_id_gran_period_lst_len", ctypes.c_size_t),  # size_t
        ("ue_id_gran_period_lst", ctypes.POINTER(ue_id_gran_period_lst_t)),  # ue_id_gran_period_lst_t*
    ]


class kpm_ind_msg_format_1_t(ctypes.Structure):
    _fields_ = [
        ("meas_data_lst_len", ctypes.c_size_t),         # [1, 65535]
        ("meas_data_lst", ctypes.POINTER(meas_data_lst_t)),
        ("meas_info_lst_len", ctypes.c_size_t),         # [0, 65535]
        ("meas_info_lst", ctypes.POINTER(meas_info_format_1_lst_t)),  # OPTIONAL, meas_info_lst_len can be zero
        ("gran_period_ms", ctypes.POINTER(ctypes.c_uint32))    # 8.3.8 - OPTIONAL
    ]

class kpm_ind_msg_format_2_t(ctypes.Structure):
    _fields_ = [
        ("meas_data_lst_len", ctypes.c_size_t),  # size_t
        ("meas_data_lst", ctypes.POINTER(meas_data_lst_t)),  # meas_data_lst_t*
        ("meas_info_cond_ue_lst_len", ctypes.c_size_t),  # size_t
        ("meas_info_cond_ue_lst", ctypes.POINTER(meas_info_cond_ue_lst_t)),  # meas_info_cond_ue_lst_t*
        ("gran_period_ms", ctypes.POINTER(ctypes.c_uint32))  # uint32_t*
    ]

class meas_report_per_ue_t(ctypes.Structure):
    _fields_ = [
        ("ue_meas_report_lst", ue_id_e2sm_t),  # ue_id_e2sm_t
        ("ind_msg_format_1", kpm_ind_msg_format_1_t)  # kpm_ind_msg_format_1_t
    ]

class kpm_ind_msg_format_3_t(ctypes.Structure):
    _fields_ = [
        ("ue_meas_report_lst_len", ctypes.c_size_t),  # size_t
        ("meas_report_per_ue", ctypes.POINTER(meas_report_per_ue_t))  # meas_report_per_ue_t*
    ]


class KpmIndMsg(ctypes.Structure):
    class Union(ctypes.Union):
        _fields_ = [
            ("frm_1", kpm_ind_msg_format_1_t),  # kpm_ind_msg_format_1_t
            ("frm_2", kpm_ind_msg_format_2_t),  # kpm_ind_msg_format_2_t
            ("frm_3", kpm_ind_msg_format_3_t)   # kpm_ind_msg_format_3_t
        ]

    _fields_ = [
        ("type", format_ind_msg_e),  # format_ind_msg_e
        ("data", Union) 
    ]

    def print_gran_period_ms(self):
        # Check the type field to determine the format
        if self.type.value == format_ind_msg_e.FORMAT_1_INDICATION_MESSAGE:  # Assuming 0 is FORMAT_1_INDICATION_MESSAGE
            if self.data.frm_1.gran_period_ms:
                print(self.data.frm_1.gran_period_ms.contents.value)
            else:
                print("gran_period_ms is not set for format 1.")
        elif self.type.value == format_ind_msg_e.FORMAT_2_INDICATION_MESSAGE:  # Assuming 1 is FORMAT_2_INDICATION_MESSAGE
            if self.data.frm_2.gran_period_ms:
                print(self.data.frm_2.gran_period_ms.contents.value)
            else:
                print("gran_period_ms is not set for format 2.")
        elif self.type.value == format_ind_msg_e.FORMAT_3_INDICATION_MESSAGE:  # Assuming 2 is FORMAT_3_INDICATION_MESSAGE
            for i in range(self.data.frm_3.ue_meas_report_lst_len):
                ind_msg_format_1 = self.data.frm_3.meas_report_per_ue[i].ind_msg_format_1
                if ind_msg_format_1.gran_period_ms:
                    print(f"gran_period_ms for UE {i}: {ind_msg_format_1.gran_period_ms.contents.value}")
                else:
                    print(f"gran_period_ms is not set for UE {i}.")
        else:
            print("Unknown format type.")
    
    def print_meas_info(self, logger: Logger):
        
        # print("~~~~~~~~~~ DATA FROM {} ~~~~~~~~~~".format(gnb_inventory_name))

        if self.type.value == format_ind_msg_e.FORMAT_1_INDICATION_MESSAGE:
            logger.debug("received indication message format 1")
            for i in range(self.data.frm_1.meas_data_lst_len):
                logger.debug("printing info regarding ue[{}]".format(i))
                meas_data_lst = self.data.frm_1.meas_data_lst
                for k in range(meas_data_lst[i].meas_record_len):
                    meas_record_lst_el = meas_data_lst[i].meas_record_lst[k]
                    if self.data.frm_1.meas_info_lst[k].meas_type.type.value == meas_type_enum.NAME_MEAS_TYPE:
                        self.log_values(logger, self.data.frm_1.meas_info_lst[k].meas_type.value.name, meas_record_lst_el, type=meas_record_lst_el.value.value)

                    elif self.data.frm_1.meas_info_lst[k].meas_type.type.value == meas_type_enum.ID_MEAS_TYPE:
                        self.log_values_id(logger, self.data.frm_1.meas_info_lst[k].meas_type.value.id, meas_record_lst_el)
                    
                    else:
                        logger.info("Not supported meas type {}".format(self.data.frm_1.meas_info_lst[k].meas_type.type.value))

        elif self.type.value == format_ind_msg_e.FORMAT_2_INDICATION_MESSAGE:
            logger.debug("received indication message format 2 - not supported yet")
        elif self.type.value == format_ind_msg_e.FORMAT_3_INDICATION_MESSAGE:
            logger.debug("received indication message format 3")
            for i in range(self.data.frm_3.ue_meas_report_lst_len):
                logger.debug("printing info regarding ue[{}]".format(i))
                ind_msg_format_1 = self.data.frm_3.meas_report_per_ue[i].ind_msg_format_1

                for j in range(ind_msg_format_1.meas_data_lst_len):
                    meas_data_lst = ind_msg_format_1.meas_data_lst
                    # logger.debug("~~~~~~~~~~ MEAS INFO data: {} ~~~~~~~~~~".format(j))
                    # print(meas_data_lst[j].meas_record_len)
                    for k in range(meas_data_lst[j].meas_record_len):
                        meas_record_lst_el = meas_data_lst[j].meas_record_lst[k]
                        if ind_msg_format_1.meas_info_lst[k].meas_type.type.value == meas_type_enum.NAME_MEAS_TYPE:
                            self.log_values(logger, ind_msg_format_1.meas_info_lst[k].meas_type.value.name, meas_record_lst_el, type=meas_record_lst_el.value.value)
                        else:
                            logger.info("Not supported meas type {}".format(ind_msg_format_1.meas_info_lst[k].meas_type.type.value))

    def log_values(self, logger: Logger, byte_array: ByteArray, meas_record: meas_record_lst_t, type=meas_value_e.INTEGER_MEAS_VALUE):
        printed = False
        for value in measurements_ids:
            if byte_array.cmp_str_ba(value):
                if type == meas_value_e.INTEGER_MEAS_VALUE:
                    logger.info("{}: {}".format(value,meas_record.union.int_val))
                    printed = True
                elif type == meas_value_e.REAL_MEAS_VALUE:
                    logger.info("{}: {}".format(value,meas_record.union.real_val))
                    printed = True

        
        if not printed:
            logger.info("Measurement Id not yet supported")

    def log_values_real(self, logger: Logger, byte_array: ByteArray, meas_record: meas_record_lst_t):
        printed = False
        for value in measurements_ids:
            if byte_array.cmp_str_ba(value):
                logger.info("{}: {}".format(value,meas_record.union.real_val))
                printed = True
                break
        
        if not printed:
            logger.info("Measurement Id not yet supported")
    
    def log_values_id(self, logger: Logger, byte_array, meas_record: meas_record_lst_t):
        logger.info("received id value - not supported yet: {}".format(byte_array))

class KpmIndMsgWrapper():
    # Manager for decoding and memory deallocation
    def __init__(self, byte_array: ByteArray):
        self.kpm_ind_msg: KpmIndMsg = None
        self.byte_array = byte_array
        self.free = wrap_functions(kpm_lib, 'free_kpm_ind_msg', None, [ctypes.POINTER(KpmIndMsg)])
        self.decode_indication_msg = wrap_functions(kpm_lib, 'kpm_dec_ind_msg_asn', KpmIndMsg, [ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint8)])

    def decode(self) -> KpmIndMsg:
        self.kpm_ind_msg = self.decode_indication_msg(len(self.byte_array), self.byte_array)
        return self.kpm_ind_msg

    def __del__(self):
        self.free(self.kpm_ind_msg)
