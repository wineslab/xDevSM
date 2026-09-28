"""Ownership of the inbound RMR message buffer.

ricxappframe's receive loop allocates a fresh 4 KiB C buffer per message
(``rmr.helpers.rmr_rcvall_msgs_raw``) and transfers ownership to the caller;
neither ``RmrLoop`` nor ``RMRXapp.run`` frees it. ``_dispatch_event`` takes that
ownership and releases it in a ``finally`` -- so the buffer survives a handler
that raises, and a chain that terminates somewhere other than
``xDevSMRMRXapp.handle``.

The release has to be idempotent: freeing there used to be ``handle``'s job, and
out-of-tree xApps copied that pattern, so a second free must be a no-op rather
than a double free of a C allocation (which aborts the process).

Unlike the other ricxappframe-touching tests, this module does **not** guard on
``requires_ricxappframe``. Importing ``ricxappframe.xapp_frame`` dlopens
``librmr_si.so``, which neither CI nor a plain ``pip install`` provides, so a
guarded module never runs anywhere -- and a skipped double-free test proves
nothing. Nothing here calls into RMR (``rmr_free_msg`` is spied on either way),
so when the real package is unavailable the three imported ricxappframe modules
are stubbed for the duration of the test. The stubs go in through ``monkeypatch``
and are torn down with it, so no other module sees them.

``xDevSMRMRXapp.__init__`` needs a live RMR runtime regardless, so these build
bare instances the way ``test_report_decode_once.py`` builds its frames.

The last groups cover the other direction: ``send_control_request_rmr``
allocates a send buffer and RMR does not take ownership on send, so it has to
free it itself; and the ricInstanceID it puts in the request, which E2Term
routes the acknowledge by.
"""

import ctypes
import importlib
import sys
import threading
import types

import pytest

MODULE = "xdevsm.handlers.xDevSM_rmr_xapp"
CONTROL_MODULE = "xdevsm.decorators.control"


def _ricxappframe_importable():
    try:
        importlib.import_module("ricxappframe.xapp_frame")
        return True
    except Exception:
        return False


def _install_ricxappframe_stubs(monkeypatch):
    """Minimal stand-ins for the three ricxappframe modules MODULE imports.

    Constant values are the real ones (ricxappframe/rmr/rmr.py) so the stub
    cannot drift into testing a different dict key than production uses.
    """
    rmr = types.SimpleNamespace(
        RMR_MS_PAYLOAD_LEN="payload length",
        RMR_MS_MSG_TYPE="message type",
        rmr_free_msg=lambda sbuf: None,
    )

    xapp_frame = types.ModuleType("ricxappframe.xapp_frame")
    xapp_frame.rmr = rmr

    class RMRXapp:                      # never constructed by these tests
        pass

    xapp_frame.RMRXapp = RMRXapp

    util = types.ModuleType("ricxappframe.util")
    util_constants = types.ModuleType("ricxappframe.util.constants")

    class Constants:
        DEFAULT_PLT_NS = "ricplt"
        DEFAULT_XAPP_NS = "ricxapp"

    util_constants.Constants = Constants
    util.constants = util_constants

    xapp_rest = types.ModuleType("ricxappframe.xapp_rest")
    xapp_rest.ThreadedHTTPServer = object
    xapp_rest.initResponse = lambda *a, **kw: {}

    e2ap = types.ModuleType("ricxappframe.e2ap")
    asn1 = types.ModuleType("ricxappframe.e2ap.asn1")

    class ControlRequestMsg:            # replaced per-test where it is exercised
        pass

    asn1.ControlRequestMsg = ControlRequestMsg
    e2ap.asn1 = asn1

    pkg = types.ModuleType("ricxappframe")
    pkg.__path__ = []
    pkg.xapp_frame = xapp_frame
    pkg.util = util
    pkg.xapp_rest = xapp_rest
    pkg.e2ap = e2ap

    for name, module in (
        ("ricxappframe", pkg),
        ("ricxappframe.xapp_frame", xapp_frame),
        ("ricxappframe.util", util),
        ("ricxappframe.util.constants", util_constants),
        ("ricxappframe.xapp_rest", xapp_rest),
        ("ricxappframe.e2ap", e2ap),
        ("ricxappframe.e2ap.asn1", asn1),
    ):
        monkeypatch.setitem(sys.modules, name, module)


