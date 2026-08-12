"""Service Model enums are plain ctypes-int subclasses (no native .so needed to import)."""

from xdevsm.sm_framework.py_oran.dapp import enums as dapp_enums
from xdevsm.sm_framework.py_oran.kpm import enums as kpm_enums
from xdevsm.sm_framework.py_oran.rc import enums as rc_enums


def test_kpm_enums():
    assert kpm_enums.meas_value_e.INTEGER_MEAS_VALUE == 0
    assert kpm_enums.meas_value_e.REAL_MEAS_VALUE == 1
    assert kpm_enums.meas_type_enum.NAME_MEAS_TYPE == 0


def test_rc_enums():
    assert rc_enums.ran_parameter_val_type_e.STRUCTURE_RAN_PARAMETER_VAL_TYPE == 2
    assert rc_enums.ran_parameter_val_type_e.LIST_RAN_PARAMETER_VAL_TYPE == 3


def test_dapp_enums():
    assert dapp_enums.dapp_e3_sm_type_e.DAPP_E3_SM_NONE == 0
    assert dapp_enums.dapp_e3_sm_type_e.DAPP_E3_SM_SPECTRUM == 1
    assert dapp_enums.e2sm_dapp_ind_hdr_format_e.FORMAT_1_E2SM_DAPP_IND_HDR == 0
