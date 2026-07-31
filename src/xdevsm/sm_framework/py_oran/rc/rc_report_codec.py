"""E2SM-RC REPORT Style 1 "Message Copy" codec + NR-RRC MeasurementReport decoder.

Thin ctypes binding over the ``rc_report_*`` ABI exported by the bundled
``librc_1_03.so`` (flexric's rc_sm plus ``rc_report_api.c``). That library does the
heavy lifting in C -- flexric's rc_sm codecs + the asn1c NR-RRC decoder -- and
exposes a flat ABI:

  rc_report_ba_t   rc_report_enc_event_trigger(void);   // RIC SUBSCRIPTION event trigger
  rc_report_ba_t   rc_report_enc_action_def(void);      // REPORT Style 1 action def (RAN param RRC Message)
  rc_report_meas_t rc_report_decode(hdr,msg);           // decode indication -> per-cell (pci,rsrp,rsrq,sinr)
  void rc_report_free_ba/free_meas(...);

The library ships in ``xdevsm/sm_framework/lib/`` and is self-contained (it links
only libc/libm). Against an older, control-only build that does not export the
``rc_report_*`` symbols this module still imports -- encode/decode then raise
RuntimeError, which the data ingestor's guarded subscribe / decode paths log and
swallow (the feature stays optional).

Values come back already converted to physical units (dBm/dB) by the C side.
"""

from __future__ import annotations

import ctypes
from typing import List, Optional, Tuple

from xdevsm.sm_framework.py_oran.ByteArray import ByteArray
from xdevsm.sm_framework.lib.library_wrapper import wrap_functions, rc_lib


# REPORT Service Style 1 ("Message Copy"); RAN Parameter ID of the copied RRC msg.
RC_REPORT_STYLE_MESSAGE_COPY = 1
E2SM_RC_RS1_RRC_MESSAGE = 3


# --- ctypes structs (must mirror rc_report.h) ------------------------------

class _RcReportCell(ctypes.Structure):
    _fields_ = [
        ("pci", ctypes.c_int32),
        ("rsrp", ctypes.c_double),
        ("rsrq", ctypes.c_double),
        ("sinr", ctypes.c_double),
        ("has_rsrp", ctypes.c_int32),
        ("has_rsrq", ctypes.c_int32),
        ("has_sinr", ctypes.c_int32),
        ("is_neighbour", ctypes.c_int32),
    ]


class _RcReportMeas(ctypes.Structure):
    _fields_ = [
        ("ev_trigger_id", ctypes.c_int32),
        ("is_meas_report", ctypes.c_int32),
        ("len", ctypes.c_size_t),
        ("cells", ctypes.POINTER(_RcReportCell)),
    ]


# --- library binding (optional: absent lib -> raise at call time) ----------

_UINT8_P = ctypes.POINTER(ctypes.c_uint8)

try:
    # The RC REPORT helpers now live inside the RC SM library (librc_1_03.so),
    # already loaded by library_wrapper as rc_lib -- no separate lib to load.
    _report_lib = rc_lib
    _enc_event_trigger = wrap_functions(_report_lib, "rc_report_enc_event_trigger", ByteArray, [])
    _enc_action_def = wrap_functions(_report_lib, "rc_report_enc_action_def", ByteArray, [])
    _free_ba = wrap_functions(_report_lib, "rc_report_free_ba", None, [ByteArray])
    _decode = wrap_functions(
        _report_lib, "rc_report_decode", _RcReportMeas,
        [ctypes.c_size_t, _UINT8_P, ctypes.c_size_t, _UINT8_P])
    _free_meas = wrap_functions(_report_lib, "rc_report_free_meas", None, [ctypes.POINTER(_RcReportMeas)])
    _LIB_ERR: Optional[str] = None
except Exception as e:  # rc_report_* not present in librc_1_03.so (old control-only build)
    _report_lib = None
    _LIB_ERR = str(e)


def _require_lib():
    if _report_lib is None:
        raise RuntimeError(
            "RC REPORT helpers not available in librc_1_03.so ({}). Rebuild the "
            "RC SM (flexric-sm/rc_sm) with rc_report_api and redeploy "
            "librc_1_03.so.".format(_LIB_ERR))


def _to_bytes(x) -> bytes:
    """Normalise an indication buffer to Python bytes. The report base
    (`xAppReportService._handle_indication`) hands decode_message a ctypes
    ``c_uint8 * N`` array (from utility.get_c_byte_array_from_py_byte_string), but
    a ByteArray struct is also accepted for symmetry with the encoders."""
    if isinstance(x, ByteArray):
        return x.to_bytes()
    if isinstance(x, (bytes, bytearray)):
        return bytes(x)
    return bytes(x)  # ctypes c_uint8 array -> its payload bytes


