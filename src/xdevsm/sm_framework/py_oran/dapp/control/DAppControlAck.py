"""Decode an E2AP RIC Control Acknowledge down to the E2SM-DAPP outcome.

An xApp receives the acknowledge as raw RMR bytes. ricxappframe ships no
control-acknowledge decoder, so the two layers are peeled by two FlexRIC
libraries: libe2ap_ctrl_ack_dec.so lifts the Service Model's octets out of the
E2AP PDU, and libdapp_sm.so decodes those as an E2SM-DAPP control outcome. They
are separate objects because each links its own asn1c-generated grammar.
"""
import ctypes

from xdevsm.sm_framework.lib.library_wrapper import e2ap_ctrl_ack_lib, wrap_functions
from xdevsm.sm_framework.py_oran.dapp.control.DAppControlOut import DAppControlOutWrapper


_decode_e2ap_ctrl_ack = wrap_functions(
    e2ap_ctrl_ack_lib, 'e2ap_dec_ctrl_ack', ctypes.c_bool,
    [ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint8),
     ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)), ctypes.POINTER(ctypes.c_size_t),
     ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint16)])

_free_ctrl_ack_outcome = wrap_functions(
    e2ap_ctrl_ack_lib, 'e2ap_free_ctrl_ack_outcome', None, [ctypes.POINTER(ctypes.c_uint8)])


class DAppControlAck:
    """What a RIC Control Acknowledge says about the procedure it answers.

    ``sequence_id`` is the correlation id the xApp put on its control request,
    echoed back; it identifies which decision this answers. ``apply_outcome`` is
    the Service Model's own account of applying the control -- for the Spectrum
    SM an APER Spectrum-ApplyOutcomeData -- and is None when the RAN
    acknowledged without one, which is what a rejected or timed-out control
    looks like.
    """

    __slots__ = ('ric_requestor_id', 'ran_function_id', 'timestamp_ns',
                 'sequence_id', 'apply_outcome')

    def __init__(self, ric_requestor_id, ran_function_id, timestamp_ns,
                 sequence_id, apply_outcome):
        self.ric_requestor_id = ric_requestor_id
        self.ran_function_id = ran_function_id
        self.timestamp_ns = timestamp_ns
        self.sequence_id = sequence_id
        self.apply_outcome = apply_outcome

    def __repr__(self):
        return ("DAppControlAck(sequence_id={}, timestamp_ns={}, apply_outcome={} B)"
                .format(self.sequence_id, self.timestamp_ns,
                        len(self.apply_outcome) if self.apply_outcome else 0))


def decode_control_ack(pdu):
    """Decode one E2AP RIC Control Acknowledge, or None if it is not one.

    Returns None rather than raising: an xApp's RMR callback sees whatever the
    RIC routes to it, and a PDU that does not decode is not worth unwinding the
    dispatch for.
    """
    if not pdu:
        return None

    buf = (ctypes.c_uint8 * len(pdu)).from_buffer_copy(bytes(pdu))
    outcome = ctypes.POINTER(ctypes.c_uint8)()
    outcome_len = ctypes.c_size_t(0)
    requestor_id = ctypes.c_uint32(0)
    ran_function_id = ctypes.c_uint16(0)

    ok = _decode_e2ap_ctrl_ack(len(pdu), buf,
                               ctypes.byref(outcome), ctypes.byref(outcome_len),
                               ctypes.byref(requestor_id), ctypes.byref(ran_function_id))
    if not ok:
        return None

    try:
        if not outcome or outcome_len.value == 0:
            # Acknowledged with no outcome: a real answer, just an empty one.
            return DAppControlAck(requestor_id.value, ran_function_id.value, None, None, None)
        outcome_bytes = bytes(bytearray(outcome[:outcome_len.value]))
    finally:
        # Release through the library that allocated. Also correct on the empty
        # path, where the pointer is null and free() is a no-op.
        _free_ctrl_ack_outcome(outcome)

    # A ctypes array, not bytes: dapp_dec_ctrl_out_asn takes a uint8 pointer.
    outcome_buf = (ctypes.c_uint8 * len(outcome_bytes)).from_buffer_copy(outcome_bytes)
    decoded = DAppControlOutWrapper(outcome_buf).decode()
    if decoded is None:
        return DAppControlAck(requestor_id.value, ran_function_id.value, None, None, None)

    frmt_1 = decoded.union.frmt_1
    # 0 is the wire's "unassigned" sentinel in both fields, not a value.
    ts = int(frmt_1.timestamp_ns) or None
    seq = int(frmt_1.sequence_id) or None

    apply_outcome = None
    size = int(frmt_1.e3_control_outcome_size)
    if frmt_1.e3_control_outcome and size > 0:
        apply_outcome = bytes(bytearray(frmt_1.e3_control_outcome[:size]))

    return DAppControlAck(requestor_id.value, ran_function_id.value, ts, seq, apply_outcome)
