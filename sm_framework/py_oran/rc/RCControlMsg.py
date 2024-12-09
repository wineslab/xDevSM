import ctypes
from sm_framework.py_oran.ByteArray import ByteArray
from sm_framework.py_oran.rc.enums import * 

# Modify ran_parameter_value_t to include the union
class ran_parameter_value_t(ctypes.Structure):
    class ran_parameter_value_union(ctypes.Union):
        _fields_ = [
            ("bool_ran", ctypes.c_bool),
            ("int_ran", ctypes.c_int64),
            ("real_ran", ctypes.c_double),
            ("bit_str_ran", ByteArray),
            ("octet_str_ran", ByteArray),
            ("printable_str_ran", ByteArray),
        ]
    _fields_ = [
        ("type", ran_parameter_value_e),
        ("union", ran_parameter_value_union),  # Union for the various data types
    ]

# ran_param_struct_t forward declaration
class ran_param_struct_t(ctypes.Structure):
    pass

# ran_param_list_t forward declaration
class ran_param_list_t(ctypes.Structure):
    pass

class ran_param_val_type_t(ctypes.Structure):
    class ran_param_val_type_union(ctypes.Union):
        _fields_ = [
            ("flag_true", ctypes.POINTER(ran_parameter_value_t)),
            ("flag_false", ctypes.POINTER(ran_parameter_value_t)),
            ("strct", ctypes.POINTER(ran_param_struct_t)),
            ("lst", ctypes.POINTER(ran_param_list_t)),
        ]
    _fields_ = [
        ("type", ran_parameter_val_type_e),
        ("union", ran_param_val_type_union),
    ]

class seq_ran_param_t(ctypes.Structure):
    _fields_ = [
        ("ran_param_id", ctypes.c_uint32),
        ("ran_param_val", ran_param_val_type_t),
    ]

ran_param_struct_t._fields_ = [
    ("sz_ran_param_struct", ctypes.c_size_t),
    ("ran_param_struct", ctypes.POINTER(seq_ran_param_t)),
]

# lst_ran_param_t
class lst_ran_param_t(ctypes.Structure):
    _fields_ = [
        ("ran_param_struct", ran_param_struct_t),
    ]

# ran_param_list_t
ran_param_list_t._fields_ = [
    ("sz_lst_ran_param", ctypes.c_size_t),
    ("lst_ran_param", ctypes.POINTER(lst_ran_param_t)),
]


class e2sm_rc_ctrl_msg_frmt_1_t(ctypes.Structure):
    _fields_ = [
        ("sz_ran_param", ctypes.c_size_t),  # Size of the list of RAN parameters
        ("ran_param", ctypes.POINTER(seq_ran_param_t)),  # Pointer to the list of RAN parameters
    ]

class seq_ctrl_act_t(ctypes.Structure):
    _fields_ = [
        ("ctrl_act_id", ctypes.c_uint16),  # Control Action ID (mandatory, range [1 - 65535])
        ("ctrl_msg_frmt_1", ctypes.POINTER(e2sm_rc_ctrl_msg_frmt_1_t)),  # Pointer to E2SM-RC Control Message Format 1 (optional/mandatory as per context)
    ]

class seq_ctrl_sma_t(ctypes.Structure):
    _fields_ = [
        ("ctrl_style", ctypes.c_uint32),  # Indicated Control Style (mandatory, integer)
        ("sz_seq_ctrl_act", ctypes.c_size_t),  # Size of the Sequence of Control Actions [1-63]
        ("seq_ctrl_act", ctypes.POINTER(seq_ctrl_act_t)),  # Pointer to an array of seq_ctrl_act_t
    ]

class e2sm_rc_ctrl_msg_frmt_2_t(ctypes.Structure):
    _fields_ = [
        ("sz_seq_ctrl_sma", ctypes.c_size_t),  # Size of Sequence of Control Styles [1-63]
        ("action", ctypes.POINTER(seq_ctrl_sma_t)),  # Pointer to an array of seq_ctrl_sma_t
    ]


class RCControlMsg(ctypes.Structure):
    class e2sm_rc_ctrl_msg_union(ctypes.Union):
        _fields_ = [
            ("frmt_1", e2sm_rc_ctrl_msg_frmt_1_t),  # Format 1: e2sm_rc_ctrl_msg_frmt_1_t
            ("frmt_2", e2sm_rc_ctrl_msg_frmt_2_t),  # Format 2: e2sm_rc_ctrl_msg_frmt_2_t
        ]
    _fields_ = [
        ("format", e2sm_rc_ctrl_msg_e),  # Enum to identify the format
        ("union", e2sm_rc_ctrl_msg_union),  # Union for the format-specific fields
    ]

# TODO add wrapper for encode/decode procedure and memory management