@pytest.fixture
def mod(monkeypatch):
    """MODULE, imported fresh so its module-global in-flight token starts clean."""
    if not _ricxappframe_importable():
        _install_ricxappframe_stubs(monkeypatch)
    # Import under the stubs and drop the entry again on teardown, so a real
    # import elsewhere in the session is never served a stub-built module.
    monkeypatch.delitem(sys.modules, MODULE, raising=False)
    m = importlib.import_module(MODULE)
    monkeypatch.setitem(sys.modules, MODULE, m)
    return m


class _Logger:
    """Minimal stand-in for mdclogpy.Logger."""

    def __init__(self):
        self.lines = []

    def _record(self, msg):
        self.lines.append(msg)

    debug = info = warning = error = _record


@pytest.fixture
def freed(mod, monkeypatch):
    """Record every address handed to rmr_free_msg.

    Patches the attribute on whatever rmr object MODULE bound, so with the real
    package the genuine RMR_MS_* constants are still in play.
    """
    calls = []
    monkeypatch.setattr(mod.rmr, "rmr_free_msg", lambda p: calls.append(mod._addr(p)))
    return calls


@pytest.fixture
def xapp(mod):
    class _Bare(mod.xDevSMRMRXapp):
        def __init__(self):
            self._handler = None
            self.logger = _Logger()

    return _Bare()


def _sbuf(addr):
    """A fake mbuf pointer. Never dereferenced: rmr_free_msg is spied on."""
    return ctypes.c_void_p(addr)


def _summary(mod):
    from xdevsm.utils.constants import Values
    return {
        mod.rmr.RMR_MS_PAYLOAD_LEN: 3,
        mod.rmr.RMR_MS_MSG_TYPE: Values.RIC_INDICATION,
    }


IN = 0x7F0000001000
OTHER = 0x7F0000002000


# --- the inbound buffer is released, exactly once ------------------------------

def test_dispatch_frees_the_inbound_buffer(mod, xapp, freed):
    """No registered handler: the handle() fallback no longer frees, so the
    finally must."""
    sbuf = _sbuf(IN)
    xapp._dispatch_event(xapp, _summary(mod), sbuf)
    assert freed == [IN]


def test_dispatch_frees_after_a_registered_handler(mod, xapp, freed):
    """The path every real xApp takes: a chain registered via register_handler."""
    seen = []
    xapp.register_handler(lambda x, s, b: seen.append(b))
    sbuf = _sbuf(IN)
    xapp._dispatch_event(xapp, _summary(mod), sbuf)
    assert seen == [sbuf]
    assert freed == [IN]


def test_handler_that_frees_does_not_double_free(mod, xapp, freed):
    """Regression guard for handlers written against the old contract -- e.g.
    spectranet-xapps' A1 policy handler, which frees after an rmr_rts."""
    xapp.register_handler(lambda x, s, b: x.rmr_free(b))
    xapp._dispatch_event(xapp, _summary(mod), _sbuf(IN))
    assert freed == [IN]


def test_guard_absorbs_one_extra_free_not_arbitrarily_many(mod, xapp, freed):
    """The documented limit of the guard.

    It reconciles exactly one handler free with the framework's own -- the
    old-contract case. It cannot also absorb a handler that frees the *same*
    buffer twice, because once the token is consumed that is indistinguishable
    from the allocator reissuing the address to a new buffer (see
    test_address_reuse_after_release_is_not_swallowed), and swallowing that would
    leak. A handler freeing twice is a double free in its own right, and was one
    before this change too.
    """
    def handler(x, s, b):
        x.rmr_free(b)
        x.rmr_free(b)

    xapp.register_handler(handler)
    xapp._dispatch_event(xapp, _summary(mod), _sbuf(IN))
    assert freed == [IN, IN]           # both reach rmr_free_msg; no third


