"""CCC (E2SM-CCC) is a pure-Python JSON codec — no native .so, no RIC/RMR."""

import json
import logging

import pytest

from xdevsm.sm_framework.py_oran.ccc import constants as ccc_const
from xdevsm.sm_framework.py_oran.ccc.ccc_decoder import (
    CccIndicationHeader,
    CccIndicationMessage,
)
from xdevsm.sm_framework.py_oran.ccc.ccc_encoder import (
    RrmPolicySlice,
    encode_action_definition_cell_level,
    encode_control_header,
    encode_event_trigger_periodic,
    encode_rrm_policy_ratio_control,
)

from _env import requires_ricxappframe


def test_constants():
    assert ccc_const.SM_CCC_ID == 149
    assert ccc_const.STRUCT_O_NRCELLDU == "O-NRCellDU"
    assert ccc_const.EVENT_TRIGGER_FORMAT_PERIODIC == 3


def test_encode_event_trigger_periodic_roundtrips_json():
    ba = encode_event_trigger_periodic(1000)
    payload = json.loads(ba.to_bytes())
    assert payload["eventTriggerDefinitionFormat"]["period"] == 1000


def test_encode_action_definition_cell_level_contains_attributes():
    ba = encode_action_definition_cell_level("O-NRCellDU", ["arfcnDL", "bSChannelBwDL"])
    payload = json.loads(ba.to_bytes())
    # The exact JSON shape is codec-defined; assert the essentials survive the round-trip.
    blob = json.dumps(payload)
    assert "O-NRCellDU" in blob
    assert "arfcnDL" in blob
    assert "bSChannelBwDL" in blob


def test_indication_header_reads_reason():
    raw = b'{"indicationHeaderFormat":{"indicationReason":"periodic","eventTime":"2024-01-01T00:00:00Z"}}'
    hdr = CccIndicationHeader(raw)
    assert hdr.indication_reason == "periodic"
    assert hdr.event_time == "2024-01-01T00:00:00Z"


def test_indication_message_iterates_cells():
    raw = (
        b'{"indicationMessageFormat":{"listOfCellsReported":['
        b'{"cellGlobalId":{"nrCellId":"1"},"listOfConfigurationStructuresReported":['
        b'{"ranConfigurationStructureName":"O-NRCellDU","valuesOfAttributes":{"arfcnDL":620000}}]}]}}'
    )
    msg = CccIndicationMessage(raw)
    cells = msg.cells()
    assert len(cells) == 1
    structures = list(msg.iter_structures())
    assert structures, "expected at least one (cell, structure) pair"


def test_decoders_are_defensive_on_empty_input():
    assert CccIndicationMessage(b"").cells() == []
    # A header with no recognizable fields should not raise.
    assert CccIndicationHeader(b"").indication_reason is None


SLICE_SD = RrmPolicySlice(sst=1, sd="000001", min_ratio=57, max_ratio=79)
PLMN = {"mcc": "001", "mnc": "01"}


def _structure(payload):
    cell = payload["controlMessageFormat"]["listOfCellsControlled"][0]
    return cell["listOfConfigurationStructures"][0]


def test_control_header_json():
    assert encode_control_header().to_bytes() == b'{"controlHeaderFormat":{"ricStyleType":2}}'


def test_rrm_policy_ratio_message_with_sd():
    ba = encode_rrm_policy_ratio_control("001", "01", 3669 << 14, [SLICE_SD])
    payload = json.loads(ba.to_bytes())
    cell = payload["controlMessageFormat"]["listOfCellsControlled"][0]
    assert cell["cellGlobalId"] == {"plmnIdentity": PLMN, "nRCellIdentity": "003954000"}
    struct = _structure(payload)
    assert struct["ranConfigurationStructureName"] == "O-RRMPolicyRatio"
    assert struct["oldValuesOfAttributes"]["ranConfigurationStructure"] == {
        "resourceType": "PRB_DL",
        "rRMPolicyMemberList": [{"plmnId": PLMN, "snssai": {"sst": 1, "sd": "000001"}}],
    }
    assert struct["newValuesOfAttributes"]["ranConfigurationStructure"] == {
        "resourceType": "PRB_DL",
        "rRMPolicyMemberList": [{"plmnId": PLMN, "snssai": {"sst": 1, "sd": "000001"}}],
        "rRMPolicyMinRatio": 57,
        "rRMPolicyMaxRatio": 79,
        "rRMPolicyDedicatedRatio": 0,
    }


