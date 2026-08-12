"""Handlers: pure-Python config loading and the abstract xApp interface.

The RMR-backed ``xDevSMRMRXapp`` requires ricxappframe + the RMR C library; it is only
import-checked here (guarded), since constructing it needs a live RMR runtime.
"""

import json

import pytest

from _env import requires_ricxappframe

from xdevsm.handlers import config
from xdevsm.handlers.I_xDevSM_xapp import BasexDevSMXapp


def test_load_descriptor_from_path(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"controls": {"a": 1}, "name": "x"}))
    data = config.load_descriptor(str(cfg))
    assert data["controls"] == {"a": 1}


def test_load_descriptor_missing_returns_empty(tmp_path):
    assert config.load_descriptor(str(tmp_path / "nope.json")) == {}


def test_load_controls(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"controls": {"prb": {"min": 0}}}))
    assert config.load_controls(str(cfg)) == {"prb": {"min": 0}}


def test_load_controls_no_controls_key(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"name": "x"}))
    assert config.load_controls(str(cfg)) == {}


def test_base_xapp_is_abstract():
    with pytest.raises(TypeError):
        BasexDevSMXapp()  # abstract methods not implemented


def test_base_xapp_subclass_must_implement_all():
    class Incomplete(BasexDevSMXapp):
        def send(self, *args, **kwargs):
            pass

    with pytest.raises(TypeError):
        Incomplete()

    class Complete(BasexDevSMXapp):
        def send(self, *args, **kwargs):
            return "sent"

        def handle(self, xapp, summary, sbuf):
            pass

        def terminate(self, signum, frame):
            pass

        def get_ran_function_description(self, json_ran_info):
            return {}

    inst = Complete()
    assert inst.send() == "sent"


@requires_ricxappframe
def test_rmr_xapp_importable():
    from xdevsm.handlers.xDevSM_rmr_xapp import xDevSMRMRXapp

    assert isinstance(xDevSMRMRXapp, type)