def test_handler_exception_still_frees(mod, xapp, freed):
    """The leak path before this fix: no try/finally, so any raise in the chain
    dropped the buffer."""
    def handler(x, s, b):
        raise RuntimeError("boom")

    xapp.register_handler(handler)
    with pytest.raises(RuntimeError, match="boom"):
        xapp._dispatch_event(xapp, _summary(mod), _sbuf(IN))
    assert freed == [IN]


def test_handle_alone_does_not_free(mod, xapp, freed):
    """handle() is the chain terminator, not the owner. Pins the removal of its
    rmr_free so nobody reinstates it."""
    xapp.handle(xapp, _summary(mod), _sbuf(IN))
    assert freed == []


# --- other buffers are not hijacked -------------------------------------------

def test_freeing_an_unrelated_buffer_passes_through(mod, xapp, freed):
    """The override must not swallow frees of outbound buffers the handler owns."""
    xapp.register_handler(lambda x, s, b: x.rmr_free(_sbuf(OTHER)))
    xapp._dispatch_event(xapp, _summary(mod), _sbuf(IN))
    assert freed == [OTHER, IN]


def test_rmr_free_outside_dispatch_passes_through(mod, xapp, freed):
    """Covers _BaseXapp.rmr_send freeing its own send buffer, and
    ricxappframe's handle_healthcheck."""
    xapp.rmr_free(_sbuf(OTHER))
    assert freed == [OTHER]


def test_address_reuse_after_release_is_not_swallowed(mod, xapp, freed):
    """The crux of clear-before-free.

    rmr_free_msg returns the address to the allocator, so the next
    rmr_alloc_msg on this thread can be handed it straight back. A token that
    still held that address would match the new buffer's free and swallow it --
    one leak traded for another. Two frees must reach rmr_free_msg, and the
    finally must add no third.
    """
    def handler(x, s, b):
        x.rmr_free(b)                 # releases the inbound buffer
        x.rmr_free(_sbuf(IN))         # allocator reissued the same address
    xapp.register_handler(handler)
    xapp._dispatch_event(xapp, _summary(mod), _sbuf(IN))
    assert freed == [IN, IN]


def test_reconstructed_pointer_to_the_inflight_buffer_is_matched(mod, xapp, freed):
    """A handler holding a different ctypes object for the same address still
    gets the idempotent path -- the _addr fallback behind the `is` fast path."""
    xapp.register_handler(lambda x, s, b: x.rmr_free(_sbuf(IN)))
    xapp._dispatch_event(xapp, _summary(mod), _sbuf(IN))
    assert freed == [IN]


# --- threading and nesting ----------------------------------------------------

def test_in_flight_token_is_per_thread(mod, xapp, freed):
    """rmr_free is reached from threads that never dispatch. Those must not see,
    or clear, the dispatch thread's token."""
    entered, release = threading.Event(), threading.Event()

    def handler(x, s, b):
        entered.set()
        release.wait(5)

    xapp.register_handler(handler)
    t = threading.Thread(target=xapp._dispatch_event, args=(xapp, _summary(mod), _sbuf(IN)))
    t.start()
    assert entered.wait(5)
    xapp.rmr_free(_sbuf(OTHER))       # from the main thread, mid-dispatch
    assert freed == [OTHER]
    release.set()
    t.join(5)
    assert freed == [OTHER, IN]


def test_nested_dispatch_restores_the_outer_token(mod, xapp, freed):
    """A handler that pumped the queue itself must not clobber the outer
    message's token and leak it."""
    def handler(x, s, b):
        x.register_handler(None)      # inner dispatch takes the handle() path
        x._dispatch_event(x, _summary(mod), _sbuf(OTHER))

    xapp.register_handler(handler)
    xapp._dispatch_event(xapp, _summary(mod), _sbuf(IN))
    assert freed == [OTHER, IN]       # inner released first, then the outer


# --- outbound: the control-request send buffer ---------------------------------