def test_rrm_policy_ratio_message_without_sd():
    ba = encode_rrm_policy_ratio_control(
        "001", "01", 1, [{"sst": 1, "min_ratio": 10, "max_ratio": 20}], resource_type="PRB_UL"
    )
    new = _structure(json.loads(ba.to_bytes()))["newValuesOfAttributes"]["ranConfigurationStructure"]
    assert new["resourceType"] == "PRB_UL"
    assert new["rRMPolicyMemberList"][0]["snssai"] == {"sst": 1}


def test_nci_hex_is_upper_case_zero_padded():
    ba = encode_rrm_policy_ratio_control("001", "01", 0xABC, [SLICE_SD])
    cell = json.loads(ba.to_bytes())["controlMessageFormat"]["listOfCellsControlled"][0]
    assert cell["cellGlobalId"]["nRCellIdentity"] == "000000ABC"


def test_dedicated_ratio_is_sent_as_given_and_stays_within_min():
    sl = RrmPolicySlice(sst=1, min_ratio=0, max_ratio=100, dedicated_ratio=0)
    new = _structure(json.loads(encode_rrm_policy_ratio_control("001", "01", 1, [sl]).to_bytes()))
    assert new["newValuesOfAttributes"]["ranConfigurationStructure"]["rRMPolicyDedicatedRatio"] == 0
    with pytest.raises(ValueError):
        encode_rrm_policy_ratio_control("001", "01", 1, [RrmPolicySlice(sst=1, min_ratio=0, max_ratio=100,
                                                                        dedicated_ratio=1)])


def test_sst_plmn_and_cell_min_sum_are_checked():
    encode_rrm_policy_ratio_control("001", "001", 1, [SLICE_SD])
    for mcc, mnc in (("01", "01"), ("001", "1"), (1, "01"), ("001", "0001"), ("00a", "01")):
        with pytest.raises(ValueError):
            encode_rrm_policy_ratio_control(mcc, mnc, 1, [SLICE_SD])
    with pytest.raises(ValueError):
        encode_rrm_policy_ratio_control("001", "01", 1, [RrmPolicySlice(sst=256, min_ratio=0, max_ratio=10)])
    encode_rrm_policy_ratio_control("001", "01", 1, [RrmPolicySlice(sst=1, min_ratio=60, max_ratio=90),
                                                     RrmPolicySlice(sst=2, min_ratio=40, max_ratio=90)])
    with pytest.raises(ValueError):
        encode_rrm_policy_ratio_control("001", "01", 1, [RrmPolicySlice(sst=1, min_ratio=60, max_ratio=90),
                                                         RrmPolicySlice(sst=2, min_ratio=41, max_ratio=90)])


def test_min_above_max_raises():
    sl = RrmPolicySlice(sst=1, min_ratio=80, max_ratio=79)
    with pytest.raises(ValueError):
        encode_rrm_policy_ratio_control("001", "01", 1, [sl])


def test_ratio_out_of_range_raises():
    sl = RrmPolicySlice(sst=1, min_ratio=0, max_ratio=101)
    with pytest.raises(ValueError):
        encode_rrm_policy_ratio_control("001", "01", 1, [sl])


def test_invalid_resource_type_raises():
    with pytest.raises(ValueError):
        encode_rrm_policy_ratio_control("001", "01", 1, [SLICE_SD], resource_type="PRB")


