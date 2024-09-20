import ctypes
import numpy as np
from sm_framework.lib.library_wrapper import wrapper, wrap_functions

class ByteArray(ctypes.Structure):
    _fields_ = [("len", ctypes.c_size_t),
                ("buf", ctypes.POINTER(ctypes.c_uint8))]

    def byte_array_to_tuple(self):
        length = self.len
        buffer_pointer = self.buf
        
        buffer_list = [buffer_pointer[i] for i in range(length)]
        
        return tuple(buffer_list)

    def cmp_str_ba(self, input_str: str):
        np_array =  np.frombuffer(bytes(input_str, 'utf-8'), dtype=np.uint8)
        buf_to_numpy = np.ctypeslib.as_array(self.buf, shape = (self.len,))
        return np.array_equal(buf_to_numpy, np_array)

free = wrap_functions(wrapper, 'free_byte_array', None, [ByteArray])       