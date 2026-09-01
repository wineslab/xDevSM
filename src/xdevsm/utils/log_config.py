"""Resolve the xApp's logging settings from its descriptor and environment.

Three knobs, read from the descriptor's ``controls`` block and overridable per
deployment by an environment variable, so a Deployment can change them without
rebuilding an image:

==================  =================  ==========================  =========
controls key        env override       values                      default
==================  =================  ==========================  =========
``log_level``       ``LOG_LEVEL``      DEBUG/INFO/WARNING/ERROR    ``INFO``
``log_stdout``      ``LOG_STDOUT``     boolean                     ``True``
``log_file``        ``LOG_FILE``       path ("" = no file)         ``None``
``log_buffering``   ``LOG_BUFFERING``  int, as for ``open()``      ``1``
==================  =================  ==========================  =========

``log_buffering`` is the file's buffer size. The default, 1, is line-buffered:
the file is readable while the xApp runs, at the cost of a write syscall per
entry. An xApp that logs from a hot path should set a block size (65536, say)
and call :func:`flush_log_file` periodically -- the data ingestor logs from the
single RMR dispatch thread, where per-line syscalls are the difference between
keeping up with the indication rate and falling behind it.

ERROR is the quietest level there is: mdclogpy's severity enum stops there, with
no OFF.

This module deliberately imports no ``mdclogpy``. That package binds ``inotify``,
a Linux syscall, so it cannot even be imported on macOS -- keeping the decision
logic here, and the part that touches a real logger in the caller, is what makes
the behaviour unit-testable off a deployment host. It mirrors why
``xdevsm.handlers.config`` stays RMR-free.
"""
import os

LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")
DEFAULT_LEVEL = "INFO"
DEFAULT_BUFFERING = 1  # line-buffered; see the module docstring

_FALSE = ("0", "false", "no", "off", "")


def _as_bool(value, fallback: bool) -> bool:
    if value is None:
        return fallback
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in _FALSE


def resolve_log_settings(controls=None, environ=None):
    """Return ``(level, to_stdout, log_file)``.

    Precedence is environment, then ``controls``, then the default. An
    unrecognised level falls back to the default rather than raising: a typo in
    a descriptor should not stop an xApp from starting.
    """
    controls = controls or {}
    environ = os.environ if environ is None else environ

    level = (environ.get("LOG_LEVEL") or controls.get("log_level") or DEFAULT_LEVEL)
    level = str(level).strip().upper()
    if level not in LEVELS:
        level = DEFAULT_LEVEL

    to_stdout = _as_bool(environ.get("LOG_STDOUT"), _as_bool(controls.get("log_stdout"), True))

    log_file = environ.get("LOG_FILE")
    if log_file is None:
        log_file = controls.get("log_file")
    log_file = str(log_file).strip() if log_file is not None else ""

    return level, to_stdout, (log_file or None)


def resolve_log_buffering(controls=None, environ=None):
    """Return the log file's buffer size, as ``open()``'s ``buffering``.

    Kept out of :func:`resolve_log_settings` on purpose: that function answers
    "where does output go", which every xApp cares about, while this one is a
    performance knob only an xApp logging from a hot path needs to touch. Same
    env-then-controls precedence. A non-integer value falls back to the default
    rather than raising, for the same reason an unknown level does.
    """
    controls = controls or {}
    environ = os.environ if environ is None else environ

    raw = environ.get("LOG_BUFFERING")
    if raw is None:
        raw = controls.get("log_buffering")
    if raw is None:
        return DEFAULT_BUFFERING
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return DEFAULT_BUFFERING


def apply_to_logger(logger, controls=None, environ=None):
    """Point ``logger`` at the configured level and sinks; return the settings.

    ``mdclogpy`` is imported here rather than at module scope so this module
    stays importable where that package cannot load (see the note above).
    """
    level, to_stdout, log_file = resolve_log_settings(controls, environ)

    from mdclogpy import Level

    logger.set_level(getattr(Level, level))
    if log_file or not to_stdout:
        _install_sink(logger, log_file, to_stdout,
                      resolve_log_buffering(controls, environ))
    return level, to_stdout, log_file


class LogSink:
    """The logger's output step: stdout, a file, or both.

    mdclogpy writes every entry with a bare ``print()`` in ``_output_log``, with
    no way to redirect it. An instance of this class is assigned over that one
    method, which keeps stdout optional and adds the file without subclassing --
    the logger object belongs to ricxappframe and is shared with it, so leaving
    its class alone is the least surprising thing to do.

    It is an object rather than a closure because the file has a lifecycle:
    something has to flush it on a schedule and close it at shutdown. Owning the
    handle here means those are methods on the thing that opened it, instead of
    free functions reaching into an attribute parked on the logger.
    """

    def __init__(self, emit, logger, to_stdout=True, log_file=None,
                 buffering=DEFAULT_BUFFERING):
        self._emit = emit
        self._logger = logger
        self._to_stdout = to_stdout
        self._fp = None
        if log_file:
            path = os.path.abspath(log_file)
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            self._fp = open(path, "a", buffering=buffering)

    def __call__(self, entry):
        if self._to_stdout:
            self._emit(self._logger, entry)
        fp = self._fp
        if fp is not None:
            fp.write(entry + "\n")

    def flush(self):
        """Push buffered entries to disk. No-op without a file, or once closed."""
        fp = self._fp
        if fp is not None and not fp.closed:
            fp.flush()

    def close(self):
        """Flush and close the file. Idempotent."""
        fp = self._fp
        if fp is not None:
            if not fp.closed:
                fp.close()
            self._fp = None


def _install_sink(logger, log_file, to_stdout, buffering=DEFAULT_BUFFERING):
    """Build a :class:`LogSink` for ``logger`` and install it; return the sink.

    The sink is also stashed on the logger so :func:`close_log_file` and
    :func:`flush_log_file` can find it from anywhere holding the logger -- which
    is what ricxappframe passes around -- without every caller having to thread
    the handle through.
    """
    sink = LogSink(type(logger)._output_log, logger, to_stdout, log_file, buffering)
    logger._output_log = sink
    logger._xdevsm_log_sink = sink
    return sink


def _sink_of(logger):
    return getattr(logger, "_xdevsm_log_sink", None)


def flush_log_file(logger):
    """Flush the log file if one was opened. Safe on any logger.

    For xApps that set a block ``log_buffering``: call this from whatever
    periodic task they already run, so the file's tail is never more than one
    period stale.
    """
    sink = _sink_of(logger)
    if sink is not None:
        sink.flush()


def close_log_file(logger):
    """Close the log file if one was opened. Idempotent, safe on any logger."""
    sink = _sink_of(logger)
    if sink is not None:
        sink.close()
