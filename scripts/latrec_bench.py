#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Measure the per-stamp cost of the reference Python latrec writer
(xdevsm._latrec.writer), both enabled and disabled, at whatever rate the
caller chooses.

Both paths matter: enabled tells you what a capture costs, disabled tells you
what every xApp pays for carrying the instrumentation with tracing off, which
is how they run in production.

Run this on the actual deployment host/pod, not just a dev machine -- the
issue-#6 data-taking checklist calls for the cost "at the deployed message
rate", and container CPU limits/noisy-neighbour scheduling can move these
numbers well past what a bare dev laptop reports.

Usage:
    python3 scripts/latrec_bench.py [N]          # times both paths
    LATREC_DIR=/some/dir python3 scripts/latrec_bench.py [N]
"""
import os
import statistics
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def _percentiles(samples, label):
    samples.sort()
    return (f"{label}: mean={statistics.mean(samples):.0f}ns "
            f"p50={samples[len(samples) // 2]}ns "
            f"p99={samples[int(len(samples) * 0.99)]}ns "
            f"p99.9={samples[int(len(samples) * 0.999)]}ns")


def _time_stamps(n, role="bench"):
    """One full stamp site, as the decorators call it."""
    from xdevsm._latrec import writer

    r = writer.tls_ring(role)
    samples = []
    for _ in range(n):
        t0 = time.perf_counter_ns()
        seq = writer.seq_next()
        writer.ctx_set(seq)
        r.stamp(seq, 0x60, aux=128)
        samples.append(time.perf_counter_ns() - t0)
    writer.flush_rings()
    return samples


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200_000

    if os.environ.get("_LATREC_BENCH_CHILD"):
        # Re-exec'd with LATREC_DIR unset: the writer samples it at import,
        # so the disabled path can only be timed in a fresh interpreter.
        print(_percentiles(_time_stamps(n), "disabled (LATREC_DIR unset)  "), flush=True)
        return

    own_tmp = None
    if not os.environ.get("LATREC_DIR"):
        own_tmp = tempfile.TemporaryDirectory()
        os.environ["LATREC_DIR"] = own_tmp.name

    from xdevsm._latrec import writer

    print(f"N={n}", flush=True)
    print(_percentiles(_time_stamps(n), "enabled  (seq+ctx+stamp)     "), flush=True)
    print(f"raw clock_gettime cost (from ring header): "
          f"{writer.measure_clock_ns()}ns", flush=True)

    env = {k: v for k, v in os.environ.items() if k != "LATREC_DIR"}
    env["_LATREC_BENCH_CHILD"] = "1"
    subprocess.run([sys.executable, os.path.abspath(__file__), str(n)],
                   env=env, check=True)

    if own_tmp is not None:
        own_tmp.cleanup()


if __name__ == "__main__":
    main()
