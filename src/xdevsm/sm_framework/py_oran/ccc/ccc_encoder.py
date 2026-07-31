import ctypes
import json
from typing import List, Optional

from xdevsm.sm_framework.py_oran.ccc.constants import (
    EVENT_TRIGGER_FORMAT_PERIODIC,
    ACTION_DEF_FORMAT_CELL_LEVEL,
    REPORT_STYLE_CELL_LEVEL,
    REPORT_TYPE_ALL,
)


class CCCByteArray:
    """Drop-in replacement for ByteArray with a `byte_array_to_tuple`
    method matching the xAppReportService.send_subscription contract.

    Holds the raw bytes in a ctypes uint8 array so the lifetime survives
    the subscription POST call.
    """

    def __init__(self, raw: bytes):
        self._raw = raw
        arr_type = ctypes.c_uint8 * len(raw)
        self._buf = arr_type.from_buffer_copy(raw)
        self.len = len(raw)
        self.buf = ctypes.cast(self._buf, ctypes.POINTER(ctypes.c_uint8))

    def byte_array_to_tuple(self):
        return tuple(self._raw)

    def to_bytes(self) -> bytes:
        return bytes(self._raw)


def encode_event_trigger_periodic(period_ms: int) -> CCCByteArray:
    """E2SM-CCC Event Trigger Definition Format 3 (periodic, §9.2.1.1.3).

    The single field `period` is in milliseconds (range 10..4294967295).
    """
    obj = {
        "eventTriggerDefinitionFormat": {
            "period": int(period_ms),
        }
    }
    return CCCByteArray(json.dumps(obj, separators=(",", ":")).encode("utf-8"))


def encode_action_definition_cell_level(
    ran_cfg_structure_name: str,
    attribute_names: List[str],
    cell_global_id: Optional[dict] = None,
    report_type: str = REPORT_TYPE_ALL,
    ric_style_type: int = REPORT_STYLE_CELL_LEVEL,
) -> CCCByteArray:
    """E2SM-CCC Action Definition Format 2 (cell-level, §9.2.1.2.2).

    Parameters
    ----------
    ran_cfg_structure_name : e.g. "O-NRCellDU"
    attribute_names : e.g. ["arfcnDL", "bSChannelBwDL", "bWPList"]
    cell_global_id : optional dict matching NR-CGI ({"plmnIdentity":{...},
                     "nRCellIdentity":"<9-hex>"}); when omitted the action
                     applies to all cells of the E2 Node.
    """
    one_struct = {
        "reportType": report_type,
        "ranConfigurationStructureName": ran_cfg_structure_name,
        "listOfAttributes": [
            {"attributeName": n} for n in attribute_names
        ],
    }
    one_cell = {
        "listOfCellLevelRANConfigurationStructuresForADF": [one_struct]
    }
    if cell_global_id is not None:
        one_cell["cellGlobalId"] = cell_global_id

    obj = {
        "ricStyleType": int(ric_style_type),
        "actionDefinitionFormat": {
            "listOfCellConfigurationsToBeReportedForADF": [one_cell]
        },
    }
    return CCCByteArray(json.dumps(obj, separators=(",", ":")).encode("utf-8"))
