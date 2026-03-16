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

    def to_bytes(self):
        if not self.buf or self.len == 0:
            return b""  # Return an empty byte string if there's no data
        return bytes(ctypes.cast(self.buf, ctypes.POINTER(ctypes.c_uint8 * self.len)).contents)

    def from_hex(self, hex:str):
        byte_string = bytes.fromhex(hex)
        byte_array = (ctypes.c_uint8 * len(byte_string)).from_buffer_copy(byte_string)
        self.len = len(byte_array)
        self.buf = byte_array

free = wrap_functions(wrapper, 'free_byte_array', None, [ByteArray])       