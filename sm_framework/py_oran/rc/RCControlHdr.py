import ctypes
from sm_framework.py_oran.kpm.KpmIndicationMsg import ue_id_e2sm_t, e2sm_plmn_t
from sm_framework.py_oran.rc.enums import * 

class e2ap_gnb_id_t(ctypes.Structure):
    _fields_ = [
        ("nb_id", ctypes.c_uint32),   # uint32_t nb_id
        ("unused", ctypes.c_uint32)  # uint32_t unused
    ]

# class e2sm_plmn_t(ctypes.Structure):
#     _fields_ = [
#         ("mcc", ctypes.c_uint16),         # uint16_t mcc
#         ("mnc", ctypes.c_uint16),         # uint16_t mnc
#         ("mnc_digit_len", ctypes.c_uint8) # uint8_t mnc_digit_len
#     ]


class global_gnb_id_t(ctypes.Structure):
    class e2ap_gnb_id_t_union(ctypes.Union):
        _fields_ = [
            ("gnb_id", e2ap_gnb_id_t)
        ]    
    _fields_ = [
        ("plmn_id", e2sm_plmn_t),  # e2sm_plmn_t plmn_id
        ("type", gnb_type_id_e),   # gnb_type_id_e type
        ("union", e2ap_gnb_id_t_union)
    ]


# class global_ng_enb_id_t(ctypes.Structure):
#     class _Union(ctypes.Union):
#         _fields_ = [
#             ("macro_ng_enb_id", ctypes.c_uint32),       # uint32_t macro_ng_enb_id
#             ("short_macro_ng_enb_id", ctypes.c_uint32), # uint32_t short_macro_ng_enb_id
#             ("long_macro_ng_enb_id", ctypes.c_uint32)   # uint32_t long_macro_ng_enb_id
#         ]
    
#     _fields_ = [
#         ("plmn_id", e2sm_plmn_t),        # e2sm_plmn_t plmn_id
#         ("type", ng_enb_type_id_e),      # ng_enb_type_id_e type
#         ("union", _Union)                
#     ]

# class global_ng_ran_node_id_t(ctypes.Structure):
#     class _Union(ctypes.Union):
#         _fields_ = [
#             ("global_gnb_id", global_gnb_id_t),          # global_gnb_id_t global_gnb_id
#             ("global_ng_enb_id", global_ng_enb_id_t)     # global_ng_enb_id_t global_ng_enb_id
#         ]
    
#     _fields_ = [
#         ("type", ng_ran_node_type_id_e), # ng_ran_node_type_id_e type
#         ("union", _Union)                    # Anonymous union
#     ]

class guami_t(ctypes.Structure):
    _fields_ = [
        ("plmn_id", e2sm_plmn_t),           # e2sm_plmn_t plmn_id
        ("amf_region_id", ctypes.c_uint8), # uint8_t amf_region_id
        ("amf_set_id", ctypes.c_uint16),   # uint16_t amf_set_id (not constrained to 10 bits) # FIXME
        ("amf_ptr", ctypes.c_uint16)       # uint16_t amf_ptr (not constrained to 6 bits) # FIXME
    ]

# class gnb_e2sm_t(ctypes.Structure):
#     _fields_ = [
#         ("amf_ue_ngap_id", ctypes.c_uint64),            # uint64_t amf_ue_ngap_id
#         ("guami", guami_t),                             # guami_t guami (TOBEFIXED)
#         ("gnb_cu_ue_f1ap_lst_len", ctypes.c_size_t),    # size_t gnb_cu_ue_f1ap_lst_len
#         ("gnb_cu_ue_f1ap_lst", ctypes.POINTER(ctypes.c_uint32)), # uint32_t* gnb_cu_ue_f1ap_lst
#         ("gnb_cu_cp_ue_e1ap_lst_len", ctypes.c_size_t), # size_t gnb_cu_cp_ue_e1ap_lst_len
#         ("gnb_cu_cp_ue_e1ap_lst", ctypes.POINTER(ctypes.c_uint32)), # uint32_t* gnb_cu_cp_ue_e1ap_lst
#         ("ran_ue_id", ctypes.POINTER(ctypes.c_uint64)), # uint64_t* ran_ue_id
#         ("ng_ran_node_ue_xnap_id", ctypes.POINTER(ctypes.c_uint32)), # uint32_t* ng_ran_node_ue_xnap_id
#         ("global_gnb_id", ctypes.POINTER(global_gnb_id_t)), # global_gnb_id_t* global_gnb_id
#         ("global_ng_ran_node_id", ctypes.POINTER(global_ng_ran_node_id_t)) # global_ng_ran_node_id_t* global_ng_ran_node_id
#     ]

