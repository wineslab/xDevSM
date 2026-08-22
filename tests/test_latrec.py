"""Round-trip tests for the reference Python latrec writer
(xdevsm._latrec.writer), byte-compatible with libe3's C latrec_hdr/latrec_rec
layout (include/libe3/latrec.h)."""

import struct
import threading
import uuid

import pytest

from xdevsm._latrec import writer

_HDR = struct.Struct("<IIQQQQ64s")
_HDR_V2 = struct.Struct("<IIQQ")
_V2_OFF = 104
_REC = struct.Struct("<QQQQ")


def _unique_name() -> str:
    return f"test.{uuid.uuid4().hex}"


def test_stamp_is_noop_without_latrec_dir(monkeypatch, tmp_path):
    monkeypatch.delenv("LATREC_DIR", raising=False)
    r = writer.LatRec(_unique_name())
    assert r.enabled is False
    r.stamp(1, 0x60)  # must not raise, must not create anything
    assert list(tmp_path.iterdir()) == []


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