@requires_ricxappframe
def test_send_policies_sends_all_slices_in_one_control():
    from xdevsm.decorators.ccc.ccc_rrm_policy_control import CccRrmPolicyRatioControl

    sent = []
    ctrl = object.__new__(CccRrmPolicyRatioControl)
    ctrl.mcc, ctrl.mnc, ctrl.nci = "001", "01", 1
    ctrl.logger = logging.getLogger("test")
    ctrl.send_control_request_rmr = lambda **kw: sent.append(kw)
    other = RrmPolicySlice(sst=2, min_ratio=5, max_ratio=15)
    ctrl.send_policies("gnb_1", [SLICE_SD, other])
    (msg,) = sent
    assert msg["e2_node_id"] == "gnb_1"
    assert msg["control_header"] == b'{"controlHeaderFormat":{"ricStyleType":2}}'
    (cell,) = json.loads(msg["control_message"])["controlMessageFormat"]["listOfCellsControlled"]
    assert [s["newValuesOfAttributes"]["ranConfigurationStructure"]["rRMPolicyMemberList"][0]["snssai"]["sst"]
            for s in cell["listOfConfigurationStructures"]] == [1, 2]


@requires_ricxappframe
def test_a_three_slice_control_goes_through_the_real_e2ap_encoding():
    # Needs ricxappframe patch 004: upstream encodes a control request into a fixed 1024-byte buffer.
    from ricxappframe.e2ap.asn1 import ControlRequestMsg

    slices = [RrmPolicySlice(sst=i, sd=f"00000{i}", min_ratio=10, max_ratio=90, dedicated_ratio=5) for i in (1, 2, 3)]
    header = encode_control_header().to_bytes()
    message = encode_rrm_policy_ratio_control("001", "01", 3669 << 14, slices).to_bytes()
    size, payload = ControlRequestMsg().encode(requestor_id=1, request_sequence_number=1, ran_function_id=4,
                                               call_process_id=b"", control_header=header,
                                               control_message=message, control_ack_request=1)
    assert len(message) > 1024
    assert size == len(payload)  # the bytes of the PDU, not a zero-padded buffer
    assert header in payload and message in payload


def test_find_ccc_function_id_matches_both_oids():
    from xdevsm.sm_framework.py_oran.ccc.ccc_decoder import find_ccc_function_id

    def info(oid):
        return {"gnb": {"ranFunctions": [{"ranFunctionId": 2, "ranFunctionOid": "kpm"},
                                         {"ranFunctionId": 4, "ranFunctionOid": oid}]}}

    assert find_ccc_function_id(info(ccc_const.SM_CCC_OID_OCUDU)) == 4
    assert find_ccc_function_id(info(ccc_const.SM_CCC_OID)) == 4
    with pytest.raises(LookupError):
        find_ccc_function_id(info("other"))
    with pytest.raises(LookupError):
        find_ccc_function_id(None)


def test_numpy_like_and_float_ratios():
    class IntLike(int):
        pass

    sl = RrmPolicySlice(sst=1, min_ratio=IntLike(0), max_ratio=IntLike(40))
    new = _structure(json.loads(encode_rrm_policy_ratio_control("001", "01", 1, [sl]).to_bytes()))
    assert type(new["newValuesOfAttributes"]["ranConfigurationStructure"]["rRMPolicyMaxRatio"]) is int
    with pytest.raises(ValueError):
        encode_rrm_policy_ratio_control("001", "01", 1, [RrmPolicySlice(sst=1, min_ratio=0, max_ratio=37.5)])


def test_bad_sd_and_dedicated_above_max_raise():
    with pytest.raises(ValueError):
        encode_rrm_policy_ratio_control("001", "01", 1, [RrmPolicySlice(sst=1, sd="1", min_ratio=0, max_ratio=10)])
    with pytest.raises(ValueError):
        encode_rrm_policy_ratio_control("001", "01", 1, [RrmPolicySlice(sst=1, min_ratio=0, max_ratio=10, dedicated_ratio=20)])


