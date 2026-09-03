"""Per-E2-node subscription ownership and cleanup."""

import threading

import pytest

from _env import requires_ricxappframe

pytestmark = requires_ricxappframe


class _Logger:
    def __init__(self):
        self.info_lines = []
        self.error_lines = []

    def info(self, message):
        self.info_lines.append(message)

    def error(self, message):
        self.error_lines.append(message)


class _Subscriber:
    def __init__(self, fail=None):
        self.deleted = []
        self.fail = fail

    def Unsubscribe(self, subscription_id):
        self.deleted.append(subscription_id)
        if subscription_id == self.fail:
            raise RuntimeError("delete failed")


def _report(subscription_ids, pending=None, fail=None):
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
    report.subscriber = _Subscriber(fail=fail)
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
