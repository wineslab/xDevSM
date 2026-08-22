"""Reference Python latrec writer -- a per-writer mmap ring recorder.

WIRE-FORMAT CONTRACT. Byte-identical to the C ``latrec_hdr`` / ``latrec_rec``
layout libe3 writes, so the RAN, the dApps, the E2 agent and any xApp
framework produce one comparable capture and the offline converter
(libe3's ``tools/latrec_reader.py`` / ``latrec2csv.py``) reads every ring the
same way. This module has no dependency on libe3's build (no SWIG binding
available here), so the format is mirrored by hand. Two things must not
drift from libe3/include/libe3/latrec.h:
  - the on-disk layout below (magic, version, 4 KiB header, 32-byte records);
  - the stage ids a caller passes to ``stamp()`` -- a cross-repo namespace
    owned by libe3's catalog, not by this module.

This module is intentionally catalog-agnostic: it knows nothing about which
stage ids mean what. Callers own their own mirror of the relevant subset of
libe3's catalog (see e.g. ``xdevsm._latrec.stages``) and pass raw ints.

Env-gated by ``LATREC_DIR``: every ``stamp()`` is a no-op when it is unset.
This mirrors libe3's own directory-selection knob, but -- unlike libe3/
flexric's C build-flag gate -- a pure-Python package has no separate build
for "traced" vs "untraced", so the runtime env var is the only gate
available here.

Record: 32 B = sc(u64: seq:48 | cpu:8 | stage:8), t_ns(u64, written LAST ==
valid), aux(u64), aux2(u64). The cpu byte is left 0: CPython has no
``os.sched_getcpu()`` before 3.13, and reading it per stamp any other way
costs more than the stamp.

This module is meant to be adopted as-is by other pure-Python components in
this stack (e.g. spear-dApp) once they need the same mechanism -- keep it
free of any project-specific imports so reuse is a straight copy, not a
rewrite.
"""
import atexit
import mmap
import os
import struct
import threading
import time

HDR_LEN = 4096
MAGIC = 0x31524C41  # "ALR1"
VERSION = 2
_REC_SIZE = 32
_HDR = struct.Struct("<IIQQQQ64s")      # v1 prefix; offsets frozen
_HDR_V2 = struct.Struct("<IIQQ")        # rec_size, clock_ns_per_call, t1_mono, t1_real
_V2_OFF = 104


def _mono_ns() -> int:
    return time.clock_gettime_ns(time.CLOCK_MONOTONIC)


def _real_ns() -> int:
    return time.clock_gettime_ns(time.CLOCK_REALTIME)


