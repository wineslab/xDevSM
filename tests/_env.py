"""Capability probes shared by the test suite.

xDevSM's ``sm_framework`` loads prebuilt linux-x86_64 ``.so`` encoders at import time,
and several handler/decorator modules import ``ricxappframe`` (which needs the RMR C
library). Tests guard on these so the suite degrades gracefully on platforms/CI where a
capability is missing instead of erroring at collection time.
"""

import importlib

import pytest


def _importable(module: str) -> bool:
    try:
        importlib.import_module(module)
        return True
    except Exception:
        return False


NATIVE_AVAILABLE = _importable("xdevsm.sm_framework.lib.library_wrapper")
# Probe the submodule the handlers/decorators actually import, not the bare package: the
# `ricxappframe` __init__ imports cleanly everywhere, while `xapp_frame` is what pulls in
# mdclogpy -> inotify (Linux-only) and the RMR C library.
RICXAPP_AVAILABLE = _importable("ricxappframe.xapp_frame")

requires_native = pytest.mark.skipif(
    not NATIVE_AVAILABLE,
    reason="native sm_framework .so encoders not loadable on this platform",
)
requires_ricxappframe = pytest.mark.skipif(
    not RICXAPP_AVAILABLE,
    reason="ricxappframe/RMR not available in this environment",
)