# class gnb_du_e2sm_t(ctypes.Structure):
#     _fields_ = [
#         ("gnb_cu_ue_f1ap", ctypes.c_uint32),  # uint32_t gnb_cu_ue_f1ap
#         ("ran_ue_id", ctypes.POINTER(ctypes.c_uint64))  # uint64_t* ran_ue_id (OPTIONAL)
#     ]

# class gnb_cu_up_e2sm_t(ctypes.Structure):
#     _fields_ = [
#         ("gnb_cu_cp_ue_e1ap", ctypes.c_uint32),  # uint32_t gnb_cu_cp_ue_e1ap
#         ("ran_ue_id", ctypes.POINTER(ctypes.c_uint64))  # uint64_t* ran_ue_id (OPTIONAL)
#     ]

# class ng_enb_e2sm_t(ctypes.Structure):
#     _fields_ = [
#         ("amf_ue_ngap_id", ctypes.c_uint64),               # uint64_t amf_ue_ngap_id
#         ("guami", guami_t),                                 # guami_t guami
#         ("ng_enb_cu_ue_w1ap_id", ctypes.POINTER(ctypes.c_uint32)),  # uint32_t* ng_enb_cu_ue_w1ap_id
#         ("ng_ran_node_ue_xnap_id", ctypes.POINTER(ctypes.c_uint32)),  # uint32_t* ng_ran_node_ue_xnap_id
#         ("global_ng_enb_id", ctypes.POINTER(global_ng_enb_id_t)),     # global_ng_enb_id_t* global_ng_enb_id (OPTIONAL)
#         ("global_ng_ran_node_id", ctypes.POINTER(global_ng_ran_node_id_t))  # global_ng_ran_node_id_t* global_ng_ran_node_id
#     ]

# class ng_enb_du_e2sm_t(ctypes.Structure):
#     _fields_ = [
#         ("ng_enb_cu_ue_w1ap_id", ctypes.c_uint32)  # uint32_t ng_enb_cu_ue_w1ap_id
#     ]

class global_enb_id_t(ctypes.Structure):
    _fields_ = [
        ("plmn_id", e2sm_plmn_t),                                   # e2sm_plmn_t plmn_id
        ("type", enb_type_id_e),                                      # enb_type_id_e type
        ("macro_enb_id", ctypes.c_uint32),                            # uint32_t macro_enb_id (BIT STRING (SIZE(20)))
        ("home_enb_id", ctypes.c_uint32),                             # uint32_t home_enb_id (BIT STRING (SIZE(28)))
        ("short_macro_enb_id", ctypes.c_uint32),                      # uint32_t short_macro_enb_id (BIT STRING (SIZE(18)))
        ("long_macro_enb_id", ctypes.c_uint32)                        # uint32_t long_macro_enb_id (BIT STRING (SIZE(21)))
    ]

# class en_gnb_e2sm_t(ctypes.Structure):
#     _fields_ = [
#         ("enb_ue_x2ap_id", ctypes.c_uint16),                            # uint16_t enb_ue_x2ap_id
#         ("enb_ue_x2ap_id_extension", ctypes.POINTER(ctypes.c_uint16)),  # uint16_t* enb_ue_x2ap_id_extension (OPTIONAL)
#         ("global_enb_id", global_enb_id_t),                              # global_enb_id_t global_enb_id
#         ("gnb_cu_ue_f1ap_lst", ctypes.POINTER(ctypes.c_uint32)),        # uint32_t* gnb_cu_ue_f1ap_lst
#         ("gnb_cu_cp_ue_e1ap_lst_len", ctypes.c_size_t),                  # size_t gnb_cu_cp_ue_e1ap_lst_len
#         ("gnb_cu_cp_ue_e1ap_lst", ctypes.POINTER(ctypes.c_uint32)),     # uint32_t* gnb_cu_cp_ue_e1ap_lst
#         ("ran_ue_id", ctypes.POINTER(ctypes.c_uint64))                   # uint64_t* ran_ue_id (OPTIONAL)
#     ]

