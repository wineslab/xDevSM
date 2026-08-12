"""Native sm_framework: the bundled encoders load package-relative, and ByteArray works."""

import os

from _env import requires_native


@requires_native
def test_all_encoders_load_package_relative():
    # Importing this module loads all bundled .so via ctypes with RTLD_GLOBAL.
    from xdevsm.sm_framework.lib import library_wrapper as lw

    assert lw.kpm_lib is not None
    assert lw.wrapper is not None
    assert lw.rc_lib is not None
    assert lw.dApp_lib is not None


@requires_native
def test_encoders_load_without_ld_library_path(monkeypatch):
    # Prove the loader resolves the .so from the package dir, not LD_LIBRARY_PATH.
    monkeypatch.delenv("LD_LIBRARY_PATH", raising=False)
    import importlib

    lw = importlib.import_module("xdevsm.sm_framework.lib.library_wrapper")
    importlib.reload(lw)
    assert lw.wrapper is not None
    # The libraries live next to the module.
    lib_dir = os.path.dirname(lw.__file__)
    assert os.path.exists(os.path.join(lib_dir, "libsm_framework.so"))


@requires_native
def test_bytearray_hex_roundtrip():
    from xdevsm.sm_framework.py_oran.ByteArray import ByteArray

    ba = ByteArray()
    ba.from_hex("deadbeef")
    assert ba.len == 4
    assert ba.to_bytes().hex() == "deadbeef"


@requires_native
def test_bytearray_empty_to_bytes():
    from xdevsm.sm_framework.py_oran.ByteArray import ByteArray

    ba = ByteArray()
    assert ba.to_bytes() == b""
