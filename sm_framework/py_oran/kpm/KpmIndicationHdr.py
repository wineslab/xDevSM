import ctypes
from ctypes import POINTER, Structure, Union, c_uint32
from sm_framework.py_oran.ByteArray import ByteArray
from sm_framework.lib.library_wrapper import kpm_lib, wrap_functions

            
class FormatIndHdrE(ctypes.c_uint):
    FORMAT_1_INDICATION_HEADER = 0
    END_INDICATION_HEADER = 1


class KpmRicIndHdrFormat1(Structure):
    _fields_ = [
        ("collectStartTime", c_uint32),
        ("fileformat_version", POINTER(ByteArray)),
        ("sender_name", POINTER(ByteArray)),
        ("sender_type", POINTER(ByteArray)),
        ("vendor_name", POINTER(ByteArray))
    ]

class KpmIndHdr(Structure):
    class TypeUnion(Union):
        _fields_ = [
            ("kpm_ric_ind_hdr_format_1", KpmRicIndHdrFormat1)
        ]

    _fields_ = [
        ("type", FormatIndHdrE),
        ("data", TypeUnion)
    ]


class KpmIndHdrWrapper():
    # Manager for decoding and memory deallocation
    def __init__(self, byte_array: ByteArray):
        self.kpm_ind_hdr: KpmIndHdr = None
        self.byte_array = byte_array
        self.free = wrap_functions(kpm_lib, 'free_kpm_ind_hdr', None, [ctypes.POINTER(KpmIndHdr)])
        self.decode_indication_header = wrap_functions(kpm_lib, 'kpm_dec_ind_hdr_asn', KpmIndHdr, [ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint8)])


    def decode(self) -> KpmIndHdr:
        self.kpm_ind_hdr = self.decode_indication_header(len(self.byte_array), self.byte_array)
        return self.kpm_ind_hdr
    
    def __del__(self):
        self.free(self.kpm_ind_hdr)
        
