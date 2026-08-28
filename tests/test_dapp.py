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


@requires_native
def test_spectrum_report_struct_matches_the_shipped_library():
    """The ctypes mirror must match libdapp_sm.so's spectrum_sm_report_t.

    ctypes reads struct members by offset and validates nothing, so a layout that
    drifts from the shipped .so returns plausible garbage instead of failing. Pin
    the offsets that the C side fixes: long, pointer, int64 on LP64.
    """
    import ctypes
    from xdevsm.sm_framework.py_oran.dapp.e3.DAppE3IndPayload import spectrum_sm_report_t

    assert [f[0] for f in spectrum_sm_report_t._fields_] == [
        "prb_count", "prbs", "timestamp_ns"]
    assert spectrum_sm_report_t.prb_count.offset == 0
    assert spectrum_sm_report_t.prbs.offset == 8
    assert spectrum_sm_report_t.timestamp_ns.offset == 16
    assert ctypes.sizeof(spectrum_sm_report_t) == 24


@requires_native
def test_e3_ind_payload_exposes_the_report_timestamp():
    from xdevsm.sm_framework.py_oran.dapp.e3.DAppE3IndPayload import DAppE3IndPayloadWrapper

    assert callable(getattr(DAppE3IndPayloadWrapper, "get_timestamp_ns", None))
