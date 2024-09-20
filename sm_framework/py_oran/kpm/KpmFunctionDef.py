import ctypes
from sm_framework.lib.library_wrapper import wrapper, wrap_functions
from sm_framework.py_oran.ByteArray import ByteArray
from sm_framework.py_oran.kpm.enums import format_action_def_e




# Custom structure
class kpm_func_def_cus_t(ctypes.Structure):
    _fields_ = [
        ("format", ctypes.c_long),  # Assuming format_action_def_e is an enumeration, replace c_int with the appropriate type if needed
        ("names", ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8))),
        ("names_len", ctypes.c_size_t),
        ("ids", ctypes.POINTER(ctypes.c_long)),
    ]

class KpmFuncDefArr(ctypes.Structure):
    _fields_ = [
        ("len", ctypes.c_size_t),
        ("values", ctypes.POINTER(kpm_func_def_cus_t)),
    ]

    def get_dict_of_values(self):
        """
        key = format
        values = list of actions
        """
        dict_by_format = {}
        for value in range(format_action_def_e.FORMAT_1_ACTION_DEFINITION,
                       format_action_def_e.END_ACTION_DEFINITION):
            dict_by_format[value] = []

        # Access each kpm_act_def_arr_t element in the values array
        for i in range(self.len):
            current_value = self.values[i]
            for j in range(current_value.names_len):
                # Dereference the name pointer and convert it to a string
                name_ptr = current_value.names[j]
                name = ctypes.cast(name_ptr, ctypes.c_char_p).value.decode('utf-8')
                dict_by_format[current_value.format].append(name)
        return dict_by_format


class KpmFuncDefArrWrapper():
    def __init__(self, hex: str):
        self.kpm_action_def: KpmFuncDefArr = None
        self.hex = hex
        self.free = wrap_functions(wrapper, 'free_kpm_ran_func_arr', None, [ctypes.POINTER(KpmFuncDefArr)])
        self.decode_function_def = wrap_functions(wrapper, 'get_ran_func_def_kpm_oai_wrap', KpmFuncDefArr, [ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint8)])

    def set_hex(self, hex: str):
        self.hex = hex

    def decode(self) -> KpmFuncDefArr:
        byte_string = bytes.fromhex(self.hex)
        byte_array = (ctypes.c_uint8 * len(byte_string)).from_buffer_copy(byte_string)
        self.kpm_action_def = self.decode_function_def(len(byte_array), byte_array)
        return self.kpm_action_def
    
    def __del__(self):
        if self.kpm_action_def:
            self.free(self.kpm_action_def)
            self.kpm_action_def = None
