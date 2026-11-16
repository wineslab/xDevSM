import json
from typing import Iterator, List, NamedTuple, Optional

from xdevsm.sm_framework.py_oran.ccc.ccc_encoder import nr_cell_id_of
from xdevsm.sm_framework.py_oran.ccc.constants import SM_CCC_OID, SM_CCC_OID_OCUDU

CCC_OIDS = (SM_CCC_OID, SM_CCC_OID_OCUDU)


def find_ccc_function_id(json_ran_info) -> int:
    """Return the E2SM-CCC RAN function ID in an E2 node's e2mgr info; raise LookupError if absent."""
    functions = ((json_ran_info or {}).get("gnb") or {}).get("ranFunctions") or []
    for ran_func in functions:
        if ran_func.get("ranFunctionOid") in CCC_OIDS:
            return ran_func["ranFunctionId"]
    raise LookupError("the E2 node announces no E2SM-CCC RAN function")


class CccIndicationHeader:
    """Wrapper around an E2SM-CCC Indication Header Format 1 payload."""

    def __init__(self, raw: bytes):
        self.raw = raw
        try:
            outer = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
            outer = {}
        self.payload = outer.get("indicationHeaderFormat", outer) or {}

    @property
    def indication_reason(self) -> Optional[str]:
        return self.payload.get("indicationReason")

    @property
    def event_time(self) -> Optional[str]:
        return self.payload.get("eventTime")

    def __repr__(self):
        return (
            f"CccIndicationHeader(reason={self.indication_reason!r}, "
            f"event_time={self.event_time!r})"
        )


class CccIndicationMessage:
    """Wrapper around an E2SM-CCC Indication Message Format 2 payload.

    Provides convenience accessors for iterating over reported cells and
    the configuration structures they carry.
    """

    def __init__(self, raw: bytes):
        self.raw = raw
        try:
            outer = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
            outer = {}
        self.payload = outer.get("indicationMessageFormat", outer) or {}

    def cells(self) -> List[dict]:
        return self.payload.get("listOfCellsReported", []) or []

    def iter_structures(self) -> Iterator[dict]:
        """Yield (cell, structure) tuples (Indication Message Format 2)."""
        for c in self.cells():
            for s in c.get("listOfConfigurationStructuresReported", []) or []:
                yield c, s

    def find_o_nr_cell_du(self) -> List[dict]:
        """Return all O-NRCellDU `valuesOfAttributes.ranConfigurationStructure`
        dicts reported across all cells in this indication."""
        out = []
        for _, s in self.iter_structures():
            if s.get("ranConfigurationStructureName") == "O-NRCellDU":
                vs = (s.get("valuesOfAttributes") or {}).get("ranConfigurationStructure") or {}
                out.append(vs)
        return out

    def __repr__(self):
        return f"CccIndicationMessage(cells={len(self.cells())})"


class CccStructureOutcome(NamedTuple):
    """The outcome of one configuration structure of a control request"""

    nr_cell_id: Optional[int]
    ran_cfg_structure_name: str
    applied: bool
    failure_reason: str
    applied_values: dict


def _values(attributes) -> dict:
    return dict((attributes or {}).get("ranConfigurationStructure") or {}) if isinstance(attributes, dict) else {}


def _structure_outcomes(nr_cell_id: Optional[int], outcome: dict) -> List[CccStructureOutcome]:
    out = [CccStructureOutcome(nr_cell_id, s.get("ranConfigurationStructureName", ""), True, "",
                               _values(s.get("currentValuesOfAttributes")))
           for s in outcome.get("ranConfigurationStructuresAcceptedList", []) or []]
    out += [CccStructureOutcome(nr_cell_id, s.get("ranConfigurationStructureName", ""), False, str(s.get("cause", "")),
                                {})
            for s in outcome.get("ranConfigurationStructuresFailedList", []) or []]
    return out


class CccControlOutcome:
    """Wrapper around an E2SM-CCC RIC Control Outcome, Format 1 (node level) or Format 2 (cell level).

    OCUDU sends the format without the controlOutcomeFormat wrapper. An accepted structure carries its
    currentValuesOfAttributes as ``applied_values``, a failed one its cause as ``failure_reason``.
    """

    def __init__(self, raw: bytes):
        self.raw = raw
        try:
            outer = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
            outer = {}
        if not isinstance(outer, dict):
            outer = {}
        self.payload = outer.get("controlOutcomeFormat", outer) or {}

    def structures(self) -> List[CccStructureOutcome]:
        out = _structure_outcomes(None, self.payload)
        for cell in self.payload.get("listOfCellsForControlOutcome", []) or []:
            out += _structure_outcomes(nr_cell_id_of(cell.get("cellGlobalId")), cell)
        return out

    @property
    def all_applied(self) -> bool:
        structures = self.structures()
        return bool(structures) and all(s.applied for s in structures)

    def __repr__(self):
        return f"CccControlOutcome({self.structures()!r})"
