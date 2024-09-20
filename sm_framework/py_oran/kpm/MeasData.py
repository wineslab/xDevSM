import ctypes
from sm_framework.py_oran.kpm.enums import meas_value_e, enum_value_e, meas_type_enum
from sm_framework.py_oran.ByteArray import ByteArray
from mdclogpy import Logger

from sm_framework.lib.library_wrapper import wrapper, kpm_lib, wrap_functions


class meas_record_lst_t(ctypes.Structure):
    class Union(ctypes.Union):
        _fields_ = [
            ("int_val", ctypes.c_uint32),
            ("real_val", ctypes.c_double),
            ("no_value", ctypes.c_void_p)
        ]

    _fields_ = [
        ("value", meas_value_e), 
        ("union", Union)
    ]

class meas_type_union(ctypes.Union):
    _fields_ = [
        ("name", ByteArray),  
        ("id", ctypes.c_uint16)
    ]

class meas_type_t(ctypes.Structure):
    _fields_ = [
        ("type", meas_type_enum),
        ("value", meas_type_union)
        ]

class meas_data_lst_t(ctypes.Structure):
    _fields_ = [
        ("meas_record_len", ctypes.c_size_t),
        ("meas_record_lst", ctypes.POINTER(meas_record_lst_t)),
        ("incomplete_flag", ctypes.POINTER(enum_value_e))
    ]


class meas_data_basic_t(ctypes.Structure):
    _fields_ = [
        ("meas_data_lst_len", ctypes.c_size_t),  # size_t
        ("meas_data_lst", ctypes.POINTER(meas_data_lst_t)),  # meas_data_lst_t*
        ("meas_type_len", ctypes.c_size_t),  # size_t
        ("meas_type", ctypes.POINTER(meas_type_t)),  # meas_type_t*
    ]

class meas_data_basic_mue_t(ctypes.Structure):
    _fields_ = [
        ("ue_meas_report_lst_len", ctypes.c_size_t),  # size_t
        ("meas_data", ctypes.POINTER(meas_data_basic_t)),  # meas_data_basic_t*
    ]

    def print_meas_values(self, logger: Logger):
        for i in range(self.ue_meas_report_lst_len):
            logger.info("~~~~~~~~~~ MEAS INFO data: {} ~~~~~~~~~~".format(i))
            logger.info("Analyzing UE [{}]".format(i))
            logger.info(self.meas_data[i].meas_data_lst_len)
            for j in range(self.meas_data[i].meas_data_lst_len):
                print("data [{}]".format(j))
                meas_data_lst_el = self.meas_data[i].meas_data_lst[j]
                for k in range(meas_data_lst_el.meas_record_len):
                    if self.meas_data[i].meas_type[k].type.value == meas_type_enum.NAME_MEAS_TYPE:
                        if meas_data_lst_el.meas_record_lst[k].value.value == meas_value_e.INTEGER_MEAS_VALUE:
                            self.log_values(logger, self.meas_data[i].meas_type[k].value.name, meas_data_lst_el.meas_record_lst[k])
                        elif meas_data_lst_el.meas_record_lst[k].value.value == meas_value_e.REAL_MEAS_VALUE:
                            self.log_values_real(logger, self.meas_data[i].meas_type[k].value.name, meas_data_lst_el.meas_record_lst[k])
                    else:
                        logger.info("Not supported meas type {}".format(self.meas_data[i].meas_type[k].type.name))
    

    def log_values(self, logger: Logger, byte_array: ByteArray, meas_record: meas_record_lst_t):
        if byte_array.cmp_str_ba("RRU.PrbTotDl"):
            logger.info("RRU.PrbTotDl = {} [PRBs]".format(meas_record.union.int_val))
        elif byte_array.cmp_str_ba("RRU.PrbTotUl"):
            logger.info("RRU.PrbTotUl = {} [PRBs]".format(meas_record.union.int_val))
        elif byte_array.cmp_str_ba("DRB.PdcpSduVolumeDL"):
            logger.info("DRB.PdcpSduVolumeDL = {} [kb]".format(meas_record.union.int_val))
        elif byte_array.cmp_str_ba("DRB.PdcpSduVolumeUL"):
            logger.info("DRB.PdcpSduVolumeUL = {} [kb]".format(meas_record.union.int_val))
        elif byte_array.cmp_str_ba("DRB.UEThpDl"):
            logger.info("DRB.UEThpDl - not supported")
        elif byte_array.cmp_str_ba("DRB.UEThpUl"):
            logger.info("DRB.UEThpUl - not supported")
        elif byte_array.cmp_str_ba("RRU.PrbTotDl"):
            logger.info("RRU.PrbTotDl - not supported")
        elif byte_array.cmp_str_ba("RRU.PrbTotUl"):
            logger.info("RRU.PrbTotUl - not supported")
        else:
            logger.info("Measurement Name not yet supported")

    def log_values_real(self, logger: Logger, byte_array: ByteArray, meas_record: meas_record_lst_t):
        if byte_array.cmp_str_ba("RRU.PrbTotDl"):
            logger.info("RRU.PrbTotDl = {} [PRBs]".format(meas_record.union.real_val))
        elif byte_array.cmp_str_ba("RRU.PrbTotUl"):
            logger.info("RRU.PrbTotUl = {} [PRBs]".format(meas_record.union.real_val))
        elif byte_array.cmp_str_ba("DRB.PdcpSduVolumeDL"):
            logger.info("DRB.PdcpSduVolumeDL = {} [kb]".format(meas_record.union.real_val))
        elif byte_array.cmp_str_ba("DRB.PdcpSduVolumeUL"):
            logger.info("DRB.PdcpSduVolumeUL = {} [kb]".format(meas_record.union.real_val))
        elif byte_array.cmp_str_ba("DRB.UEThpDl"):
            logger.info("DRB.UEThpDl - not supported")
        elif byte_array.cmp_str_ba("DRB.UEThpUl"):
            logger.info("DRB.UEThpUl - not supported")
        elif byte_array.cmp_str_ba("RRU.PrbTotDl"):
            logger.info("RRU.PrbTotDl - not supported")
        elif byte_array.cmp_str_ba("RRU.PrbTotUl"):
            logger.info("RRU.PrbTotUl - not supported")
        else:
            logger.info("Measurement Name not yet supported")

def decode(len, buf) -> meas_data_basic_mue_t:
    get_meas_data = wrap_functions(wrapper, 'get_basic_meas_info', meas_data_basic_mue_t, [ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint8)])

    custom_meas_struct = get_meas_data(len, buf)

    return custom_meas_struct     