@requires_ricxappframe
def test_send_policies_sends_nothing_if_a_later_slice_is_invalid():
    from xdevsm.decorators.ccc.ccc_rrm_policy_control import CccRrmPolicyRatioControl

    sent = []
    ctrl = object.__new__(CccRrmPolicyRatioControl)
    ctrl.mcc, ctrl.mnc, ctrl.nci = "001", "01", 1
    ctrl.logger = logging.getLogger("test")
    ctrl.send_control_request_rmr = lambda **kw: sent.append(kw)
    with pytest.raises(ValueError):
        ctrl.send_policies("gnb_1", [SLICE_SD, RrmPolicySlice(sst=2, min_ratio=50, max_ratio=40)])
    with pytest.raises(ValueError):
        ctrl.send_policies("gnb_1", [])
    assert sent == []


# Control outcome that OCUDU packs for an accepted control (convert_to_e2sm_response in
# lib/e2/e2sm/e2sm_ccc/e2sm_ccc_control_action_du_executor.cpp, branch feature/e2sm_ccc_report): Format 2 without the
# controlOutcomeFormat wrapper, the request's old values as oldValuesOfAttributes and its new values as
# currentValuesOfAttributes.
OCUDU_NEW_VALUES = {"resourceType": "PRB_DL",
                    "rRMPolicyMemberList": [{"plmnId": PLMN, "snssai": {"sst": 1, "sd": "000001"}}],
                    "rRMPolicyMaxRatio": 79, "rRMPolicyMinRatio": 57, "rRMPolicyDedicatedRatio": 1}
OCUDU_ACCEPTED_OUTCOME = json.dumps({"listOfCellsForControlOutcome": [{
    "cellGlobalId": {"plmnIdentity": PLMN, "nRCellIdentity": "003954000"},
    "ranConfigurationStructuresAcceptedList": [{
        "ranConfigurationStructureName": "O-RRMPolicyRatio",
        "oldValuesOfAttributes": {"ranConfigurationStructure": {"resourceType": "PRB_DL"}},
        "currentValuesOfAttributes": {"ranConfigurationStructure": OCUDU_NEW_VALUES}}]}]}).encode()
OCUDU_FAILED_OUTCOME = json.dumps({"listOfCellsForControlOutcome": [{
    "cellGlobalId": {"plmnIdentity": PLMN, "nRCellIdentity": "003954000"},
    "ranConfigurationStructuresFailedList": [{
        "ranConfigurationStructureName": "O-RRMPolicyRatio",
        "oldValuesOfAttributes": {"ranConfigurationStructure": {"resourceType": "PRB_DL"}},
        "requestedValuesOfAttributes": {"ranConfigurationStructure": OCUDU_NEW_VALUES},
        "cause": "Unspecified"}]}]}).encode()


def test_ocudu_accepted_control_outcome():
    from xdevsm.sm_framework.py_oran.ccc.ccc_decoder import CccControlOutcome, CccStructureOutcome

    outcome = CccControlOutcome(OCUDU_ACCEPTED_OUTCOME)
    assert outcome.structures() == [CccStructureOutcome(3669 << 14, "O-RRMPolicyRatio", True, "", OCUDU_NEW_VALUES)]
    assert outcome.all_applied
    wrapped = CccControlOutcome(json.dumps({"controlOutcomeFormat": json.loads(OCUDU_ACCEPTED_OUTCOME)}).encode())
    assert wrapped.structures() == outcome.structures()


def test_ocudu_failed_control_outcome():
    from xdevsm.sm_framework.py_oran.ccc.ccc_decoder import CccControlOutcome

    outcome = CccControlOutcome(OCUDU_FAILED_OUTCOME)
    (failed,) = outcome.structures()
    assert (failed.applied, failed.failure_reason, failed.applied_values) == (False, "Unspecified", {})
    assert not outcome.all_applied


