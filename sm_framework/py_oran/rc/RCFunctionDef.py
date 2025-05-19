import ctypes
import numpy as np
from sm_framework.lib.library_wrapper import rc_lib, wrap_functions
from sm_framework.py_oran.ByteArray import ByteArray
from sm_framework.py_oran.rc.enums import *
 

class ran_function_name_t(ctypes.Structure):
    _fields_ = [
        ("name", ByteArray),           # RAN Function Short Name (PrintableString [1-150])
        ("oid", ByteArray),            # RAN Function Service Model OID (PrintableString [1-1000])
        ("description", ByteArray),    # RAN Function Description (PrintableString [1-150])
        ("instance", ctypes.POINTER(ctypes.c_long))  # Optional INTEGER
    ]


# Forward declaration of ran_param_def_t
class ran_param_def_t(ctypes.Structure):
    pass

class ran_param_lst_struct_t(ctypes.Structure):
    _fields_ = [
        ("ran_param_id", ctypes.c_uint32),        # RAN Parameter ID (INTEGER)
        ("ran_param_name", ByteArray),            # RAN Parameter Name (PrintableString)
        ("ran_param_def", ctypes.POINTER(ran_param_def_t))  # Optional RAN Parameter Definition (Pointer)
    ]

# Mapping ran_param_type_t
class ran_param_type_t(ctypes.Structure):
    _fields_ = [
        ("sz_ran_param", ctypes.c_size_t),        # Size of RAN Parameter (size_t)
        ("ran_param", ctypes.POINTER(ran_param_lst_struct_t))  # Pointer to ran_param_lst_struct_t
    ]

# Mapping ran_param_def_t with a union
class _ran_param_union(ctypes.Union):
    _fields_ = [
        ("lst", ctypes.POINTER(ran_param_type_t)),    # Pointer to ran_param_type_t (LIST)
        ("strct", ctypes.POINTER(ran_param_type_t))   # Pointer to ran_param_type_t (STRUCTURE)
    ]
    
# Managing forward declaration
ran_param_def_t._fields_ = [
        ("type", ran_parameter_def_type_e),            # RAN Parameter Type (INTEGER, ran_parameter_def_type_e)
        ("value", _ran_param_union)        # Union with lst or strct
    ]
# class ran_param_def_t(ctypes.Structure):
#     class _ran_param_union(ctypes.Union):
#         _fields_ = [
#             ("lst", ctypes.POINTER(ran_param_type_t)),    # Pointer to ran_param_type_t (LIST)
#             ("strct", ctypes.POINTER(ran_param_type_t))   # Pointer to ran_param_type_t (STRUCTURE)
#         ]

#     _fields_ = [
#         ("type", ran_parameter_def_type_e),            # RAN Parameter Type (INTEGER, ran_parameter_def_type_e)
#         ("value", _ran_param_union)        # Union with lst or strct
#     ]


class seq_ev_trg_style_t(ctypes.Structure):
    _fields_ = [
        ("style", ctypes.c_uint32),    # RIC Event Trigger Style Type (INTEGER)
        ("name", ByteArray),           # RIC Event Trigger Style Name (PrintableString [1-150])
        ("format", ctypes.c_uint32)    # RIC Event Trigger Format Type (INTEGER)
    ]

class seq_ran_param_3_t(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint32),             # RAN Parameter ID [1-4294967295]
        ("name", ByteArray),                 # RAN Parameter Name [1-150]
        ("ran_param_def", ctypes.POINTER(ran_param_def_t))  # Optional RAN Parameter Definition (Pointer)
    ]

class call_proc_break_t(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint16),             # Call Process Breakpoint ID [1 - 65535]
        ("name", ByteArray),                 # Call Process Breakpoint Name [1-150]
        ("sz_param", ctypes.c_size_t),       # Size of Associated RAN Parameters [0-65535]
        ("param", ctypes.POINTER(seq_ran_param_3_t))  # Pointer to sequence of Associated RAN Parameters
    ]

