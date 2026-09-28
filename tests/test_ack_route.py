"""The control-acknowledge route (xdevsm.utils.ack_route).

AckRoute is driven one registration pass at a time against a fake rtmgr, so no
thread or network is involved. The id it puts in the control request is tested
with the other control-send tests, in test_rmr_buffer_ownership.
"""

from xdevsm.utils.ack_route import ID_MAX, ID_MIN, AckRoute

ME = "service-ricxapp-j-decision-engine-xapp-rmr.ricxapp-j:4560"


class _Logger:
    def __init__(self):
        self.debugs = []
        self.errors = []

    def debug(self, msg):
        self.debugs.append(msg)

    def error(self, msg):
        self.errors.append(msg)


class _Response:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self.text = "Invalid data" if status_code >= 400 else ""
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("HTTP {}".format(self.status_code))


class _Rtmgr:
    """rtmgr's northbound API: serves a route table, records registrations.

    post_status is consumed one per POST; its last value repeats.
    """

    def __init__(self, table=(), post_status=(201,)):
        self.table = list(table)
        self.post_status = list(post_status)
        self.posts = []
        self.deletes = []

    def get(self, url, timeout):
        return _Response(200, {"RouteTable": self.table})

    def post(self, url, json, timeout):
        self.posts.append(json)
        status = self.post_status.pop(0) if len(self.post_status) > 1 else self.post_status[0]
        return _Response(status)

    def delete(self, url, json, timeout):
        self.deletes.append(json)
        return _Response(200)


def _route(rtmgr):
    return AckRoute(_Logger(), "ricxapp-j", "decision-engine-xapp", 4560, "ricplt-j", http=rtmgr)


# --- registration --------------------------------------------------------------

def test_registers_an_id_for_this_xapps_rmr_endpoint():
    rtmgr = _Rtmgr()
    route = _route(rtmgr)
    route._register()

    assert route.handle_url == "http://service-ricplt-j-rtmgr-http.ricplt-j:3800/ric/v1/handles/xapp-subscription-handle"
    body = rtmgr.posts[0]
    assert body["address"] == "service-ricxapp-j-decision-engine-xapp-rmr.ricxapp-j"
    assert body["port"] == 4560
    assert ID_MIN <= body["subscription_id"] <= ID_MAX
    assert route.instance_id == body["subscription_id"]


def test_no_id_until_rtmgr_accepts_the_registration():
    """rtmgr answers 400 until appmgr has registered the xApp."""
    route = _route(_Rtmgr(post_status=(400, 400, 201)))
    route._register()
    route._register()
    assert route.instance_id is None
    route._register()
    assert route.instance_id is not None


def test_keepalive_reposts_the_same_id():
    """rtmgr forgets these registrations when it restarts."""
    rtmgr = _Rtmgr()
    route = _route(rtmgr)
    route._register()
    route._register()
    assert rtmgr.posts[0] == rtmgr.posts[1]


def test_picks_an_id_no_route_uses():
    free = 61234
    table = ["mse|12041|{}|service-other-rmr.ns:4560\n".format(i)
             for i in range(ID_MIN, ID_MAX + 1) if i != free]
    rtmgr = _Rtmgr(table)
    _route(rtmgr)._register()
    assert rtmgr.posts[0]["subscription_id"] == free


def test_registers_even_when_the_route_table_cannot_be_read():
    rtmgr = _Rtmgr()
    rtmgr.get = lambda url, timeout: _Response(503)
    route = _route(rtmgr)
    route._register()
    assert route.instance_id is not None


def test_route_table_parsing():
    rtmgr = _Rtmgr([
        "newrt|start\n",
        "mse|12041|-1|{}\n".format(ME),                        # the shared default route
        "mse|12050|61000|service-x-rmr.ns:4560\n",             # not an ack route
        "mse|12042,e2t:38000|61001|a:1,b:2;c:3\n",             # sender list, groups
        "mse|12041|61002|{}\n".format(ME),
    ])
    assert _route(rtmgr)._ack_routes() == {61001: {"a:1", "b:2", "c:3"}, 61002: {ME}}


# --- two xApps on one id --------------------------------------------------------

def test_clash_moves_the_endpoint_that_sorts_later():
    rtmgr = _Rtmgr()
    route = _route(rtmgr)
    route._register()
    rid = route.instance_id
    rtmgr.table = ["mse|12041|{}|{}\n".format(rid, ME),
                   "mse|12041|{}|service-aaa-rmr.ns:4560\n".format(rid)]
    route._register()
    assert rtmgr.deletes == [rtmgr.posts[0]]
    assert route.instance_id not in (None, rid)


def test_clash_keeps_the_id_when_this_endpoint_sorts_first():
    rtmgr = _Rtmgr()
    route = _route(rtmgr)
    route._register()
    rid = route.instance_id
    rtmgr.table = ["mse|12041|{}|service-zzz-rmr.ns:4560\n".format(rid)]
    route._register()
    assert rtmgr.deletes == []
    assert route.instance_id == rid


# --- removal and errors ---------------------------------------------------------

def test_stop_removes_the_registration_once():
    rtmgr = _Rtmgr()
    route = _route(rtmgr)
    route._register()
    route.stop()
    route.stop()                       # atexit after terminate: a no-op
    assert rtmgr.deletes == [rtmgr.posts[0]]
    assert route.instance_id is None


def test_stop_during_the_post_leaves_nothing_behind():
    rtmgr = _Rtmgr()
    route = _route(rtmgr)
    route._stop.set()
    route._register()
    assert rtmgr.deletes == rtmgr.posts
    assert route.instance_id is None


def test_one_error_after_repeated_failures():
    route = _route(_Rtmgr(post_status=(400,)))
    for _ in range(AckRoute.ERROR_AFTER + 5):
        route._register()
    assert len(route.logger.errors) == 1
