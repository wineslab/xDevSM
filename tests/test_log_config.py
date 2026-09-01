"""Settings resolution for the descriptor-driven logging knobs.

These exercise xdevsm.utils.log_config, which is deliberately free of mdclogpy
so it can be tested anywhere -- mdclogpy binds inotify and will not import off
Linux, which is exactly why the resolution logic lives apart from the code that
applies it to a real logger.
"""

import os

import pytest

from xdevsm.utils import log_config


def _resolve(controls=None, **env):
    return log_config.resolve_log_settings(controls or {}, environ=env)


def test_defaults_when_nothing_is_configured():
    assert _resolve() == ("INFO", True, None)


def test_controls_supply_all_three():
    level, stdout, path = _resolve(
        {"log_level": "ERROR", "log_stdout": False, "log_file": "/tmp/xapp.log"})
    assert (level, stdout, path) == ("ERROR", False, "/tmp/xapp.log")


def test_env_overrides_controls():
    """A Deployment can change these without rebuilding the image, so the env
    has to win over the descriptor baked into the container."""
    level, stdout, path = _resolve(
        {"log_level": "DEBUG", "log_stdout": True, "log_file": "/tmp/a.log"},
        LOG_LEVEL="WARNING", LOG_STDOUT="false", LOG_FILE="/var/log/b.log")
    assert (level, stdout, path) == ("WARNING", False, "/var/log/b.log")


@pytest.mark.parametrize("level", ["DEBUG", "INFO", "WARNING", "ERROR"])
def test_every_mdclogpy_level_is_accepted(level):
    assert _resolve({"log_level": level})[0] == level


@pytest.mark.parametrize("given,expected", [
    ("error", "ERROR"), ("  Info  ", "INFO"),      # case and whitespace tolerated
    ("TRACE", "INFO"), ("", "INFO"), ("42", "INFO"),  # nonsense -> default
])
def test_unknown_level_falls_back_rather_than_raising(given, expected):
    """A typo in a descriptor must not stop an xApp from starting."""
    assert _resolve({"log_level": given})[0] == expected


@pytest.mark.parametrize("given", [False, "false", "False", "0", "no", "off", ""])
def test_falsey_stdout_spellings(given):
    assert _resolve({"log_stdout": given})[1] is False


@pytest.mark.parametrize("given", [True, "true", "yes", "1", "on"])
def test_truthy_stdout_spellings(given):
    assert _resolve({"log_stdout": given})[1] is True


def test_empty_log_file_means_no_file():
    """Distinguishes "unset" from "set to nothing" -- an env var exported as an
    empty string must disable the file, not create one named ''."""
    assert _resolve({"log_file": ""})[2] is None
    assert _resolve({"log_file": "/tmp/x.log"}, LOG_FILE="")[2] is None


def test_stdout_stays_on_by_default_so_behaviour_is_unchanged():
    """A descriptor that configures nothing must keep logging to stdout."""
    assert _resolve({"log_level": "ERROR"})[1] is True


class _FakeLogger:
    """Stands in for mdclogpy.Logger: same _output_log contract, no inotify."""

    def __init__(self):
        self.level = None
        self.written = []

    def set_level(self, level):
        self.level = level

    def _output_log(self, entry):
        self.written.append(entry)


def test_install_sink_writes_file_and_can_mute_stdout(tmp_path):
    path = tmp_path / "xapp.log"
    logger = _FakeLogger()
    log_config._install_sink(logger, str(path), to_stdout=False)

    logger._output_log('{"msg": "hello"}')

    assert path.read_text() == '{"msg": "hello"}\n'
    assert logger.written == []  # stdout suppressed
    log_config.close_log_file(logger)


def test_install_sink_can_do_both(tmp_path):
    path = tmp_path / "xapp.log"
    logger = _FakeLogger()
    log_config._install_sink(logger, str(path), to_stdout=True)

    logger._output_log('{"msg": "hi"}')

    assert path.read_text() == '{"msg": "hi"}\n'
    assert logger.written == ['{"msg": "hi"}']
    log_config.close_log_file(logger)


def test_sink_creates_missing_parent_directories(tmp_path):
    path = tmp_path / "nested" / "dir" / "xapp.log"
    logger = _FakeLogger()
    log_config._install_sink(logger, str(path), to_stdout=False)
    logger._output_log("x")
    assert path.exists()
    log_config.close_log_file(logger)


def test_close_log_file_is_idempotent_and_safe_on_any_logger():
    logger = _FakeLogger()
    log_config.close_log_file(logger)  # never had a file; must not raise
    log_config.close_log_file(logger)


def test_resolve_reads_real_environ_when_none_passed(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    monkeypatch.delenv("LOG_STDOUT", raising=False)
    monkeypatch.delenv("LOG_FILE", raising=False)
    assert log_config.resolve_log_settings({})[0] == "WARNING"
    assert os.environ["LOG_LEVEL"] == "WARNING"


# --- buffering knob + LogSink lifecycle -------------------------------------


def _buffering(controls=None, **env):
    return log_config.resolve_log_buffering(controls or {}, environ=env)


def test_buffering_defaults_to_line_buffered():
    assert _buffering() == 1


def test_buffering_from_controls_and_env_override():
    assert _buffering({"log_buffering": 65536}) == 65536
    assert _buffering({"log_buffering": 65536}, LOG_BUFFERING="4096") == 4096


@pytest.mark.parametrize("given", ["", "banana", None, [1]])
def test_bad_buffering_falls_back_rather_than_raising(given):
    """A typo in a descriptor must not stop an xApp from starting, same as an
    unknown level."""
    assert _buffering({"log_buffering": given}) == log_config.DEFAULT_BUFFERING


def test_block_buffered_sink_holds_entries_until_flushed(tmp_path):
    """The whole point of the knob: no write syscall per entry on a hot path."""
    path = tmp_path / "xapp.log"
    logger = _FakeLogger()
    sink = log_config._install_sink(logger, str(path), to_stdout=False,
                                    buffering=1 << 16)

    logger._output_log('{"msg": "buffered"}')
    assert path.read_text() == ""          # still in the buffer

    sink.flush()
    assert path.read_text() == '{"msg": "buffered"}\n'
    sink.close()


def test_flush_log_file_finds_the_sink_from_the_logger(tmp_path):
    path = tmp_path / "xapp.log"
    logger = _FakeLogger()
    log_config._install_sink(logger, str(path), to_stdout=False, buffering=1 << 16)

    logger._output_log('{"msg": "via helper"}')
    log_config.flush_log_file(logger)

    assert path.read_text() == '{"msg": "via helper"}\n'
    log_config.close_log_file(logger)


def test_flush_and_close_are_idempotent_and_safe_after_close(tmp_path):
    path = tmp_path / "xapp.log"
    logger = _FakeLogger()
    sink = log_config._install_sink(logger, str(path), to_stdout=False)

    sink.close()
    sink.close()          # second close must not raise
    sink.flush()          # flushing a closed sink must not raise
    log_config.flush_log_file(logger)
    log_config.close_log_file(logger)


def test_flush_log_file_is_safe_on_a_logger_that_never_had_one():
    log_config.flush_log_file(_FakeLogger())


def test_install_sink_returns_the_sink(tmp_path):
    logger = _FakeLogger()
    sink = log_config._install_sink(logger, str(tmp_path / "x.log"), to_stdout=True)
    assert isinstance(sink, log_config.LogSink)
    assert logger._output_log is sink
    sink.close()
