import ctypes
import numpy as np
from sm_framework.py_oran.rc import RCControlHdr as hdr
from sm_framework.py_oran.rc import RCControlMsg as ctrl
from sm_framework.py_oran.rc import RCFunctionDef as funcdef
from sm_framework.py_oran.ByteArray import ByteArray
from sm_framework.py_oran.rc.enums import *

from sm_framework.lib.library_wrapper import rc_lib, wrap_functions

# Defined in Section 7.6.2.1 of the RC Service Model Specification
control_action_ids = {
    "DRB QoS Configuration": 1,
    "QoS flow mapping configuration": 2,
    "Logical channel configuration": 3,
    "Radio admission control": 4,
    "DRB termination control": 5,
    "DRB split ratio control": 6,
    "PDCP Duplication control": 7
}

# RIC Style Type for RIC Control Service: defined in SEction 7.6.1 of the RC Service Model Specification
ric_style_types = {
    "Radio Bearer Control": 1,
    "Radio resource allocation control": 2,
    "Connected mode mobility control": 3,
    "Radio access control": 4,
    "Dual connectivity (DC) control": 5,
    "Carrier Aggregation (CA) control": 6,
    "Idle mode mobility control": 7,
    "UE information and assignment": 8,
    "Measurement Reporting Configuration control": 9,
    "Beamforming Configuration control": 10,
    "Multiple Actions Control": 255
}

# QoS flow mapping configuration: defined in Section 8.4.2.2 of the RC Service Model Specification
qos_ran_parameter_ids = {
    "DRB ID": 1,
    "List of QoS Flows to be modified in DRB": 2,
    "QoS Flow Item": 3,
    "QoS Flow Identifier": 4,
    "QoS Flow Mapping Indication": 5
}

qos_ran_parameter_id_to_name = {
    1: "DRB ID",
    2: "List of QoS Flows to be modified in DRB",
    3: "QoS Flow Item",
    4: "QoS Flow Identifier",
    5: "QoS Flow Mapping Indication"
}


class RCControlReq(ctypes.Structure):
    _fields_ = [
        ("hdr", hdr.RCControlHdr),
        ("msg", ctrl.RCControlMsg),  # Union for the various data types
    ]

class RCControlReqEncoded(ctypes.Structure):
    _fields_ = [
        ("hdr_encoded", ByteArray),
        ("msg_encoded", ByteArray)
    ]

