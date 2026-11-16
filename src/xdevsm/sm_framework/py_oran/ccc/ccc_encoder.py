import ctypes
import json
import re
from dataclasses import dataclass
from typing import List, Optional, Sequence, Union

from xdevsm.sm_framework.py_oran.ccc.constants import (
    CONTROL_STYLE_CELL_LEVEL,
    RESOURCE_TYPE_PRB_DL,
    RESOURCE_TYPE_PRB_UL,
    STRUCT_O_RRM_POLICY_RATIO,
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


def nr_cell_id_of(cell_global_id: Optional[dict]) -> Optional[int]:
    """The NR Cell Identity of an NR CGI dict, None if it has none"""
    try:
        return int(str((cell_global_id or {})["nRCellIdentity"]), 16)
    except (KeyError, TypeError, ValueError):
        return None


MAX_RATIO = 100
_MAX_SST = 255
_NCI_HEX_DIGITS = 9
_SD_HEX_DIGITS = 6
_RESOURCE_TYPES = (RESOURCE_TYPE_PRB_DL, RESOURCE_TYPE_PRB_UL)


@dataclass(frozen=True)
class RrmPolicySlice:
    """One O-RRMPolicyRatio member: an S-NSSAI and its PRB ratios in percent."""

    sst: int
    min_ratio: int
    max_ratio: int
    sd: Optional[str] = None
    dedicated_ratio: int = 0


def _dumps(obj: dict) -> CCCByteArray:
    return CCCByteArray(json.dumps(obj, separators=(",", ":")).encode("utf-8"))


def encode_control_header(ric_style_type: int = CONTROL_STYLE_CELL_LEVEL) -> CCCByteArray:
    """E2SM-CCC RIC Control Header Format 1 (§9.2.1.5.1)."""
    return _dumps({"controlHeaderFormat": {"ricStyleType": int(ric_style_type)}})


def _as_slice(item: Union[RrmPolicySlice, dict]) -> RrmPolicySlice:
    sl = item if isinstance(item, RrmPolicySlice) else RrmPolicySlice(**item)
    values = {}
    for name, top in (("sst", _MAX_SST), ("min_ratio", MAX_RATIO), ("max_ratio", MAX_RATIO),
                      ("dedicated_ratio", MAX_RATIO)):
        value = getattr(sl, name)
        if isinstance(value, bool) or int(value) != value:
            raise ValueError(f"{name} must be an integer, got {value!r}")
        if not 0 <= value <= top:
            raise ValueError(f"{name} must be in 0..{top}, got {value}")
        values[name] = int(value)
    # TS 28.541: the dedicated share is part of the min share, which is part of the max share.
    if not values["dedicated_ratio"] <= values["min_ratio"] <= values["max_ratio"]:
        raise ValueError("ratios must satisfy dedicated_ratio <= min_ratio <= max_ratio, got {dedicated_ratio}, "
                         "{min_ratio}, {max_ratio}".format(**values))
    if sl.sd is not None and (len(sl.sd) != _SD_HEX_DIGITS or not all(c in "0123456789abcdefABCDEF" for c in sl.sd)):
        raise ValueError(f"sd must be {_SD_HEX_DIGITS} hex digits, got {sl.sd!r}")
    return RrmPolicySlice(sd=sl.sd, **values)


def validate_slices(slices: Sequence[Union[RrmPolicySlice, dict]]) -> List[RrmPolicySlice]:
    """Return the slices of one cell as RrmPolicySlice; raise ValueError (TypeError for unknown dict keys)."""
    parsed = [_as_slice(s) for s in slices]
    if not parsed:
        raise ValueError("slices must not be empty")
    # TS 28.541: the min ratios of a cell sum to at most 100 (so do the dedicated ones, each at most its min).
    # shortcut: sums only the slices of this call; the cell's policies for other slices count too, add them once
    # their current values come from a CCC report or query.
    total_min = sum(s.min_ratio for s in parsed)
    if total_min > MAX_RATIO:
        raise ValueError(f"the min_ratio of the slices sum to {total_min}, above {MAX_RATIO}")
    return parsed


def _structure(plmn: dict, sl: RrmPolicySlice, resource_type: str) -> dict:
    snssai = {"sst": sl.sst}
    if sl.sd is not None:
        snssai["sd"] = sl.sd
    member_list = [{"plmnId": plmn, "snssai": snssai}]
    new_attrs = {
        "resourceType": resource_type,
        "rRMPolicyMemberList": member_list,
        "rRMPolicyMinRatio": sl.min_ratio,
        "rRMPolicyMaxRatio": sl.max_ratio,
        "rRMPolicyDedicatedRatio": sl.dedicated_ratio,
    }
    # §8.1.5: the E2 node finds the policy to change from the Old Values, so they carry its resource type and member.
    # shortcut: the old ratios are left out because the xApp does not know them; add them once a CCC report or
    # query gives the cell's current values.
    old_attrs = {"resourceType": resource_type, "rRMPolicyMemberList": member_list}
    return {
        "ranConfigurationStructureName": STRUCT_O_RRM_POLICY_RATIO,
        "oldValuesOfAttributes": {"ranConfigurationStructure": old_attrs},
        "newValuesOfAttributes": {"ranConfigurationStructure": new_attrs},
    }


def encode_rrm_policy_ratio_control(
    mcc: str,
    mnc: str,
    nci: int,
    slices: Sequence[Union[RrmPolicySlice, dict]],
    resource_type: str = RESOURCE_TYPE_PRB_DL,
) -> CCCByteArray:
    """E2SM-CCC Control Message Format 2 with one O-RRMPolicyRatio per slice, for the
    36-bit `nci` and `resource_type` "PRB_DL" or "PRB_UL". Raises as `validate_slices`,
    and ValueError for a bad resource type, PLMN or NCI."""
    if resource_type not in _RESOURCE_TYPES:
        raise ValueError(f"resource_type must be one of {_RESOURCE_TYPES}, got {resource_type!r}")
    if not (isinstance(mcc, str) and re.fullmatch(r"[0-9]{3}", mcc)
            and isinstance(mnc, str) and re.fullmatch(r"[0-9]{2,3}", mnc)):
        raise ValueError(f"mcc must be 3 digits and mnc 2 or 3 digits, got {mcc!r} and {mnc!r}")
    if not 0 <= nci < 1 << 36:
        raise ValueError(f"nci must fit in 36 bits, got {nci}")
    parsed = validate_slices(slices)
    plmn = {"mcc": mcc, "mnc": mnc}
    obj = {
        "controlMessageFormat": {
            "listOfCellsControlled": [
                {
                    "cellGlobalId": {
                        "plmnIdentity": plmn,
                        "nRCellIdentity": f"{nci:0{_NCI_HEX_DIGITS}X}",
                    },
                    "listOfConfigurationStructures": [
                        _structure(plmn, sl, resource_type) for sl in parsed
                    ],
                }
            ]
        }
    }
    return _dumps(obj)
