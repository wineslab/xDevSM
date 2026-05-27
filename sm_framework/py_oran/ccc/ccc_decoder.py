"""
Pure-Python JSON decoders for the E2SM-CCC IEs received from the RIC.

The FlexRIC ccc_sm plugin forwards the on-wire JSON bytes verbatim into
the indication header / message OCTET STRINGs, so on the dApp side we
just need `json.loads`. Two thin wrappers expose the decoded dicts and
a few helpers to drill into Indication Message Format 2 (cell-level).
"""
import json
from typing import Iterator, List, Optional


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
