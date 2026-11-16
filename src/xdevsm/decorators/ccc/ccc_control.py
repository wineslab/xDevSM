from typing import Optional

from xdevsm.sm_framework.py_oran.ccc.ccc_decoder import CccControlOutcome

try:
    from ricxappframe.e2ap.asn1 import ControlAckMsg
except ImportError:  # pragma: no cover - unpatched ricxappframe: acknowledges without outcome
    ControlAckMsg = None
try:
    from ricxappframe.e2ap.asn1 import ControlFailureMsg
except ImportError:  # pragma: no cover - ricxappframe without patch 003: failures reach the callback as the RMR summary
    ControlFailureMsg = None


class CccControlAck:
    """What a RIC Control Acknowledge or Failure of a CCC control says: ``outcome`` is the decoded JSON outcome (None
    if the message carried none, or the installed ricxappframe cannot decode it). ``cause`` is the E2AP Cause of a
    failure as (choice, value), None for an acknowledge."""

    __slots__ = ("ric_requestor_id", "ran_function_id", "outcome", "cause", "meid")

    def __init__(self, ric_requestor_id, ran_function_id, outcome: Optional[CccControlOutcome], cause=None):
        self.ric_requestor_id = ric_requestor_id
        self.ran_function_id = ran_function_id
        self.outcome = outcome
        self.cause = cause
        self.meid = None

    def __repr__(self):
        return "CccControlAck(meid={}, outcome={}, cause={})".format(self.meid, self.outcome, self.cause)


def decode_ccc_control_ack(pdu) -> Optional[CccControlAck]:
    """Decode one E2AP RIC Control Acknowledge or Failure with a CCC outcome, None if it is neither"""
    if not pdu:
        return None
    for msg_type in (ControlAckMsg, ControlFailureMsg):
        if msg_type is None:
            continue
        msg = msg_type()
        try:
            msg.decode(pdu)
        except Exception:  # not this message, or malformed
            continue
        raw = msg.control_outcome
        cause = (msg.cause_type, msg.cause_value) if msg_type is ControlFailureMsg else None
        return CccControlAck(msg.request_id, msg.function_id, CccControlOutcome(bytes(raw)) if raw else None, cause)
    return None