# class e2sm_gummei_t(ctypes.Structure):
#     _fields_ = [
#         ("plmn_id", e2sm_plmn_t),      # e2sm_plmn_t plmn_id
#         ("mme_group_id", ctypes.c_uint16),  # uint16_t mme_group_id
#         ("mme_code", ctypes.c_uint8)       # uint8_t mme_code
#     ]

# class enb_e2sm_t(ctypes.Structure):
#     _fields_ = [
#         ("mme_ue_s1ap_id", ctypes.c_uint32),                            # uint32_t mme_ue_s1ap_id
#         ("gummei", e2sm_gummei_t),                                       # e2sm_gummei_t gummei
#         # ("enb_ue_x2ap_id", ctypes.POINTER(ctypes.c_uint16)),             # uint16_t* enb_ue_x2ap_id (OPTIONAL)
#         # ("enb_ue_x2ap_id_extension", ctypes.POINTER(ctypes.c_uint16)),   # uint16_t* enb_ue_x2ap_id_extension (OPTIONAL)
#         # ("global_enb_id", ctypes.POINTER(global_enb_id_t))               # global_enb_id_t* global_enb_id (OPTIONAL)
#     ]


# class ue_id_e2sm_t(ctypes.Structure):
#     class Union(ctypes.Union):
#         _fields_ = [
#             ("gnb", gnb_e2sm_t),  # Direct structure, no POINTER
#             ("gnb_du", gnb_du_e2sm_t),
#             ("gnb_cu_up", gnb_cu_up_e2sm_t),
#             ("ng_enb", ng_enb_e2sm_t),
#             ("ng_enb_du", ng_enb_du_e2sm_t),
#             ("en_gnb", en_gnb_e2sm_t),
#             ("enb", enb_e2sm_t),
#         ]

#     _fields_ = [
#         ("type", ue_id_e2sm_e),  # Enum or integer type
#         ("union", Union),  # Directly embedded union
#     ]

class e2sm_rc_ctrl_hdr_frmt_1_t(ctypes.Structure):
    _fields_ = [
        ("ue_id", ue_id_e2sm_t),  # UE ID
        ("ric_style_type", ctypes.c_uint32),  # RIC Style Type (INTEGER)
        ("ctrl_act_id", ctypes.c_uint16),  # Control Action ID
        ("ric_ctrl_decision", ctypes.POINTER(ric_ctrl_decision_e)),  # Pointer to the ric_ctrl_decision enum (optional)
    ]

class e2sm_rc_ctrl_hdr_frmt_2_t(ctypes.Structure):
    _fields_ = [
        ("ue_id", ctypes.POINTER(ue_id_e2sm_t)),  # Pointer to ue_id_e2sm_t (optional)
        ("ric_ctrl_dec", ctypes.POINTER(ric_ctrl_dec_ctrl_hdr_frmt_2_e)),  # Pointer to ric_ctrl_dec_ctrl_hdr_frmt_2_e (optional)
    ]

   
class RCControlHdr(ctypes.Structure):
    class e2sm_rc_ctrl_hdr_union(ctypes.Union):
        _fields_ = [
            ("frmt_1", e2sm_rc_ctrl_hdr_frmt_1_t),
            ("frmt_2", e2sm_rc_ctrl_hdr_frmt_2_t),
        ]
    _fields_ = [
        ("format", e2sm_rc_ctrl_hdr_e),  # The format field
        ("union", e2sm_rc_ctrl_hdr_union),  # The union with frmt_1 and frmt_2
    ]


# TODO add wrapper for encode/decode procedure and memory management