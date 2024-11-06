import ctypes


class ran_parameter_def_type_e(ctypes.c_uint):
    LIST_RAN_PARAMETER_DEF_TYPE = 0
    STRUCTURE_RAN_PARAMETER_DEF_TYPE = 1
    END_RAN_PARAMETER_DEF_TYPE = 2