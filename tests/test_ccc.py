"""CCC (E2SM-CCC) is a pure-Python JSON codec — no native .so, no RIC/RMR."""

import json

from xdevsm.sm_framework.py_oran.ccc import constants as ccc_const
from xdevsm.sm_framework.py_oran.ccc.ccc_decoder import (
    CccIndicationHeader,
    CccIndicationMessage,
)
from xdevsm.sm_framework.py_oran.ccc.ccc_encoder import (
    encode_action_definition_cell_level,
    encode_event_trigger_periodic,
)


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
