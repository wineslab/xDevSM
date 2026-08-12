"""RMR-free access to the xApp descriptor.

ricxappframe loads the descriptor into ``_config_data`` when the RMR frame is
built, but building that frame pulls in the native RMR/E2SM libs. This module
reads the *same* descriptor (the JSON at ``CONFIG_FILE``) using only ``os`` and
``json`` -- so an xApp can read its ``controls`` for configuration *before* (or
without) building the RMR frame, e.g. on an offline/test import path where the
native libs are absent. ``xDevSMRMRXapp.get_controls`` returns the same data at
runtime.
"""

import json
import os


def load_descriptor(config_file=None):
    """Return the parsed xApp descriptor (dict).

    Reads the JSON at ``config_file`` or, when not given, the path in the
    ``CONFIG_FILE`` environment variable. Returns ``{}`` when the path is unset,
    missing, or unparseable -- e.g. a local run with no mounted descriptor, where
    callers fall back to their own defaults.
    """
    path = config_file or os.environ.get("CONFIG_FILE")
    if not path:
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def load_controls(config_file=None):
    """Return the descriptor's ``controls`` block ({} if absent)."""
    return (load_descriptor(config_file) or {}).get("controls") or {}
