import ctypes

def read_file(filename):
    try:
        with open(filename, 'r') as f:
            data = f.read()
            if len(data) == 0:
                return None
            return data
    except IOError as error:
        return None

def get_c_byte_array_from_py_byte_string(byte_string: bytes):
    try:
        byte_data = bytes(byte_string.decode('unicode_escape').encode('latin-1'))
        byte_array = (ctypes.c_uint8 * len(byte_data)).from_buffer_copy(byte_data)

        return byte_array
    except:
        print("exception in byte array")
        return None