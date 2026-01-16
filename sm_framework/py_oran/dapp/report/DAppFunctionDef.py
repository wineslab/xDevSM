import ctypes
import numpy as np
from sm_framework.py_oran.rc.RCFunctionDef import ran_function_name_t
from sm_framework.py_oran.ByteArray import ByteArray
from sm_framework.lib.library_wrapper import dApp_lib, wrap_functions


class seq_ev_trg_style_dapp_sm_t(ctypes.Structure):
    _fields_ = [
        ("style", ctypes.c_uint32),
        ("name", ByteArray),
        ("format", ctypes.c_uint32),
    ]

class ran_func_def_ev_trig_dapp_sm_t(ctypes.Structure):
    _fields_ = [
        ("sz_seq_ev_trg_style", ctypes.c_size_t),
        ("seq_ev_trg_style", ctypes.POINTER(seq_ev_trg_style_dapp_sm_t)),
    ]

class seq_report_sty_dapp_sm_t(ctypes.Structure):
    _fields_ = [
        ("report_type", ctypes.c_uint32),
        ("name", ByteArray),             # byte_array_t
        ("ev_trig_type", ctypes.c_uint32),
        ("act_frmt_type", ctypes.c_uint32),
        ("ind_hdr_type", ctypes.c_uint32),
        ("ind_msg_type", ctypes.c_uint32),
    ]

class ran_func_def_report_dapp_sm_t(ctypes.Structure):
    _fields_ = [
        ("sz_seq_report_sty", ctypes.c_size_t),
        ("seq_report_sty",ctypes.POINTER(seq_report_sty_dapp_sm_t)),
    ]

class seq_ctrl_style_dapp_sm_t(ctypes.Structure):
    _fields_ = [
        ("style_type", ctypes.c_uint32),
        ("name", ByteArray),          # byte_array_t
        ("hdr", ctypes.c_uint32),
        ("msg", ctypes.c_uint32),
        ("out_frmt", ctypes.c_uint32),
    ]

class ran_func_def_ctrl_dapp_sm_t(ctypes.Structure):
    _fields_ = [
        ("sz_seq_ctrl_style", ctypes.c_size_t),
        ("seq_ctrl_style", ctypes.POINTER(seq_ctrl_style_dapp_sm_t)),
    ]


class DAppFunctionDef(ctypes.Structure):
    _fields_ = [
        ("name", ran_function_name_t),
        ("ev_trig", ctypes.POINTER(ran_func_def_ev_trig_dapp_sm_t)),
        ("report", ctypes.POINTER(ran_func_def_report_dapp_sm_t)),
        ("ctrl", ctypes.POINTER(ran_func_def_ctrl_dapp_sm_t)),
    ]

    def print_dapp_function_def(self):
        print("DApp Function Definition:")
        if self.ev_trig:
            print("[Event Trigger]")
            ev_trig_obj = self.ev_trig.contents
            for i in range(ev_trig_obj.sz_seq_ev_trg_style):
                function_def = ev_trig_obj.seq_ev_trg_style[i]
                function_def_array = bytes(np.ctypeslib.as_array(function_def.name.buf, shape = (function_def.name.len,)))
                function_def_decoded = function_def_array.decode('utf-8')
                style = function_def.style
                print("\tStyle: {}".format(style))
                print("\tName: {}".format(function_def_decoded))

        if self.report:
            print("[Report]")
            # get report object
            report_obj = self.report.contents
            for i in range(0, report_obj.sz_seq_report_sty):
                function_def = report_obj.seq_report_sty[i]
                function_def_array = bytes(np.ctypeslib.as_array(function_def.name.buf, shape = (function_def.name.len,)))
                function_def_decoded = function_def_array.decode('utf-8')
                report_type = function_def.report_type
                print("\tReport Type: {}".format(report_type))
                print("\tName: {}".format(function_def_decoded))
        
        if self.ctrl:
            print("[Control]")
            ctrl_obj = self.ctrl.contents
            for i in range(0, ctrl_obj.sz_seq_ctrl_style):
                function_def = ctrl_obj.seq_ctrl_style[i]
                function_def_array = bytes(np.ctypeslib.as_array(function_def.name.buf, shape = (function_def.name.len,)))
                function_def_decoded = function_def_array.decode('utf-8')
                style_type = function_def.style_type
                print("\tStyle Type: {}".format(style_type))
                print("\tName: {}".format(function_def_decoded))
                    


class DAppFunctionDefWrapper:
    def __init__(self, hex:str):
        self.dapp_function_def: DAppFunctionDef = None
        self.hex = hex
        self.free = wrap_functions(dApp_lib, "free_e2sm_dapp_func_def", None, [ctypes.POINTER(DAppFunctionDef)])
        self.decode_function_def = wrap_functions(dApp_lib, "dapp_dec_func_def_asn", DAppFunctionDef, [ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint8)])
    
    def set_hex(self, hex: str):
        self.hex = hex

    def decode(self) -> DAppFunctionDef:
        byte_string = bytes.fromhex(self.hex)
        byte_array = (ctypes.c_uint8 * len(byte_string)).from_buffer_copy(byte_string)
        self.dapp_function_def = self.decode_function_def(len(byte_array), byte_array)
        return self.dapp_function_def

    def __del__(self):
        if self.dapp_function_def is not None:
            self.free(self.dapp_function_def)
            self.dapp_function_def = None