def _own_byte_array(c_ba: ByteArray) -> ByteArray:
    """Copy a C-owned byte_array_t into a Python-owned ByteArray, then free the
    C buffer. The returned ByteArray keeps its own backing store alive."""
    data = c_ba.to_bytes()
    _free_ba(c_ba)
    out = ByteArray()
    out.from_hex(data.hex())
    return out


# --- (1) subscription encode ------------------------------------------------

def encode_report_subscription(ran_period_ms: int = 1000) -> Tuple[ByteArray, ByteArray]:
    """Return ``(event_trigger_ba, action_definition_ba)`` for REPORT Style 1
    "Message Copy" of the UL-DCCH MeasurementReport. ``ran_period_ms`` is accepted
    for interface symmetry but the trigger is message-driven, not periodic."""
    _require_lib()
    et = _enc_event_trigger()
    ad = _enc_action_def()
    if not et.len or not ad.len:
        # free whatever was allocated to avoid leaks on partial failure
        if et.len:
            _free_ba(et)
        if ad.len:
            _free_ba(ad)
        raise RuntimeError("E2SM-RC REPORT subscription encode returned empty bytes")
    return _own_byte_array(et), _own_byte_array(ad)


# --- (2)+(3) indication + NR-RRC MeasurementReport decode ------------------

class DecodedMeasReport:
    """Decoded UE MeasurementReport handed to the data ingestor callback.

    ``ue_id`` is None: RC REPORT Style 1 indication header (format 1) carries only
    the event-trigger id, not a UE identity, so the ingestor tags these with the
    cell-level sentinel. ``get_neighbor_measurements`` yields every measured cell
    (serving + neighbour) that reported RSRP, keyed by PCI, which is what the
    decision engine matches a candidate target gNB against.
    """

    def __init__(self, ue_id: Optional[int],
                 cells: List[Tuple[int, float, Optional[float], Optional[float]]],
                 is_meas_report: bool, ev_trigger_id: int):
        self.ue_id = ue_id
        self._cells = cells
        self.is_meas_report = is_meas_report
        self.ev_trigger_id = ev_trigger_id

    def get_neighbor_measurements(self) -> List[Tuple[int, float, Optional[float], Optional[float], bool]]:
        """List of ``(pci, rsrp_dbm, rsrq_db, sinr_db, is_neighbour)`` per measured
        cell. ``is_neighbour`` is False for the serving cell(s)
        (measResultServingMOList) and True for neighbour cells
        (measResultNeighCells) -- i.e. the HO target candidates. rsrq/sinr are None
        when the UE did not report them."""
        return self._cells


def decode_meas_report(ind_hdr, ind_msg) -> DecodedMeasReport:
    """Decode an E2SM-RC indication (header+message) carrying a copied RRC message
    and, if it is a MeasurementReport, extract the per-cell measurements.

    ``ind_hdr``/``ind_msg`` are whatever the report base passes to decode_message
    (ctypes c_uint8 arrays), or ByteArray -- both handled by _to_bytes."""
    _require_lib()

    hbytes = _to_bytes(ind_hdr)
    mbytes = _to_bytes(ind_msg)
    # flexric's rc_dec_ind_{hdr,msg}_asn assert on NULL/empty input (they would
    # abort the whole xApp process), so never hand them an empty buffer.
    if not hbytes or not mbytes:
        return DecodedMeasReport(None, [], False, -1)

    hbuf = (ctypes.c_uint8 * len(hbytes)).from_buffer_copy(hbytes)
    mbuf = (ctypes.c_uint8 * len(mbytes)).from_buffer_copy(mbytes)

    res = _decode(len(hbytes), ctypes.cast(hbuf, _UINT8_P),
                  len(mbytes), ctypes.cast(mbuf, _UINT8_P))

    cells: List[Tuple[int, float, Optional[float], Optional[float]]] = []
    try:
        for i in range(res.len):
            c = res.cells[i]
            if c.pci < 0 or not c.has_rsrp:
                continue  # rsrp is the ranking key; skip cells without a PCI/RSRP
            rsrq = float(c.rsrq) if c.has_rsrq else None
            sinr = float(c.sinr) if c.has_sinr else None
            cells.append((int(c.pci), float(c.rsrp), rsrq, sinr, bool(c.is_neighbour)))
        is_meas = bool(res.is_meas_report)
        ev_id = int(res.ev_trigger_id)
    finally:
        _free_meas(ctypes.byref(res))

    return DecodedMeasReport(None, cells, is_meas, ev_id)