class seq_call_proc_type_t(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint16),                   # Call Process Type ID [1-65535]
        ("name", ByteArray),                       # Call Process Type Name [1-150]
        ("sz_call_proc_break", ctypes.c_size_t),   # Size of Call Process Breakpoints [1-65535]
        ("call_proc_break", ctypes.POINTER(call_proc_break_t))  # Pointer to Call Process Breakpoints
    ]

class seq_report_sty_t(ctypes.Structure):
    _fields_ = [
        ("report_type", ctypes.c_uint32),             # RIC Report Style Type [INTEGER]
        ("name", ByteArray),                           # RIC Report Style Name [1-150]
        ("ev_trig_type", ctypes.c_uint32),            # Supported RIC Event Trigger Style Type [INTEGER]
        ("act_frmt_type", ctypes.c_uint32),           # RIC Report Action Format Type [INTEGER]
        ("ind_hdr_type", ctypes.c_uint32),            # RIC Indication Header Format Type [INTEGER]
        ("ind_msg_type", ctypes.c_uint32),            # RIC Indication Message Format Type [INTEGER]
        ("sz_seq_ran_param", ctypes.c_size_t),        # Size of RAN Parameters Supported [0 - 65535]
        ("ran_param", ctypes.POINTER(seq_ran_param_3_t))  # Pointer to sequence of RAN Parameters
    ]

class seq_ins_ind_t(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint16),             # Insert Indication ID [1-65535]
        ("name", ByteArray),                 # Insert Indication Name [1-150]
        ("sz_seq_ins_ind", ctypes.c_size_t), # Size of Insert Indications [0-65535]
        ("seq_ins_ind", ctypes.POINTER(seq_ran_param_3_t))  # Pointer to sequence of Insert Indications
    ]

class seq_ins_sty_t(ctypes.Structure):
    _fields_ = [
        ("style_type", ctypes.c_uint32),           # RIC Insert Style Type [INTEGER]
        ("name", ByteArray),                        # RIC Insert Style Name [1-150]
        ("ev_trig_style_type", ctypes.c_uint32),   # Supported RIC Event Trigger Style Type [INTEGER]
        ("act_def_frmt_type", ctypes.c_uint32),    # RIC Action Definition Format Type [INTEGER]
        ("sz_seq_ins_ind", ctypes.c_size_t),       # Size of Insert Indications [0-65535]
        ("seq_ins_ind", ctypes.POINTER(seq_ins_ind_t)),  # Pointer to sequence of Insert Indications
        ("ind_hdr_frmt_type", ctypes.c_uint32),    # RIC Indication Header Format Type [INTEGER]
        ("ind_msg_frmt_type", ctypes.c_uint32),    # RIC Indication Message Format Type [INTEGER]
        ("call_proc_id_type", ctypes.c_uint32)     # RIC Call Process ID Format Type [INTEGER]
    ]
class call_proc_id_frmt_t(ctypes.Structure):
    _fields_ = [
        ("dummy", ctypes.c_uint32)  # Dummy field
    ]

class seq_ctrl_act_2_t(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint16),                        # Control Action ID [1-65535]
        ("name", ByteArray),                            # Control Action Name [1-150]
        ("sz_seq_assoc_ran_param", ctypes.c_size_t),   # Size of Associated RAN Parameters [0-65535]
        ("assoc_ran_param", ctypes.POINTER(seq_ran_param_3_t))  # Pointer to sequence of Associated RAN Parameters
    ]

