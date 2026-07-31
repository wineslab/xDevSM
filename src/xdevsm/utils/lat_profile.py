"""Optional [LAT] latency-profiling markers for the E2/E2SM-DAPP xApp path.

Runtime-gated by the E3_LATENCY environment variable (unset / "0" = off), read
once at import. When enabled, each site emits ONE line through the existing
mdclogpy logger at INFO in the shared machine-parseable format so an offline
collector can grep and correlate interleaved gNB / RIC / xApp logs:

    [LAT] stage=<name> t_ns=<monotonic ns> anchor_ns=<producer_ts|0> [k=v ...]

t_ns is time.monotonic_ns(). The xApp typically runs on a different node than
the gNB, so its monotonic clock is not directly comparable; the per-process
clock_offset line (CLOCK_MONOTONIC <-> CLOCK_REALTIME) lets the offline tool
bridge nodes via wall-clock. anchor_ns is 0 unless a producer timestamp is
available (the E2 envelope carries none), so the collector pairs by consecutive
line.
"""
import os
import time

_ENABLED = os.environ.get("E3_LATENCY", "").strip() not in ("", "0")


def enabled() -> bool:
    return _ENABLED


def _mono_ns() -> int:
    return time.monotonic_ns()


def _real_ns() -> int:
    return time.clock_gettime_ns(time.CLOCK_REALTIME)


def lat_log(logger, stage: str, anchor_ns: int = 0, **kv) -> None:
    """Emit one [LAT] line via the given mdclogpy logger (no-op when disabled)."""
    if not _ENABLED:
        return
    extra = "".join(f" {k}={v}" for k, v in kv.items())
    logger.info(f"[LAT] stage={stage} t_ns={_mono_ns()} anchor_ns={anchor_ns}{extra}")


def lat_clock_offset(logger) -> None:
    """Per-process run-start line mapping CLOCK_MONOTONIC <-> CLOCK_REALTIME."""
    if not _ENABLED:
        return
    logger.info(f"[LAT] clock_offset mono_ns={_mono_ns()} real_ns={_real_ns()}")