# TODO add wrapper for encode/decode procedure and memory management
class RCControlReqWrapper():
    def __init__(self):
        self.control_req: RCControlReq =  RCControlReq() # This should be built by using methods defined in this class
        self.free_hdr = wrap_functions(rc_lib, 'free_e2sm_rc_ctrl_hdr', None, [ctypes.POINTER(hdr.RCControlHdr)])
        self.free_msg = wrap_functions(rc_lib, 'free_e2sm_rc_ctrl_msg', None, [ctypes.POINTER(ctrl.RCControlMsg)])
        self.encode_hdr = wrap_functions(rc_lib, 'rc_enc_ctrl_hdr_asn', ByteArray, [ctypes.POINTER(hdr.RCControlHdr)])
        self.encode_msg = wrap_functions(rc_lib, 'rc_enc_ctrl_msg_asn', ByteArray, [ctypes.POINTER(ctrl.RCControlMsg)])
    
    def encode(self) -> RCControlReqEncoded:
        """
        This method encodes a RCControlReq and returns the corresponding binary
        
        Be sure to call other methods of this class to build the RCControlReq
        """
        if self.control_req is None:
            return

        ctrl_req_enc = RCControlReqEncoded()
        
        ctrl_req_enc.hdr_encoded = self.encode_hdr(self.control_req.hdr)
        ctrl_req_enc.msg_encoded = self.encode_msg(self.control_req.msg)

        return ctrl_req_enc


    def get_ue_id(self, ue_info: hdr.ue_id_e2sm_t):
        ret: hdr.ue_id_e2sm_t = hdr.ue_id_e2sm_t()

        if ue_info.type == ue_id_e2sm_e.GNB_CU_UP_UE_ID_E2SM:
            print()
        elif ue_info.type == ue_id_e2sm_e.GNB_DU_UE_ID_E2SM:
            print()
        elif ue_info.type == ue_id_e2sm_e.GNB_CU_UP_UE_ID_E2SM:
            print()
        elif ue_info.type == ue_id_e2sm_e.NG_ENB_UE_ID_E2SM:
            print()
        elif ue_info.type == ue_id_e2sm_e.NG_ENB_DU_UE_ID_E2SM:
            print()
        elif ue_info.type == ue_id_e2sm_e.EN_GNB_UE_ID_E2SM:
            print()
        elif ue_info.type == ue_id_e2sm_e.ENB_UE_ID_E2SM:
            print()
        else:
            print("Unknown UE ID Type")
            

        return ret

    def print_ctrl_req(self):
        # Header
        print("--- RC Control Request Header ---")
        print("Format: {}".format(self.control_req.hdr.format.value))
        print("Style: {}".format(self.control_req.hdr.union.frmt_1.ric_style_type))
        print("Control Action ID: {}".format(self.control_req.hdr.union.frmt_1.ctrl_act_id))

        # Message
        print("--- RC Control Request Msg ---")
        print("Format: {}".format(self.control_req.msg.format.value))
        for i in range(0, self.control_req.msg.union.frmt_1.sz_ran_param):
            print("Parameter: {}".format(qos_ran_parameter_id_to_name[self.control_req.msg.union.frmt_1.ran_param[i].ran_param_id]))
            print("Val type: {}".format(self.control_req.msg.union.frmt_1.ran_param[i].ran_param_val.type.value))
            
            if qos_ran_parameter_id_to_name[self.control_req.msg.union.frmt_1.ran_param[i].ran_param_id] == "DRB ID":
                if self.control_req.msg.union.frmt_1.ran_param[i].ran_param_val.type.value == ran_parameter_val_type_e.ELEMENT_KEY_FLAG_TRUE_RAN_PARAMETER_VAL_TYPE:
                    print("Flag true drb change: {}".format(self.control_req.msg.union.frmt_1.ran_param[i].ran_param_val.union.flag_true.contents.union.int_ran))
            
            if qos_ran_parameter_id_to_name[self.control_req.msg.union.frmt_1.ran_param[i].ran_param_id] == "List of QoS Flows to be modified in DRB":
                if self.control_req.msg.union.frmt_1.ran_param[i].ran_param_val.type.value == ran_parameter_val_type_e.LIST_RAN_PARAMETER_VAL_TYPE:
                    lst = self.control_req.msg.union.frmt_1.ran_param[i].ran_param_val.union.lst.contents
                    
                    for j in range(0, lst.sz_lst_ran_param):
                        print("Element in the list: {}".format(lst.lst_ran_param[j].ran_param_struct.sz_ran_param_struct))
                        for k in range(0, lst.lst_ran_param[j].ran_param_struct.sz_ran_param_struct):
                            print("--> Param id: {} ({})".format(lst.lst_ran_param[j].ran_param_struct.ran_param_struct[k].ran_param_id, qos_ran_parameter_id_to_name[lst.lst_ran_param[j].ran_param_struct.ran_param_struct[k].ran_param_id]))
                            print("--> Param Type: {}".format(lst.lst_ran_param[j].ran_param_struct.ran_param_struct[k].ran_param_val.type.value))
                            
                            if lst.lst_ran_param[j].ran_param_struct.ran_param_struct[k].ran_param_val.type.value == ran_parameter_val_type_e.ELEMENT_KEY_FLAG_TRUE_RAN_PARAMETER_VAL_TYPE:
                                # We need to check the type integer/bool and so on
                                print("--> Flag True Param Value {}".format(lst.lst_ran_param[j].ran_param_struct.ran_param_struct[k].ran_param_val.union.flag_true.contents.union.int_ran))
                            elif lst.lst_ran_param[j].ran_param_struct.ran_param_struct[k].ran_param_val.type.value == ran_parameter_val_type_e.ELEMENT_KEY_FLAG_FALSE_RAN_PARAMETER_VAL_TYPE:
                                print("--> Flag False Param Value {}".format(lst.lst_ran_param[j].ran_param_struct.ran_param_struct[k].ran_param_val.union.flag_false.contents.union.int_ran))

                            print("--")

    def fill_DRB_param(self, index):
        self.control_req.msg.union.frmt_1.ran_param[index].ran_param_id = qos_ran_parameter_ids["DRB ID"]
        self.control_req.msg.union.frmt_1.ran_param[index].ran_param_val.type = ran_parameter_val_type_e.ELEMENT_KEY_FLAG_TRUE_RAN_PARAMETER_VAL_TYPE
        flag_true_value = ctrl.ran_parameter_value_t()
        flag_true_value.type = ran_parameter_value_e.INTEGER_RAN_PARAMETER_VALUE
        flag_true_value.union.int_ran = 5 # FIXME make this a parameter

        flag_true_ptr = ctypes.pointer(flag_true_value)
        # self.control_req.msg.union.frmt_1.ran_param[index].ran_param_val.union.flag_true = ran_parameter_value_t()
        self.control_req.msg.union.frmt_1.ran_param[index].ran_param_val.union.flag_true = flag_true_ptr


    def fill_qos_param(self, index):
        self.control_req.msg.union.frmt_1.ran_param[index].ran_param_id = qos_ran_parameter_ids["List of QoS Flows to be modified in DRB"]
        self.control_req.msg.union.frmt_1.ran_param[index].ran_param_val.type = ran_parameter_val_type_e.LIST_RAN_PARAMETER_VAL_TYPE
        
        # Initialize value_list
        value_list = ctrl.ran_param_list_t()
        value_list.sz_lst_ran_param = 1
        lst_param_type = ctrl.lst_ran_param_t * value_list.sz_lst_ran_param
        value_list.lst_ran_param = lst_param_type()


        # Initialize the first list element
        value_list.lst_ran_param[0].ran_param_struct.sz_ran_param_struct = 2
        lst_param_struct_type = ctrl.seq_ran_param_t * value_list.lst_ran_param[0].ran_param_struct.sz_ran_param_struct
        value_list.lst_ran_param[0].ran_param_struct.ran_param_struct = lst_param_struct_type()


        value_list.lst_ran_param[0].ran_param_struct.ran_param_struct[0].ran_param_id = qos_ran_parameter_ids["QoS Flow Identifier"]
        value_list.lst_ran_param[0].ran_param_struct.ran_param_struct[0].ran_param_val.type = ran_parameter_val_type_e.ELEMENT_KEY_FLAG_TRUE_RAN_PARAMETER_VAL_TYPE

        flag_true_value = ctrl.ran_parameter_value_t()
        flag_true_value.type = ran_parameter_value_e.INTEGER_RAN_PARAMETER_VALUE
        flag_true_value.union.int_ran = 10  # FIXME: Replace with actual parameter (QFI)
        value_list.lst_ran_param[0].ran_param_struct.ran_param_struct[0].ran_param_val.union.flag_true = ctypes.pointer(flag_true_value)

        value_list.lst_ran_param[0].ran_param_struct.ran_param_struct[1].ran_param_id = qos_ran_parameter_ids["QoS Flow Mapping Indication"]
        value_list.lst_ran_param[0].ran_param_struct.ran_param_struct[1].ran_param_val.type = ran_parameter_val_type_e.ELEMENT_KEY_FLAG_FALSE_RAN_PARAMETER_VAL_TYPE
        flag_false_value = ctrl.ran_parameter_value_t()
        flag_false_value.type = ran_parameter_value_e.INTEGER_RAN_PARAMETER_VALUE
        flag_false_value.union.int_ran = 1  # FIXME: Replace with actual value
        value_list.lst_ran_param[0].ran_param_struct.ran_param_struct[1].ran_param_val.union.flag_false = ctypes.pointer(flag_false_value)

        self.control_req.msg.union.frmt_1.ran_param[index].ran_param_val.union.lst = ctypes.pointer(value_list)

    def qos_flow_mapping_config_handler(self, ctrl_act: funcdef.seq_ctrl_act_2_t, sz_ran_param: ctypes.c_size_t):
        # in this case only DRB ID and list of qos flows to be modified in DRB are supported
        for i in range(0, sz_ran_param):
            if ctrl_act.assoc_ran_param[i].id == qos_ran_parameter_ids["DRB ID"]:
                self.fill_DRB_param(i)
            elif ctrl_act.assoc_ran_param[i].id == qos_ran_parameter_ids["List of QoS Flows to be modified in DRB"]:
                self.fill_qos_param(i)
            else:
                print("QoS parameter not supported {}".format(ctrl_act.assoc_ran_param[i].id))
            


    def gen_rc_msg(self, ran_func_dsc: funcdef.RCFuncDef, ue_id: hdr.ue_id_e2sm_t=None):
        # FIXME Add other parameters
        if not ran_func_dsc.ctrl:
            # TODO Add error message
            return
        # self.control_req = RCControlReq()
        ctrl_descr = ran_func_dsc.ctrl.contents 

        self.control_req.hdr = hdr.RCControlHdr()
        self.control_req.msg = ctrl.RCControlMsg()
        
        for i in range(0, ctrl_descr.sz_seq_ctrl_style):
            style = ctrl_descr.seq_ctrl_style[i]
            
            # Only Radio Bearer Control Supported
            style_bytes = bytes(np.ctypeslib.as_array(style.name.buf, shape = (style.name.len,)))
            style_decoded_string = style_bytes.decode('utf-8')
            if style_decoded_string == "Radio Bearer Control":
                self.generate_radio_bearer_control_msg(style=style, style_decoded=style_decoded_string, ue_id=ue_id)
            elif style_decoded_string == "Radio Resource Allocation Control":
                print("TODO")
            else:
                # TODO add error message
                print("Not Supported Style {}".format(style_decoded_string))
                return

            


    def generate_radio_bearer_control_msg(self,  style: funcdef.seq_ctrl_style_t, style_decoded, ue_id: hdr.ue_id_e2sm_t=None):
        self.control_req.hdr.format = style.hdr
            
        if self.control_req.hdr.format.value != e2sm_rc_ctrl_hdr_e.FORMAT_1_E2SM_RC_CTRL_HDR:
            print("Not supported header format")
            return
        self.control_req.hdr.union.frmt_1 = hdr.e2sm_rc_ctrl_hdr_frmt_1_t()

        self.control_req.hdr.union.frmt_1.ric_style_type = ric_style_types[style_decoded]

        # TODO How do we get ue_id?
        if not ue_id is None:
            self.control_req.hdr.union.frmt_1.ue_id = ue_id
        else:
            print("UE ID not provided skipping (this could generate an error during encoding)...")

        self.control_req.msg.format = style.msg

        if self.control_req.msg.format.value !=e2sm_rc_ctrl_msg_e.FORMAT_1_E2SM_RC_CTRL_MSG:
            print("Not supported message format")
            return
        
        seq_ctrl_act = style.seq_ctrl_act
        sz_seq_ctrl_act = style.sz_seq_ctrl_act

        if not seq_ctrl_act:
            # TODO add error message
            return

        for j in range(0, sz_seq_ctrl_act):
            seq_ctrl_act_name_bytes = bytes(np.ctypeslib.as_array(seq_ctrl_act[j].name.buf, shape = (seq_ctrl_act[j].name.len,)))
            seq_ctrl_act_name = seq_ctrl_act_name_bytes.decode('utf-8')
            # We should make this as a parameter
            # QoS flow Mapping configuration:
            # To request the multiplexing of QoS flows to a DRB (addition, modification, deletion)
            if seq_ctrl_act_name != "QoS flow mapping configuration":
                # TODO Add error message
                print("not recognized control action")
                return

            self.control_req.hdr.union.frmt_1.ctrl_act_id = control_action_ids[seq_ctrl_act_name]
            self.control_req.msg.union.frmt_1.sz_ran_param = seq_ctrl_act[j].sz_seq_assoc_ran_param

            # Creating ran parameter array
            RanParamArr = ctrl.seq_ran_param_t * self.control_req.msg.union.frmt_1.sz_ran_param
            self.control_req.msg.union.frmt_1.ran_param = RanParamArr()

            self.qos_flow_mapping_config_handler(seq_ctrl_act[j], seq_ctrl_act[j].sz_seq_assoc_ran_param)

    # def __del__(self):
        # print("tempting free")
        # if self.control_req.hdr:
        #     print("tempting freeing header")
        #     self.free_hdr(self.control_req.hdr)
        # if self.control_req.msg:
        #     print("tempting freeing msg")
        #     self.free_msg(self.control_req.msg)
    