def test_control_outcome_is_defensive_on_other_payloads():
    from xdevsm.sm_framework.py_oran.ccc.ccc_decoder import CccControlOutcome

    for raw in (b"", b"{", b"[1]", b'{"listOfCellsForControlOutcome": []}'):
        assert CccControlOutcome(raw).structures() == []
        assert not CccControlOutcome(raw).all_applied


class _AckMsgStub:
    outcome = OCUDU_ACCEPTED_OUTCOME

    def decode(self, pdu):
        if pdu != b"ack":
            raise ValueError("not an acknowledge")
        self.request_id, self.function_id, self.control_outcome = 7, 4, self.outcome


class _FailureMsgStub:
    def decode(self, pdu):
        if pdu != b"failure":
            raise ValueError("not a failure")
        self.request_id, self.function_id, self.control_outcome = 8, 4, OCUDU_FAILED_OUTCOME
        self.cause_type, self.cause_value = 1, 1  # ricRequest, action-not-supported


@requires_ricxappframe
def test_decode_ccc_control_ack_reads_the_json_outcome(monkeypatch):
    from xdevsm.decorators.ccc import ccc_control

    monkeypatch.setattr(ccc_control, "ControlAckMsg", _AckMsgStub)
    monkeypatch.setattr(ccc_control, "ControlFailureMsg", _FailureMsgStub)
    ack = ccc_control.decode_ccc_control_ack(b"ack")
    assert (ack.ric_requestor_id, ack.ran_function_id, ack.cause) == (7, 4, None)
    assert ack.outcome.all_applied
    failure = ccc_control.decode_ccc_control_ack(b"failure")
    assert (failure.ric_requestor_id, failure.cause) == (8, (1, 1))
    assert not failure.outcome.all_applied
    assert ccc_control.decode_ccc_control_ack(b"not an E2AP PDU") is None
    assert ccc_control.decode_ccc_control_ack(b"") is None


@requires_ricxappframe
def test_a_control_without_its_own_decoder_hands_the_rmr_summary():
    from ricxappframe.xapp_frame import rmr
    from xdevsm.decorators.control import xAppControlService

    ctrl = object.__new__(xAppControlService)
    ctrl.logger = logging.getLogger("test")
    received = []
    ctrl.register_control_ack_suc_callback(received.append)
    summary = {rmr.RMR_MS_PAYLOAD: b"ack", "meid": b"gnb_1"}
    ctrl._handle_control_ack_suc(None, summary, None)
    assert received == [summary]


@requires_ricxappframe
def test_ccc_control_ack_callbacks_get_the_ccc_outcome(monkeypatch):
    from ricxappframe.xapp_frame import rmr
    from xdevsm.decorators.ccc import ccc_control
    from xdevsm.decorators.ccc.ccc_rrm_policy_control import CccRrmPolicyRatioControl

    monkeypatch.setattr(ccc_control, "ControlAckMsg", _AckMsgStub)
    monkeypatch.setattr(ccc_control, "ControlFailureMsg", _FailureMsgStub)
    ctrl = object.__new__(CccRrmPolicyRatioControl)
    ctrl.logger = logging.getLogger("test")
    received = []
    ctrl.register_control_ack_suc_callback(received.append)
    ctrl.register_control_ack_fail_callback(received.append)
    ctrl._handle_control_ack_suc(None, {rmr.RMR_MS_PAYLOAD: b"ack", "meid": b"gnb_1"}, None)
    ctrl._handle_control_ack_fail(None, {rmr.RMR_MS_PAYLOAD: b"failure", "meid": b"gnb_1"}, None)
    undecodable = {rmr.RMR_MS_PAYLOAD: b"garbage", "meid": b"gnb_1"}
    ctrl._handle_control_ack_fail(None, undecodable, None)
    assert isinstance(received[0], ccc_control.CccControlAck)
    assert received[0].meid == "gnb_1" and received[0].outcome.all_applied
    assert received[1].meid == "gnb_1" and received[1].cause == (1, 1) and not received[1].outcome.all_applied
    assert received[2] is undecodable