class seq_ctrl_style_t(ctypes.Structure):
    _fields_ = [
        ("style_type", ctypes.c_uint32),                 # RIC Control Style Type [INTEGER]
        ("name", ByteArray),                             # RIC Control Style Name [1-150]
        ("sz_seq_ctrl_act", ctypes.c_size_t),            # Size of Control Actions [0-65535]
        ("seq_ctrl_act", ctypes.POINTER(seq_ctrl_act_2_t)),  # Pointer to sequence of Control Actions
        ("hdr", ctypes.c_uint32),                        # RIC Control Header Format Type [INTEGER]
        ("msg", ctypes.c_uint32),                        # RIC Control Message Format Type [INTEGER]
        ("call_proc_id_type", ctypes.POINTER(call_proc_id_frmt_t)),  # Optional: Pointer to Call Process ID Format Type
        ("out_frmt", ctypes.c_uint32),                  # RIC Control Outcome Format Type [INTEGER]
        ("sz_ran_param_ctrl_out", ctypes.c_size_t),      # Size of Associated RAN Parameters for Control Outcome [0-255]
        ("ran_param_ctrl_out", ctypes.POINTER(seq_ran_param_3_t))  # Pointer to sequence of RAN Parameters for Control Outcome
    ]

class seq_pol_action_t(ctypes.Structure):
    _fields_ = [
        ("action_id", ctypes.c_uint32),                        # Policy Action ID (Mandatory, uint32_t)
        ("name", ByteArray),                                   # Policy Action Name (Mandatory, byte_array_t)
        ("frmt_type", ctypes.c_uint32),                       # RIC Action Definition Format Type (Mandatory, uint32_t)
        ("sz_seq_assoc_rp_action", ctypes.c_size_t),         # Size of associated RAN Parameters for Policy Action
        ("seq_assoc_rp_action", ctypes.POINTER(seq_ran_param_3_t)),  # Pointer to associated RAN Parameters for Policy Action
        ("sz_seq_assoc_rp_policy", ctypes.c_size_t),         # Size of associated RAN Parameters for Policy Condition
        ("seq_assoc_rp_policy", ctypes.POINTER(seq_ran_param_3_t))    # Pointer to associated RAN Parameters for Policy Condition
    ]

class seq_policy_sty_t(ctypes.Structure):
    _fields_ = [
        ("style_type", ctypes.c_uint32),                      # RIC Policy Style Type (Mandatory, uint32_t)
        ("name", ByteArray),                                  # RIC Policy Style Name (Mandatory, byte_array_t)
        ("ev_trg_style_type", ctypes.c_uint32),              # Supported RIC Event Trigger Style Type (Mandatory, uint32_t)
        ("sz_seq_pol_action", ctypes.c_size_t),              # Size of Policy Actions
        ("seq_pol_action", ctypes.POINTER(seq_pol_action_t)) # Pointer to Policy Actions
    ]

# Event Trigger
class ran_func_def_ev_trig_t(ctypes.Structure):
    _fields_ = [
        ("sz_seq_ev_trg_style", ctypes.c_size_t),         # Sequence of EVENT TRIGGER styles [1 - 63]
        ("seq_ev_trg_style", ctypes.POINTER(seq_ev_trg_style_t)),  # Pointer to EVENT TRIGGER styles

        ("sz_seq_ran_param_l2_var", ctypes.c_size_t),     # Sequence of RAN Parameters for L2 Variables [0 - 65535]
        ("seq_ran_param_l2_var", ctypes.POINTER(seq_ran_param_3_t)),  # Pointer to RAN Parameters for L2 Variables

        ("sz_seq_call_proc_type", ctypes.c_size_t),        # Sequence of Call Process Types [0-65535]
        ("seq_call_proc_type", ctypes.POINTER(seq_call_proc_type_t)),  # Pointer to Call Process Types

        ("sz_seq_ran_param_id_ue", ctypes.c_size_t),       # Sequence of RAN Parameters for Identifying UEs [0-65535]
        ("seq_ran_param_id_ue", ctypes.POINTER(seq_ran_param_3_t)),  # Pointer to RAN Parameters for Identifying UEs

        ("sz_seq_ran_param_id_cell", ctypes.c_size_t),     # Sequence of RAN Parameters for Identifying Cells [0-65535]
        ("seq_ran_param_id_cell", ctypes.POINTER(seq_ran_param_3_t))   # Pointer to RAN Parameters for Identifying Cells
    ]

