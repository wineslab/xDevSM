"""Round-trip tests for the reference Python latrec writer
(xdevsm._latrec.writer), byte-compatible with libe3's C latrec_hdr/latrec_rec
layout (include/libe3/latrec.h)."""

import struct
import threading
import uuid

import pytest

from xdevsm._latrec import stages, writer

_HDR = struct.Struct("<IIQQQQ64s")
_HDR_V2 = struct.Struct("<IIQQ")
_V2_OFF = 104
_REC = struct.Struct("<QQQQ")


def _unique_name() -> str:
    return f"test.{uuid.uuid4().hex}"


def test_stamp_is_noop_without_latrec_dir(monkeypatch, tmp_path):
    # LATREC_DIR unset, so tmp_path is not the target and stays empty either
    # way: assert on the ring itself, not on the directory.
    monkeypatch.delenv("LATREC_DIR", raising=False)
    r = writer.LatRec(_unique_name())
    assert r.enabled is False
    assert r._mm is None
    r.stamp(1, 0x60)  # must not raise
    r.heartbeat()
    r.close()


def test_ring_created_with_valid_header(monkeypatch, tmp_path):
    monkeypatch.setenv("LATREC_DIR", str(tmp_path))
    name = _unique_name()
    r = writer.LatRec(name, entries_log2=4)
    assert r.enabled is True
    path = tmp_path / f"{name}.latrec"
    assert path.exists()
    assert not (tmp_path / f"{name}.latrec.part").exists()  # renamed atomically

    data = path.read_bytes()
    magic, version, entries, rec_count, t0_mono, t0_real, ring_name = _HDR.unpack_from(data, 0)
    assert magic == writer.MAGIC == 0x31524C41
    assert version == writer.VERSION == 2
    assert entries == 16  # 1 << 4
    assert rec_count == 0
    assert ring_name.rstrip(b"\x00").decode() == name

    rec_size, clock_ns_per_call, t1_mono, t1_real = _HDR_V2.unpack_from(data, _V2_OFF)
    assert rec_size == 32
    assert t1_mono == t0_mono and t1_real == t0_real  # not yet refreshed
    r.close()


def test_stamp_round_trips_seq_stage_aux(monkeypatch, tmp_path):
    monkeypatch.setenv("LATREC_DIR", str(tmp_path))
    name = _unique_name()
    r = writer.LatRec(name, entries_log2=4)

    r.stamp(seq=42, stage=0x60, aux=1234, aux2=5)
    r.heartbeat()
    r.close()

    data = (tmp_path / f"{name}.latrec").read_bytes()
    _, _, entries, rec_count, *_ = _HDR.unpack_from(data, 0)
    assert rec_count == 1

    off = writer.HDR_LEN
    sc, t_ns, aux, aux2 = _REC.unpack_from(data, off)
    seq = sc & 0x0000FFFFFFFFFFFF
    stage = (sc >> 56) & 0xFF
    assert seq == 42
    assert stage == 0x60
    assert aux == 1234
    assert aux2 == 5
    assert t_ns != 0  # last-written field marks the record valid


def test_ring_wraps_without_error(monkeypatch, tmp_path):
    monkeypatch.setenv("LATREC_DIR", str(tmp_path))
    name = _unique_name()
    r = writer.LatRec(name, entries_log2=2)  # only 4 slots
    for i in range(10):
        r.stamp(seq=i, stage=0x63)
    r.close()


def test_seq_next_is_monotonic_and_process_wide():
    a = writer.seq_next()
    b = writer.seq_next()
    assert b == a + 1


def test_ctx_set_get_is_per_thread():
    writer.ctx_set(7)
    assert writer.ctx_get() == 7

    seen = {}

    def other_thread():
        seen["before"] = writer.ctx_get()  # unset on a fresh thread -> 0
        writer.ctx_set(99)
        seen["after"] = writer.ctx_get()

    t = threading.Thread(target=other_thread)
    t.start()
    t.join()

    assert seen["before"] == 0
    assert seen["after"] == 99
    assert writer.ctx_get() == 7  # unaffected by the other thread


