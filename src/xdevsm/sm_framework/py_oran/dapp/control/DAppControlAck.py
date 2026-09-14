"""Decode an E2AP RIC Control Acknowledge down to the E2SM-DAPP outcome.

An xApp receives the acknowledge as raw RMR bytes, and two layers have to be
peeled: the E2AP envelope, then the Service Model's own outcome carried inside
it.

The E2AP half is ricxappframe's job. It loads ``libriclibe2ap.so`` in
``asn1clib.py`` and already wraps the control *request* encoder; the
acknowledge decoder is the missing other half, and the symbols for it
(``e2ap_decode_ric_control_acknowledge_message`` /
``e2ap_free_decoded_ric_control_ack``) are already exported by that same
library. xDevSM supplies the wrapper as a patch rather than a second shared
object -- see ``xdevsm/ricxappframe_patches``. Keeping E2AP out of
``sm_framework/lib`` matters: that directory holds Service Models, and a second
E2AP grammar beside ricxappframe's would be a second source of truth for the
same wire format.

The E2SM half stays here, where it belongs: ``DAppControlOutWrapper`` decodes
the opaque octets as an E2SM-DAPP control outcome.
"""
import ctypes

from xdevsm.sm_framework.py_oran.dapp.control.DAppControlOut import DAppControlOutWrapper

try:
    from ricxappframe.e2ap.asn1 import ControlAckMsg
except ImportError:  # pragma: no cover - unpatched ricxappframe
    # The patch has not been applied to this install. Decoding degrades to
    # None and xAppControlService hands the raw RMR summary to the callback,
    # which is what it did before any of this existed.
    ControlAckMsg = None


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
    dispatch for. None is also what an unpatched ricxappframe yields, so a
    caller cannot tell the two apart and must treat both as "no decode".
    """
    if not pdu or ControlAckMsg is None:
        return None

    ack = ControlAckMsg()
    try:
        ack.decode(pdu)
    except Exception:
        # Not a RICControlAcknowledge, or malformed.
        return None

    outcome_bytes = ack.control_outcome
    if not outcome_bytes:
        # Acknowledged with no outcome: a real answer, just an empty one.
        return DAppControlAck(ack.request_id, ack.function_id, None, None, None)

    # A ctypes array, not bytes: dapp_dec_ctrl_out_asn takes a uint8 pointer.
    outcome_buf = (ctypes.c_uint8 * len(outcome_bytes)).from_buffer_copy(outcome_bytes)
    decoded = DAppControlOutWrapper(outcome_buf).decode()
    if decoded is None:
        return DAppControlAck(ack.request_id, ack.function_id, None, None, None)

    frmt_1 = decoded.union.frmt_1
    # 0 is the wire's "unassigned" sentinel in both fields, not a value.
    ts = int(frmt_1.timestamp_ns) or None
    seq = int(frmt_1.sequence_id) or None

    apply_outcome = None
    size = int(frmt_1.e3_control_outcome_size)
    if frmt_1.e3_control_outcome and size > 0:
        apply_outcome = bytes(bytearray(frmt_1.e3_control_outcome[:size]))

    return DAppControlAck(ack.request_id, ack.function_id, ts, seq, apply_outcome)
