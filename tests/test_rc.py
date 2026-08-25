"""RC (RAN Control) Service Model objects. Uses librc_1_03.so.

Import + symbol binding + module-level data checks only; the native encoders require valid
RC func-def inputs (the C library aborts otherwise) and are left to integration tests.
"""

from _env import requires_native


@requires_native
def test_rc_control_action_id_maps_present():
    from xdevsm.sm_framework.py_oran.rc import RCControlReq

    # Style -> control-action-id maps are module-level data used by the wrappers.
    assert isinstance(RCControlReq.control_action_ids_1, dict)
    assert isinstance(RCControlReq.control_action_ids_2, dict)
    assert isinstance(RCControlReq.control_action_ids_3, dict)


@requires_native
def test_rc_modules_bind_native_symbols():
    from xdevsm.sm_framework.py_oran.rc.RCControlReq import RCControlReqWrapper
    from xdevsm.sm_framework.py_oran.rc.RCFunctionDef import RCFuncDefWrapper

    assert isinstance(RCControlReqWrapper, type)
    assert isinstance(RCFuncDefWrapper, type)


@requires_native
def test_rc_report_helpers_bound_in_shipped_library():
    """The bundled librc_1_03.so must export the ``rc_report_*`` ABI.

    The codec degrades gracefully against a control-only build (it records the
    binding failure in ``_LIB_ERR`` and raises only at call time), so without this
    the RC REPORT path would silently stop working if the old library came back.
    """
    from xdevsm.sm_framework.py_oran.rc import rc_report_codec

    assert rc_report_codec._LIB_ERR is None, rc_report_codec._LIB_ERR
    assert rc_report_codec._report_lib is not None