def test_ring_singleton_by_name(monkeypatch, tmp_path):
    monkeypatch.setenv("LATREC_DIR", str(tmp_path))
    name = _unique_name()
    r1 = writer.ring(name)
    r2 = writer.ring(name)
    assert r1 is r2


def test_stage_ids_match_libe3_catalog():
    """The stage ids are a cross-repo namespace owned by libe3's catalog, and
    nothing at runtime catches a value that drifts from it -- the join just
    goes silently wrong. Pin them here so a change has to be deliberate.

    Source: wineslab/libe3 include/libe3/latrec.h, the LATREC_* enum.
    """
    assert stages.ENCODE_E2AP_BEGIN == 0x58
    assert stages.ENCODE_E2AP_DONE == 0x59
    assert stages.DECODE_E2AP_BEGIN == 0x5A
    assert stages.DECODE_E2AP_DONE == 0x5B
    assert stages.DECODE_E2SM_BEGIN == 0x60
    assert stages.DECODE_E2SM_DONE == 0x61
    assert stages.ENCODE_E2SM_BEGIN == 0x63
    assert stages.ENCODE_E2SM_DONE == 0x64
    # 0x62 (XAPP_PROCESS_DONE) is B4's exit -- the application's own decision,
    # stamped by the xApp, deliberately not by this framework.
    assert not hasattr(stages, "XAPP_PROCESS_DONE")
    # libe3's converter keys per-component tables off the ring role.
    assert stages.LATREC_ROLE == "xdevsm"


def test_entries_log2_keys_off_role_not_ring_name(monkeypatch, tmp_path):
    """A ring is named <role>.<tid> but sized from LATREC_ENTRIES_LOG2_<ROLE>.
    Deriving the key from the full name would bake in a thread id no operator
    can predict, leaving the knob unsettable."""
    monkeypatch.setenv("LATREC_DIR", str(tmp_path))
    monkeypatch.setenv("LATREC_ENTRIES_LOG2_XDEVSM", "12")
    r = writer.LatRec("xdevsm.987654", entries_log2=18, role="xdevsm")
    assert r.enabled is True
    data = (tmp_path / "xdevsm.987654.latrec").read_bytes()
    _, _, entries, *_ = _HDR.unpack_from(data, 0)
    assert entries == 1 << 12  # the role knob won, not the 18 fallback
    r.close()


def test_tls_ring_is_per_thread_and_named_role_tid(monkeypatch, tmp_path):
    monkeypatch.setenv("LATREC_DIR", str(tmp_path))
    monkeypatch.setattr(writer, "_DIR", str(tmp_path))
    monkeypatch.setattr(writer, "_tls", threading.local())

    mine = writer.tls_ring("xdevsm")
    assert mine is writer.tls_ring("xdevsm")  # cached per thread

    seen = {}

    def other():
        seen["ring"] = writer.tls_ring("xdevsm")

    t = threading.Thread(target=other)
    t.start()
    t.join()

    assert seen["ring"] is not mine  # a distinct ring per writer thread
    names = sorted(p.name for p in tmp_path.glob("xdevsm.*.latrec"))
    assert len(names) == 2


def test_tls_ring_is_free_when_disabled(monkeypatch):
    """Off must cost nothing beyond a global load: no ring built, no file, and
    the same shared object every time."""
    monkeypatch.setattr(writer, "_DIR", None)
    r = writer.tls_ring("xdevsm")
    assert r is writer._DISABLED
    assert r.enabled is False
    r.stamp(1, 0x5A, aux=99)  # must not raise


def test_flush_rings_publishes_rec_count(monkeypatch, tmp_path):
    """A ring that is never closed still has to carry its write count: without
    it a reader cannot tell a wrapped ring from a partly filled one."""
    monkeypatch.setenv("LATREC_DIR", str(tmp_path))
    name = _unique_name()
    r = writer.ring(name, entries_log2=4)
    r.stamp(1, 0x60)
    r.stamp(2, 0x61)

    path = tmp_path / f"{name}.latrec"
    _, _, _, before, *_ = _HDR.unpack_from(path.read_bytes(), 0)
    assert before == 0  # not published yet

    writer.flush_rings()  # no close(), as on a killed process
    _, _, _, after, *_ = _HDR.unpack_from(path.read_bytes(), 0)
    assert after == 2
    r.close()