# Report
class ran_func_def_report_t(ctypes.Structure):
    _fields_ = [
        ("sz_seq_report_sty", ctypes.c_size_t),        # Sequence of REPORT styles [1 - 63]
        ("seq_report_sty", ctypes.POINTER(seq_report_sty_t))  # Pointer to sequence of REPORT styles
    ]

# Insert
class ran_func_def_insert_t(ctypes.Structure):
    _fields_ = [
        ("sz_seq_ins_sty", ctypes.c_size_t),       # Sequence of INSERT styles [1-63]
        ("seq_ins_sty", ctypes.POINTER(seq_ins_sty_t))  # Pointer to sequence of INSERT styles
    ]

# Control
class ran_func_def_ctrl_t(ctypes.Structure):
    _fields_ = [
        ("sz_seq_ctrl_style", ctypes.c_size_t),           # Size of the sequence of CONTROL styles [1 - 63]
        ("seq_ctrl_style", ctypes.POINTER(seq_ctrl_style_t))  # Pointer to the sequence of CONTROL styles
    ]

# Policy
class ran_func_def_policy_t(ctypes.Structure):
    _fields_ = [
        ("sz_policy_styles", ctypes.c_size_t),               # Size of POLICY styles [1-63]
        ("seq_policy_sty", ctypes.POINTER(seq_policy_sty_t)) # Pointer to the sequence of POLICY styles
    ]

