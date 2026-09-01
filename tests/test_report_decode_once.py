"""The E2AP indication is decoded once per message, not once per decorator frame.

Frames are stacked as a decorator chain and each one calls _handle_indication for
every RIC_INDICATION, discarding the result unless the function id is its own. A
four-frame chain (RC, CCC, dApp, KPM) therefore used to run four full ASN.1
decodes per indication -- three of them thrown away -- on the single thread that
ricxappframe dispatches indications from.
"""

import pytest

from _env import requires_ricxappframe

pytestmark = requires_ricxappframe


@pytest.fixture
def report_mod():
    import xdevsm.decorators.report as report
    return report


class _Logger:
    """Minimal stand-in for mdclogpy.Logger."""

    def __init__(self):
        self.lines = []

    def _record(self, msg):
        self.lines.append(msg)

    debug = info = warning = error = _record

    def get_level(self):
        from mdclogpy import Level
        return Level.INFO


class _CountingIndicationMsg:
    """Replaces ricxappframe's IndicationMsg and counts every decode."""

    decodes = 0

    def decode(self, payload):
        type(self).decodes += 1
        self.function_id = int(payload[0])
        self.indication_header = b"\x01\x02"
        self.indication_message = b"\x03\x04"


def _make_chain(report, logger, function_ids):
    """Build a decorator chain of bare xAppReportService frames.

    The real frames need a live RMR xApp to construct, and none of that is
    involved in what is under test here.
    """

    class _Frame(report.xAppReportService):
        def __init__(self, function_id, downstream):
            self.function_id = function_id
            self._xapp_handler = downstream
            self.logger = logger
            self.handled = []

        def handle(self, xapp, summary, sbuf):
            from ricxappframe.xapp_frame import rmr
            from xdevsm.utils.constants import Values
            if summary[rmr.RMR_MS_MSG_TYPE] == Values.RIC_INDICATION:
                self._handle_indication(xapp, summary)
            if self._xapp_handler is not None:
                self._xapp_handler.handle(xapp, summary, sbuf)

        def decode_message(self, function_id, ba_ind_header, ba_ind_msg, meid, sub_id):
            self.handled.append(function_id)

        def send(self, *args, **kwargs):
            pass

        def terminate(self, signum, frame):
            pass

        def get_ran_function_description(self, json_ran_info):
            pass

    downstream = None
    frames = []
    for fid in reversed(function_ids):        # built bottom-up, like the xApps do
        downstream = _Frame(fid, downstream)
        frames.append(downstream)
    frames.reverse()
    return frames


def _summary(function_id):
    from ricxappframe.xapp_frame import rmr
    from xdevsm.utils.constants import Values
    return {
        rmr.RMR_MS_MSG_TYPE: Values.RIC_INDICATION,
        # A fresh bytes object per message: the decode cache is keyed on its identity.
        rmr.RMR_MS_PAYLOAD: bytes([function_id, 0xAA, 0xBB]),
        rmr.RMR_MS_SUB_ID: 1,
        "meid": b"gnb1",
    }


class _Xapp:
    def __init__(self, logger):
        self.logger = logger


def test_indication_is_decoded_once_for_the_whole_chain(report_mod, monkeypatch):
    monkeypatch.setattr(report_mod, "IndicationMsg", _CountingIndicationMsg)
    monkeypatch.setattr(report_mod._decoded, "entry", None, raising=False)
    _CountingIndicationMsg.decodes = 0

    logger = _Logger()
    frames = _make_chain(report_mod, logger, [3, 149, 255, 2])   # RC, CCC, dApp, KPM
    xapp = _Xapp(logger)

    frames[0].handle(xapp, _summary(2), None)                    # a KPM indication

    assert _CountingIndicationMsg.decodes == 1, (
        "expected one decode for the chain, got {}".format(_CountingIndicationMsg.decodes))


def test_only_the_matching_frame_decodes_the_service_model(report_mod, monkeypatch):
    monkeypatch.setattr(report_mod, "IndicationMsg", _CountingIndicationMsg)
    monkeypatch.setattr(report_mod._decoded, "entry", None, raising=False)

    logger = _Logger()
    frames = _make_chain(report_mod, logger, [3, 149, 255, 2])
    xapp = _Xapp(logger)

    frames[0].handle(xapp, _summary(255), None)                  # a dApp indication

    handled = {f.function_id: f.handled for f in frames}
    assert handled[255] == [255]
    assert handled[3] == [] and handled[149] == [] and handled[2] == []


def test_each_message_is_decoded_again(report_mod, monkeypatch):
    """The cache is per message, not per process: a second indication must not
    be served the first one's decode."""
    monkeypatch.setattr(report_mod, "IndicationMsg", _CountingIndicationMsg)
    monkeypatch.setattr(report_mod._decoded, "entry", None, raising=False)
    _CountingIndicationMsg.decodes = 0

    logger = _Logger()
    frames = _make_chain(report_mod, logger, [3, 149, 255, 2])
    xapp = _Xapp(logger)

    frames[0].handle(xapp, _summary(2), None)
    frames[0].handle(xapp, _summary(255), None)
    frames[0].handle(xapp, _summary(149), None)

    assert _CountingIndicationMsg.decodes == 3
    handled = {f.function_id: f.handled for f in frames}
    assert handled[2] == [2] and handled[255] == [255] and handled[149] == [149]


def test_debug_enabled_tracks_the_logger_level():
    from mdclogpy import Level
    from xdevsm.utils import utility

    class _L:
        def __init__(self, level):
            self._level = level

        def get_level(self):
            return self._level

    assert utility.debug_enabled(_L(Level.DEBUG)) is True
    assert utility.debug_enabled(_L(Level.INFO)) is False
    assert utility.debug_enabled(object()) is True   # unknown logger: do not suppress
