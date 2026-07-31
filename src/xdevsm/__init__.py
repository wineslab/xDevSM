"""xDevSM — an SDK framework for building O-RAN xApps over E2 Service Models (KPM, RC, CCC).

The public developer-facing classes are re-exported here for convenience, e.g.::

    from xdevsm import xDevSMRMRXapp, XappKpmFrame

Re-exports are resolved lazily (PEP 562): importing ``xdevsm`` does not eagerly pull in
``ricxappframe``/RMR or the native ``sm_framework`` encoders — those load only when the
corresponding class is first accessed.
"""

from importlib.metadata import PackageNotFoundError, version as _version

try:
    __version__ = _version("xdevsm")
except PackageNotFoundError:  # running from a source tree that is not installed
    __version__ = "0.0.0"

# name -> "submodule:attribute" for lazy resolution
_LAZY = {
    "xDevSMRMRXapp": "xdevsm.handlers.xDevSM_rmr_xapp:xDevSMRMRXapp",
    "BasexDevSMXapp": "xdevsm.handlers.I_xDevSM_xapp:BasexDevSMXapp",
    "BaseXDevSMWrapper": "xdevsm.decorators.base:BaseXDevSMWrapper",
    "XappKpmFrame": "xdevsm.decorators.kpm.kpm_frame:XappKpmFrame",
    "XappCccFrame": "xdevsm.decorators.ccc.ccc_frame:XappCccFrame",
    "RadioBearerControl": "xdevsm.decorators.rc.rc_radio_bearer_control:RadioBearerControl",
    "RadioResourceAllocationControl": "xdevsm.decorators.rc.rc_radio_resource_alloc_control:RadioResourceAllocationControl",
    "ConnectedModeMobilityControl": "xdevsm.decorators.rc.rc_connected_mode_mobility:ConnectedModeMobilityControl",
    "DAppReport": "xdevsm.decorators.dApp.report.dapp_report:DAppReport",
    "DAppPrbMaskControl": "xdevsm.decorators.dApp.control.dapp_prb_mask_control:DAppPrbMaskControl",
}

__all__ = ["__version__", *_LAZY.keys()]


def __getattr__(name):
    target = _LAZY.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib

    module_name, _, attr = target.partition(":")
    module = importlib.import_module(module_name)
    value = getattr(module, attr)
    globals()[name] = value  # cache for subsequent lookups
    return value


def __dir__():
    return sorted(__all__)
