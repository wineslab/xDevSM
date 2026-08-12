"""E2SM-DAPP objects. Encoders call libdapp_sm.so; no RIC/RMR required.

Import + symbol binding checks only; the native encode/decode entry points require valid
inputs (the C library aborts on malformed buffers) and are covered by integration tests.
"""

from _env import requires_native

from xdevsm.sm_framework.py_oran.dapp.enums import dapp_e3_sm_type_e


def test_dapp_sm_type_enum_values():
    assert dapp_e3_sm_type_e.DAPP_E3_SM_NONE == 0
    assert dapp_e3_sm_type_e.DAPP_E3_SM_SPECTRUM == 1


@requires_native
def test_dapp_modules_bind_native_symbols():
    from xdevsm.sm_framework.py_oran.dapp.control.DAppControlReq import (
        DAppControlReqWrapper,
    )
    from xdevsm.sm_framework.py_oran.dapp.e3.DAppE3CtrlPayload import (
        DAppE3CtrlPayloadWrapper,
    )
    from xdevsm.sm_framework.py_oran.dapp.report.DAppActionDef import DAppActionDefWrapper
    from xdevsm.sm_framework.py_oran.dapp.report.DAppEvTrigger import DAppEvTriggerWrapper

    for cls in (
        DAppControlReqWrapper,
        DAppE3CtrlPayloadWrapper,
        DAppActionDefWrapper,
        DAppEvTriggerWrapper,
    ):
        assert isinstance(cls, type)
