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

One caveat against libe3's C writer: it publishes t_ns with an explicit
release store (``LATREC_STORE_RELEASE``), and Python has no equivalent --
``struct.pack_into`` is a plain memcpy. Writing t_ns last is therefore
ordered by the hardware alone: guaranteed on x86-64 (TSO), not on aarch64.
That only matters to a *live* reader racing the writer; the offline
capture-then-convert workflow these rings are built for reads a quiescent
file, where the ordering is moot.

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

# Sampled once, at import, for tls_ring()'s fast path only -- the stamp sites
# are on the message hot path, and re-deriving "is tracing on" per stamp is
# what made the disabled path cost anything at all. LatRec() and ring() still
# read os.environ per call, so they stay configurable at runtime (the tests
# rely on that); tls_ring() is the one that must be free when off, and
# LATREC_DIR is a process-level knob set before start, never mid-run.
_DIR = os.environ.get("LATREC_DIR") or None


def _mono_ns() -> int:
    return time.clock_gettime_ns(time.CLOCK_MONOTONIC)


def _real_ns() -> int:
    return time.clock_gettime_ns(time.CLOCK_REALTIME)


def measure_clock_ns() -> int:
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

    def __init__(self, name: str, entries_log2: int = 18, role: str = None):
        self.enabled = False
        self._mm = None
        d = os.environ.get("LATREC_DIR")
        if not d:
            return
        os.makedirs(d, exist_ok=True)
        # Sized by role, named <role>.<tid>: a key derived from the full name
        # would carry a thread id no one can predict, so it could never be set.
        entries = 1 << _entries_log2(role or name, entries_log2)
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
        _HDR_V2.pack_into(self._mm, _V2_OFF, _REC_SIZE, measure_clock_ns(),
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


def ring(name: str, entries_log2: int = 18, role: str = None) -> "LatRec":
    """Get-or-create a process-wide named ring (e.g. ``xdevsm.12345``)."""
    with _rings_lock:
        r = _rings.get(name)
        if r is None:
            r = LatRec(name, entries_log2, role)
            _rings[name] = r
        return r


_DISABLED = LatRec.__new__(LatRec)
_DISABLED.enabled = False
_DISABLED._mm = None

_tls = threading.local()


def tls_ring(role: str, entries_log2: int = 18) -> "LatRec":
    """This thread's ring for ``role``, named ``<role>.<tid>`` as libe3 does.

    The per-thread cache keeps a stamp site off the process-wide ring lock,
    and the LATREC_DIR check keeps it off everything else when tracing is off.
    """
    if _DIR is None:
        return _DISABLED
    r = getattr(_tls, "ring", None)
    if r is None:
        r = ring(f"{role}.{threading.get_ident()}", entries_log2, role)
        _tls.ring = r
    return r


def flush_rings() -> None:
    """Refresh rec_count and the closing clock pair on every open ring.

    Without this a reader sees rec_count == 0 and cannot tell a wrapped ring
    from a partly filled one, nor fit mono->real across the run. Idempotent,
    so a shutdown path and the atexit hook can both call it.
    """
    with _rings_lock:
        for r in _rings.values():
            r.heartbeat()


atexit.register(flush_rings)


def _heartbeat_loop(interval: float) -> None:
    while True:
        time.sleep(interval)
        flush_rings()


def start_heartbeat(interval: float = 1.0) -> None:
    """Publish rec_count periodically, so a ring survives a SIGKILL with its
    write count intact. No-op when tracing is off; safe to call more than once.
    """
    if _DIR is None or getattr(start_heartbeat, "_started", False):
        return
    start_heartbeat._started = True
    threading.Thread(target=_heartbeat_loop, args=(interval,),
                     name="latrec-heartbeat", daemon=True).start()
