"""Per-E2-node subscription ownership and cleanup."""

import threading

import pytest

from _env import requires_ricxappframe

pytestmark = requires_ricxappframe


class _Logger:
    def __init__(self):
        self.info_lines = []
        self.error_lines = []
        self.debug_lines = []

    def info(self, message):
        self.info_lines.append(message)

    def error(self, message):
        self.error_lines.append(message)

    def debug(self, message):
        self.debug_lines.append(message)


class _Subscriber:
    """Mirrors xapp_sub.NewSubscriber.Unsubscribe, which RETURNS the HTTP
    status rather than raising on it."""

    def __init__(self, fail=None, reject=None):
        self.deleted = []
        self.fail = fail        # connection-level failure -> raises
        self.reject = reject    # submgr answers with an error status

    def Unsubscribe(self, subscription_id):
        self.deleted.append(subscription_id)
        if subscription_id == self.fail:
            raise RuntimeError("delete failed")
        if subscription_id == self.reject:
            return b"", "Bad Request", 400
        return b"", "No Content", 204


def _report(subscription_ids, pending=None, fail=None, reject=None):
    from xdevsm.decorators.report import xAppReportService

    class _ConcreteReport(xAppReportService):
        def decode_message(self, hdr, msg):
            return None

    report = object.__new__(_ConcreteReport)
    report.subscription_id = {
        inventory: list(ids) for inventory, ids in subscription_ids.items()
    }
    report._pending_resolutions = dict(pending or {})
    report._subscription_lock = threading.RLock()
    report.subscriber = _Subscriber(fail=fail, reject=reject)
    report.logger = _Logger()
    report.uri_subscriptions = "http://submgr/ric/v1/subscriptions"
    return report


def test_unsubscribe_gnb_removes_only_the_selected_node():
    report = _report(
        {"gnb-a": ["a-1", "a-2"], "gnb-b": ["b-1"]},
        {"a-1": "gnb-a", "a-2": "gnb-a", "b-1": "gnb-b"},
    )

    assert report.unsubscribe_gnb("gnb-a") == ["a-1", "a-2"]
    assert report.subscriber.deleted == ["a-1", "a-2"]
    assert report.subscription_id == {"gnb-b": ["b-1"]}
    assert report._pending_resolutions == {"b-1": "gnb-b"}


def test_unsubscribe_gnb_is_idempotent_and_keeps_local_state_clean_on_error():
    report = _report(
        {"gnb-a": ["a-1", "a-2"]},
        {"a-1": "gnb-a", "a-2": "gnb-a"},
        fail="a-1",
    )

    assert report.unsubscribe_gnb("gnb-a") == ["a-1", "a-2"]
    assert report.unsubscribe_gnb("gnb-a") == []
    assert report.subscription_id == {}
    assert report._pending_resolutions == {}
    assert report.subscriber.deleted == ["a-1", "a-2"]
    assert len(report.logger.error_lines) == 1


def test_unsubscribe_all_uses_per_node_cleanup():
    report = _report({"gnb-a": ["a-1"], "gnb-b": ["b-1"]})

    report.unsubscribe_all()

    assert report.subscription_id == {}
    assert report.subscriber.deleted == ["a-1", "b-1"]


# --- submgr answers with a status, it does not raise ----------------------


def test_rejected_delete_is_reported_even_though_no_exception_was_raised():
    """Unsubscribe returns (data, reason, status). A 400 read as success is how
    a subscription stays live at submgr while the xApp believes it is gone."""
    report = _report({"gnb-a": ["a-1"]}, {"a-1": "gnb-a"}, reject="a-1")

    report.unsubscribe_gnb("gnb-a")

    assert any("HTTP 400" in line for line in report.logger.error_lines)


def test_delete_of_an_unknown_subscription_is_not_an_error():
    """404 means submgr no longer holds it, which is the outcome we wanted."""
    report = _report({"gnb-a": ["a-1"]}, {"a-1": "gnb-a"})
    report.subscriber.Unsubscribe = lambda sub_id: (b"", "Not Found", 404)

    report.unsubscribe_gnb("gnb-a")

    assert report.logger.error_lines == []


def test_connection_failure_is_still_reported():
    report = _report({"gnb-a": ["a-1"]}, {"a-1": "gnb-a"}, fail="a-1")

    report.unsubscribe_gnb("gnb-a")

    assert any("delete failed" in line for line in report.logger.error_lines)


def test_late_response_for_a_detached_gnb_is_not_an_error():
    """unsubscribe_gnb detaches local state before the DELETE, so a response
    arriving afterwards finds nothing to remove. That is the design, not a fault."""
    report = _report({"gnb-a": ["a-1"]}, {"a-1": "gnb-a"})
    report.unsubscribe_gnb("gnb-a")

    report.remove_sub_id("a-1")

    assert report.logger.error_lines == []
    assert any("already detached" in line for line in report.logger.debug_lines)
