"""Decode the Spectrum SM's account of applying a PRB-block control.

The gNB tunnels a Spectrum-ApplyOutcomeData inside the E2SM-DAPP control
outcome. Both instants are CLOCK_REALTIME nanoseconds on the gNB's clock -- the
same one the dApp stamps its reports with -- so an xApp can difference them
against a report timestamp without its own clock entering the result.
"""
import ctypes

from xdevsm.sm_framework.lib.library_wrapper import dApp_lib, wrap_functions


_decode_apply_outcome = wrap_functions(
    dApp_lib, 'spectrum_sm_dec_apply_outcome', ctypes.c_bool,
    [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
     ctypes.POINTER(ctypes.c_int64), ctypes.POINTER(ctypes.c_int64),
     ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_uint16)])


def decode_apply_outcome(payload):
    """Return ``(installed_ts_ns, on_air_ts_ns, sfn, slot)``, each None if absent.

    A control that was rejected never installed; one that installed but never
    reached a scheduler tick has no on-air instant. Both are normal answers, not
    decode failures.
    """
    if not payload:
        return (None, None, None, None)

    buf = (ctypes.c_uint8 * len(payload)).from_buffer_copy(bytes(payload))
    installed = ctypes.c_int64(0)
    on_air = ctypes.c_int64(0)
    sfn = ctypes.c_uint16(0)
    slot = ctypes.c_uint16(0)

    ok = _decode_apply_outcome(buf, len(payload),
                               ctypes.byref(installed), ctypes.byref(on_air),
                               ctypes.byref(sfn), ctypes.byref(slot))
    if not ok:
        return (None, None, None, None)

    # 0 is "absent" for every field here: no instant is zero on a realtime clock,
    # and an on-air tick always names a frame.
    return (installed.value or None, on_air.value or None,
            sfn.value if on_air.value else None,
            slot.value if on_air.value else None)
