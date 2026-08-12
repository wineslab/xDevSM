"""Pure-Python utilities: constants, latency markers, file/config helpers."""

import json

import pytest

from xdevsm.utils import lat_profile, utility
from xdevsm.utils.constants import Values


def test_values_constants():
    assert Values.RIC_INDICATION == 12050
    assert Values.RIC_CONTROL_REQ == 12040
    assert Values.ACTION_TYPE == "report"
    assert Values.SUBSCRIPTION_PORT == "8088"


def test_read_file(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("hello")
    assert utility.read_file(str(f)) == "hello"
    # empty file -> None
    empty = tmp_path / "e.txt"
    empty.write_text("")
    assert utility.read_file(str(empty)) is None
    # missing file -> None
    assert utility.read_file(str(tmp_path / "nope.txt")) is None


def test_extract_config_fields(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"name": "myxapp", "APP_NAMESPACE": "ricxapp"}))
    assert utility.extract_config_fields(str(cfg)) == ("myxapp", "ricxapp")


def test_extract_config_fields_missing_key(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"name": "only"}))
    with pytest.raises(KeyError):
        utility.extract_config_fields(str(cfg))


def test_extract_config_fields_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        utility.extract_config_fields(str(tmp_path / "absent.json"))


def test_write_routing_table_basic(tmp_path):
    route = tmp_path / "route.rt"
    ok = utility.write_routing_table("myxapp", "ricxapp", 4560, str(route))
    assert ok is True
    content = route.read_text()
    assert content.startswith("newrt|start")
    assert content.strip().endswith("newrt|end")
    for mtype in (12011, 12012, 12021, 12022, 12050):
        assert f"rte|{mtype}|" in content
    # no platform namespace -> no A1 policy route
    assert "20011" not in content


def test_write_routing_table_with_platform_namespace(tmp_path):
    route = tmp_path / "route.rt"
    utility.write_routing_table("myxapp", "ricxapp", 4560, str(route), plt_namespace="ricplt")
    content = route.read_text()
    assert "rte|20011|" in content
    assert "a1mediator" in content


def test_decode_meid_bytes_and_str_and_missing():
    assert utility.decode_meid({"meid": b"gnb_001"}) == "gnb_001"
    assert utility.decode_meid({"meid": "gnb_002"}) == "gnb_002"
    assert utility.decode_meid({}) is None


def test_get_c_byte_array():
    arr = utility.get_c_byte_array_from_py_byte_string(b"abc")
    assert arr is not None
    assert len(arr) == 3


def test_lat_log_noop_when_disabled(monkeypatch):
    monkeypatch.setattr(lat_profile, "_ENABLED", False)
    assert lat_profile.enabled() is False

    class _Rec:
        def __init__(self):
            self.msgs = []

        def info(self, msg):
            self.msgs.append(msg)

    logger = _Rec()
    lat_profile.lat_log(logger, "stage-x")
    assert logger.msgs == []  # disabled -> nothing logged


def test_lat_log_emits_when_enabled(monkeypatch):
    monkeypatch.setattr(lat_profile, "_ENABLED", True)

    class _Rec:
        def __init__(self):
            self.msgs = []

        def info(self, msg):
            self.msgs.append(msg)

    logger = _Rec()
    lat_profile.lat_log(logger, "stage-x", foo=1)
    assert logger.msgs
    assert "[LAT]" in logger.msgs[0]
    assert "stage=stage-x" in logger.msgs[0]