# RAN Function Definition
class RCFuncDef(ctypes.Structure):
    _fields_ = [
        ("name", ran_function_name_t),                        # RAN Function Name (Mandatory, ran_function_name_t)
        ("ev_trig", ctypes.POINTER(ran_func_def_ev_trig_t)),  # Pointer to RAN Function Definition for EVENT TRIGGER (Optional)
        ("report", ctypes.POINTER(ran_func_def_report_t)),      # Pointer to RAN Function Definition for REPORT (Optional)
        ("insert", ctypes.POINTER(ran_func_def_insert_t)),      # Pointer to RAN Function Definition for INSERT (Optional)
        ("ctrl", ctypes.POINTER(ran_func_def_ctrl_t)),          # Pointer to RAN Function Definition for CONTROL (Optional)
        ("policy", ctypes.POINTER(ran_func_def_policy_t))       # Pointer to RAN Function Definition for POLICY (Optional)
    ]

    def print_rc_functions(self):
        if self.ev_trig:
            print("[Event Trigger]")
            # get ev_trig object
            ev_trig_obj = self.ev_trig.contents
            for i in range(0, ev_trig_obj.sz_seq_ev_trg_style):
                function_def = ev_trig_obj.seq_ev_trg_style[i]
                function_def_array = bytes(np.ctypeslib.as_array(function_def.name.buf, shape = (function_def.name.len,)))
                function_def_decoded = function_def_array.decode('utf-8')
                print(function_def_decoded)
        
        if self.report:
            print("[Report]")
            # get report object
            report_obj = self.report.contents
            for i in range(0, report_obj.sz_seq_report_sty):
                function_def = report_obj.seq_report_sty[i]
                function_def_array = bytes(np.ctypeslib.as_array(function_def.name.buf, shape = (function_def.name.len,)))
                function_def_decoded = function_def_array.decode('utf-8')
                print(function_def_decoded)

        if self.insert:
            print("[Insert]: TBD")

        if self.ctrl:
            print("[Control]")
            # get ctrl object
            ctrl_obj = self.ctrl.contents
            for i in range(0, ctrl_obj.sz_seq_ctrl_style):
                function_def = ctrl_obj.seq_ctrl_style[i]
                function_def_array = bytes(np.ctypeslib.as_array(function_def.name.buf, shape = (function_def.name.len,)))
                function_def_decoded = function_def_array.decode('utf-8')
                print(function_def_decoded)
                print("hdr frmt: {}".format(function_def.hdr))
                print("msg frmt: {}".format(function_def.msg))
                for j in range(0, function_def.sz_seq_ctrl_act):
                    action_def = function_def.seq_ctrl_act[j]
                    action_def_array = bytes(np.ctypeslib.as_array(action_def.name.buf, shape = (action_def.name.len,)))
                    action_def_decoded = action_def_array.decode('utf-8')
                    print("action: {}".format(action_def_decoded))
                    print("assoc ran param size: {}".format(action_def.sz_seq_assoc_ran_param))
                    for k in range(0, action_def.sz_seq_assoc_ran_param):
                        assoc_ran_param = action_def.assoc_ran_param[k]
                        assoc_ran_param_name_array = bytes(np.ctypeslib.as_array(assoc_ran_param.name.buf, shape = (assoc_ran_param.name.len,)))
                        assoc_ran_param_decoded = assoc_ran_param_name_array.decode('utf-8')
                        print("assoc ran param name: {}".format(assoc_ran_param_decoded))
                        print("assoc ran param id: {}".format(assoc_ran_param.id))
                        if assoc_ran_param.ran_param_def:
                            assoc_ran_param_def = assoc_ran_param.ran_param_def.contents
                            print("assoc ran param def type: {}".format(assoc_ran_param_def.type.value))
                            self.print_assoc_ran_param(assoc_ran_param_def)
                            
                                

                   
        if self.policy:
            print("[Policy]: TBD")
    
    def print_assoc_ran_param(self, assoc_ran_param_def):
        to_print = None
        if assoc_ran_param_def.type.value == ran_parameter_def_type_e.LIST_RAN_PARAMETER_DEF_TYPE:
            # print("it's a list")
            to_print = assoc_ran_param_def.value.lst
        elif assoc_ran_param_def.type.value == ran_parameter_def_type_e.STRUCTURE_RAN_PARAMETER_DEF_TYPE:
            # print("it's a structure")
            to_print = assoc_ran_param_def.value.strct
        
        if to_print:
            # print("here")
            for i in range(0, to_print.contents.sz_ran_param):
                ran_param = to_print.contents.ran_param[i]
                ran_param_name_array = bytes(np.ctypeslib.as_array(ran_param.ran_param_name.buf, shape = (ran_param.ran_param_name.len,)))
                ran_param_name_decoded = ran_param_name_array.decode('utf-8')
                print("ran param name: {}".format(ran_param_name_decoded))
                print("ran param id: {}".format(ran_param.ran_param_id))
                # print(ran_param.ran_param_def)
                if ran_param.ran_param_def:
                    ran_param_def = ran_param.ran_param_def.contents
                    print("ran param def type: {}".format(ran_param_def.type.value))
                    self.print_assoc_ran_param(ran_param_def)
            

class RCFuncDefWrapper():
    def __init__(self, hex: str):
        self.rc_action_def: RCFuncDef = None
        self.hex = hex
        self.free = wrap_functions(rc_lib, 'free_e2sm_rc_func_def', None, [ctypes.POINTER(RCFuncDef)])
        self.decode_function_def = wrap_functions(rc_lib, 'rc_dec_func_def_asn', RCFuncDef, [ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint8)])

    def set_hex(self, hex: str):
        self.hex = hex

    def decode(self) -> RCFuncDef:
        byte_string = bytes.fromhex(self.hex)
        byte_array = (ctypes.c_uint8 * len(byte_string)).from_buffer_copy(byte_string)
        self.rc_action_def = self.decode_function_def(len(byte_array), byte_array)
        return self.rc_action_def
    
    def __del__(self):
        if self.rc_action_def:
            self.free(self.rc_action_def)
            self.rc_action_def = None