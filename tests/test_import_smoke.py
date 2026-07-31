"""Smoke tests: the package imports, exposes a version, and its lazy re-exports resolve."""

import importlib

import pytest

import xdevsm

EXPECTED_EXPORTS = {
    "xDevSMRMRXapp",
    "BasexDevSMXapp",
    "BaseXDevSMWrapper",
    "XappKpmFrame",
    "XappCccFrame",
    "RadioBearerControl",
    "RadioResourceAllocationControl",
    "ConnectedModeMobilityControl",
    "DAppReport",
    "DAppPrbMaskControl",
}


def test_version_is_a_nonempty_string():
    assert isinstance(xdevsm.__version__, str)
    assert xdevsm.__version__  # not empty


def test_all_public_names_advertised():
    assert EXPECTED_EXPORTS <= set(dir(xdevsm))
    assert EXPECTED_EXPORTS <= set(xdevsm.__all__)


def test_unknown_attribute_raises():
    with pytest.raises(AttributeError):
        _ = xdevsm.NoSuchThing


@pytest.mark.parametrize("name", sorted(EXPECTED_EXPORTS))
def test_lazy_export_resolves(name):
    """Each advertised class resolves to a class.

    Some pull in ricxappframe/RMR or the native encoders; if those are unavailable in
    this environment the import is skipped rather than failed.
    """
    try:
        obj = getattr(xdevsm, name)
    except (ImportError, OSError) as exc:  # missing ricxappframe/RMR or native .so
        pytest.skip(f"{name} unavailable in this environment: {exc}")
    assert isinstance(obj, type)


def test_subpackages_are_real_packages():
    # The dApp subtrees were implicit namespace packages before packaging; they must
    # now import as regular packages (they ship __init__.py).
    for mod in (
        "xdevsm.decorators",
        "xdevsm.handlers",
        "xdevsm.utils",
        "xdevsm.sm_framework",
        "xdevsm.decorators.dApp",
        "xdevsm.decorators.dApp.control",
        "xdevsm.decorators.dApp.report",
        "xdevsm.sm_framework.py_oran.dapp",
        "xdevsm.sm_framework.py_oran.dapp.control",
        "xdevsm.sm_framework.py_oran.dapp.e3",
        "xdevsm.sm_framework.py_oran.dapp.report",
    ):
        assert importlib.import_module(mod) is not None