@pytest.fixture
def control(mod, monkeypatch):
    """A bare xAppControlService with the RMR send path faked out.

    Depends on `mod` only for the ricxappframe stubs it installs. Returns
    (service, calls) where calls records the send/free sequence; `state`
    controls what rmr_send_msg reports, so retry behaviour is drivable.
    """
    monkeypatch.delitem(sys.modules, CONTROL_MODULE, raising=False)
    cmod = importlib.import_module(CONTROL_MODULE)
    monkeypatch.setitem(sys.modules, CONTROL_MODULE, cmod)

    calls = types.SimpleNamespace(sends=[], frees=[], states=[], encoded=[])

    class _Mbuf:
        def __init__(self):
            self.contents = types.SimpleNamespace(state=0, mtype=0, sub_id=0)

    def send_msg(mrc, sbuf):
        # RMR hands back a buffer for the next send: the same mbuf re-armed on
        # success, the unsent one on failure.
        calls.sends.append(sbuf)
        sbuf.contents.state = calls.states.pop(0) if calls.states else 0
        return sbuf

    fake_rmr = types.SimpleNamespace(
        rmr_alloc_msg=lambda vctx, size, mtype: _Mbuf(),
        set_payload_and_length=lambda payload, sbuf: None,
        generate_and_set_transaction_id=lambda sbuf: None,
        rmr_set_meid=lambda sbuf, meid: None,
        rmr_send_msg=send_msg,
        rmr_free_msg=lambda sbuf: calls.frees.append(sbuf),
    )
    monkeypatch.setattr(cmod, "rmr", fake_rmr)

    class _Encoded:
        def encode(self, **kwargs):
            calls.encoded.append(kwargs)
            return 7, b"payload"

    monkeypatch.setattr(cmod, "ControlRequestMsg", _Encoded)

    class _Bare(cmod.xAppControlService):
        def __init__(self):
            self._mrc = object()
            self.logger = _Logger()
            self.function_id = 255
            self._ack_route = None
            self._ack_route_warned = False

    return _Bare(), calls


def test_send_control_request_frees_the_send_buffer(control):
    """RMR does not take ownership on send: without the free the xApp leaks one
    4 KiB buffer per control request, for its whole lifetime."""
    svc, calls = control
    svc.send_control_request_rmr(e2_node_id="gnb", control_header=b"h", control_message=b"m")
    assert len(calls.sends) == 1
    # The pointer freed is the one rmr_send_msg last returned, not the allocated one.
    assert calls.frees == [calls.sends[-1]]


def test_send_control_request_retries_then_frees_once(control):
    """A single attempt drops the request silently on RMR_ERR_RETRY."""
    svc, calls = control
    calls.states = [1, 1, 0]
    svc.send_control_request_rmr(e2_node_id="gnb", control_header=b"h", control_message=b"m")
    assert len(calls.sends) == 3
    assert len(calls.frees) == 1


def test_send_control_request_frees_when_every_retry_fails(control):
    svc, calls = control
    calls.states = [1] * 10
    svc.send_control_request_rmr(e2_node_id="gnb", control_header=b"h",
                                 control_message=b"m", retries=10)
    assert len(calls.sends) == 10
    assert len(calls.frees) == 1
    assert any("not sent after 10 attempts" in line for line in svc.logger.lines)


# --- the ricInstanceID the control request carries ---------------------------------

def test_control_carries_the_ack_route_id(control):
    """E2Term routes the acknowledge by this id (see utils/ack_route.py)."""
    svc, calls = control
    svc._ack_route = types.SimpleNamespace(instance_id=61234)
    svc.send_control_request_rmr(e2_node_id="gnb", control_header=b"h", control_message=b"m")
    assert calls.encoded[0]["request_sequence_number"] == 61234


def test_control_sends_0_with_one_error_until_the_route_is_registered(control):
    svc, calls = control
    svc._ack_route = types.SimpleNamespace(instance_id=None)
    for _ in range(2):
        svc.send_control_request_rmr(e2_node_id="gnb", control_header=b"h", control_message=b"m")
    assert [kw["request_sequence_number"] for kw in calls.encoded] == [0, 0]
    assert sum("no control-ack route" in line for line in svc.logger.lines) == 1


def test_control_never_sends_an_id_outside_the_e2ap_range(control):
    """The gNB asserts ricInstanceID < 65536: an OAI build aborts on anything else."""
    svc, calls = control
    svc.send_control_request_rmr(e2_node_id="gnb", control_header=b"h", control_message=b"m",
                                 request_sequence_number=70000)
    assert calls.encoded[0]["request_sequence_number"] == 0