def _measure_clock_ns() -> int:
    """Mean cost of one _mono_ns(), recorded in the header so a reader can
    discount it. The Python call overhead dominates, so this is much larger
    than the C writers report -- which is the point of recording it."""
    iters = 1000
    t0 = _mono_ns()
    for _ in range(iters):
        _mono_ns()
    return max(0, (_mono_ns() - t0) // iters)


def _entries_log2(role: str, fallback: int) -> int:
    """LATREC_ENTRIES_LOG2_<ROLE> (role uppercased, non-alphanumerics as '_'),
    else LATREC_ENTRIES_LOG2, else the caller's fallback -- the same knobs the
    C writers honour, so one environment sizes every ring in a capture."""
    key = "".join(c.upper() if c.isalnum() else "_" for c in role)
    for var in (f"LATREC_ENTRIES_LOG2_{key}", "LATREC_ENTRIES_LOG2"):
        v = os.environ.get(var)
        if v:
            try:
                n = int(v)
            except ValueError:
                continue
            if 12 <= n <= 28:
                return n
    return fallback


_counter = 0
_counter_lock = threading.Lock()


def seq_next() -> int:
    """Next value of the process-wide sequence counter (starts at 1)."""
    global _counter
    with _counter_lock:
        _counter += 1
        return _counter


_ctx = threading.local()


def ctx_set(seq: int) -> None:
    """Bind ``seq`` to the current thread, so a later stage on the same
    synchronous call chain can pick it up without an explicit parameter --
    the same role libe3's ``latrec_ctx_set()`` / flexric's
    ``fx_latrec_ctx_set()`` play in C."""
    _ctx.seq = seq


def ctx_get() -> int:
    """The seq last bound on this thread via ``ctx_set()``, or 0 if none."""
    return getattr(_ctx, "seq", 0)


class LatRec:
    """One ring per instance. A writer may stamp from a couple of threads, so
    a lock guards the index bump; each record still has exactly one writer,
    and t_ns is stored last so a reader never sees a half-written record."""

    def __init__(self, name: str, entries_log2: int = 18):
        self.enabled = False
        self._mm = None
        d = os.environ.get("LATREC_DIR")
        if not d:
            return
        os.makedirs(d, exist_ok=True)
        entries = 1 << _entries_log2(name, entries_log2)
        length = HDR_LEN + entries * _REC_SIZE
        path = os.path.join(d, f"{name}.latrec")
        # Built under a temporary name and renamed once the header is written:
        # rename() is atomic, so a <name>.latrec always carries a valid header.
        tmp = path + ".part"
        fd = os.open(tmp, os.O_CREAT | os.O_RDWR | os.O_TRUNC, 0o644)
        try:
            os.ftruncate(fd, length)
            self._mm = mmap.mmap(fd, length)
        finally:
            os.close(fd)
        self._mm[:HDR_LEN] = b"\x00" * HDR_LEN
        now_m, now_r = _mono_ns(), _real_ns()
        _HDR.pack_into(self._mm, 0, MAGIC, VERSION, entries, 0,
                       now_m, now_r, name.encode()[:63])
        _HDR_V2.pack_into(self._mm, _V2_OFF, _REC_SIZE, _measure_clock_ns(),
                          now_m, now_r)
        os.rename(tmp, path)
        self._mask = entries - 1
        self._idx = 0
        self._lock = threading.Lock()
        self.enabled = True

    def stamp(self, seq: int, stage: int, aux: int = 0, aux2: int = 0) -> None:
        if not self.enabled:
            return
        sc = (seq & 0x0000FFFFFFFFFFFF) | ((stage & 0xFF) << 56)
        with self._lock:
            off = HDR_LEN + (self._idx & self._mask) * _REC_SIZE
            self._idx += 1
        mm = self._mm
        struct.pack_into("<Q", mm, off + 0, sc)
        struct.pack_into("<Q", mm, off + 16, aux & 0xFFFFFFFFFFFFFFFF)
        struct.pack_into("<Q", mm, off + 24, aux2 & 0xFFFFFFFFFFFFFFFF)
        struct.pack_into("<Q", mm, off + 8, _mono_ns())  # last -> marks valid

    def heartbeat(self) -> None:
        """Publish the write count and a fresh clock pair. Records are valid
        without this (t_ns != 0); it fills in what a reader needs to tell a
        wrapped ring from a partly filled one."""
        if not self.enabled or self._mm is None:
            return
        struct.pack_into("<Q", self._mm, 16, self._idx)      # rec_count
        struct.pack_into("<QQ", self._mm, _V2_OFF + 8, _mono_ns(), _real_ns())

    def close(self) -> None:
        if not self.enabled or self._mm is None:
            return
        self.heartbeat()
        try:
            self._mm.flush()
        finally:
            self._mm.close()
            self._mm = None
            self.enabled = False


_rings = {}
_rings_lock = threading.Lock()


def ring(name: str, entries_log2: int = 18) -> "LatRec":
    """Get-or-create a process-wide named ring (e.g. ``xdevsm.12345``)."""
    with _rings_lock:
        r = _rings.get(name)
        if r is None:
            r = LatRec(name, entries_log2)
            _rings[name] = r
        return r


@atexit.register
def _flush_rings() -> None:
    """Rings are not closed by their users, so refresh rec_count and the
    closing clock pair at exit."""
    with _rings_lock:
        for r in _rings.values():
            r.heartbeat()
