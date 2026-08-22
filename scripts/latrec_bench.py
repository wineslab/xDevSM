#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Measure the per-stamp cost of the reference Python latrec writer
(xdevsm._latrec.writer), at whatever rate the caller chooses.

Run this on the actual deployment host/pod, not just a dev machine -- the
issue-#6 data-taking checklist calls for the cost "at the deployed message
rate", and container CPU limits/noisy-neighbour scheduling can move these
numbers well past what a bare dev laptop reports.

Usage:
    LATREC_DIR=$(mktemp -d) python3 scripts/latrec_bench.py [N]
"""
import os
import statistics
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200_000

    own_tmp = None
    if not os.environ.get("LATREC_DIR"):
        own_tmp = tempfile.TemporaryDirectory()
        os.environ["LATREC_DIR"] = own_tmp.name

    from xdevsm._latrec import writer

    r = writer.ring("bench.0")
    samples = []
    for _ in range(n):
        t0 = time.perf_counter_ns()
        seq = writer.seq_next()
        writer.ctx_set(seq)
        r.stamp(seq, 0x60, aux=128)
        samples.append(time.perf_counter_ns() - t0)
    r.close()

    samples.sort()
    mean = statistics.mean(samples)
    p50 = samples[len(samples) // 2]
    p99 = samples[int(len(samples) * 0.99)]
    p999 = samples[int(len(samples) * 0.999)]
    print(f"N={n}")
    print(f"full stamp (seq_next + ctx_set + stamp): "
          f"mean={mean:.0f}ns p50={p50}ns p99={p99}ns p99.9={p999}ns")
    print(f"raw clock_gettime cost (from ring header): "
          f"{writer._measure_clock_ns()}ns")

    if own_tmp is not None:
        own_tmp.cleanup()


if __name__ == "__main__":
    main()
