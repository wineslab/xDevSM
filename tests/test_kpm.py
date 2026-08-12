"""KPM (Key Performance Measurement) Service Model objects. Uses libkpm_sm.so.

These tests exercise import + symbol binding + pure-Python helpers only. The native
encode/decode entry points require valid ASN.1 inputs (the C library aborts on malformed
buffers), so they are covered by integration, not unit, tests.
"""

from _env import requires_native


@requires_native
def test_kpm_modules_bind_native_symbols():
    # Importing these binds the ctypes prototypes against libkpm_sm.so; if a symbol were
    # missing from the shipped .so this would raise at import — a real packaging check.
    from xdevsm.sm_framework.py_oran.kpm.KpmFunctionDef import KpmFuncDefArrWrapper
    from xdevsm.sm_framework.py_oran.kpm.KpmIndicationHdr import KpmIndHdrWrapper
    from xdevsm.sm_framework.py_oran.kpm.KpmIndicationMsg import KpmIndMsgWrapper

    assert all(isinstance(c, type) for c in (KpmFuncDefArrWrapper, KpmIndHdrWrapper, KpmIndMsgWrapper))


@requires_native
def test_kpm_action_array_builder_is_pure():
    from xdevsm.sm_framework.py_oran.kpm import function_definition_builder as fdb

    # action_array_builder does pure-Python parsing of a func-def payload; an empty
    # input must yield a list (no native call, no crash).
    result = fdb.action_array_builder("", ran_function_id=2, oai=True)
    assert isinstance(result, list)
