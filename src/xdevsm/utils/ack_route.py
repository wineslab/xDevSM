"""A control-acknowledge route of this xApp's own.

E2Term routes a RIC_CONTROL_ACK / RIC_CONTROL_FAILURE by the ricInstanceID the
control request carried: it copies the id the E2 node echoes into the RMR
sub_id, and RMR looks up (mtype, sub_id) before falling back to (mtype, -1).
rtmgr gives the -1 route to every registered xApp and RMR keeps whichever line
it wrote last -- a random pick on every table push -- so an xApp that sends 0
receives its acks only while it happens to be last.

AckRoute registers an id with rtmgr through the same northbound call submgr
makes for a subscription (POST /ric/v1/handles/xapp-subscription-handle). That
gives this xApp a line nobody else has, ``mse|12041|<id>|<this xApp>`` (and
12042), and the control service then sends every control with that id. No E2
subscription is involved: the id only ever travels in control requests.
"""

import random
import threading

import requests

from xdevsm.utils.constants import Values

# ricInstanceID is INTEGER (0..65535). submgr hands out its ids from 1 upwards
# (hundreds at most in practice), so xApps take theirs from the top of the range.
ID_MIN = 60000
ID_MAX = 65534

_ACK_MTYPES = (str(Values.RIC_CONTROL_ACK), str(Values.RIC_CONTROL_FAILURE))


class AckRoute:
    # Consecutive failed registrations before the one error line: 30 s of
    # retries at start-up, or a quarter of an hour of failed keep-alives.
    ERROR_AFTER = 15

    def __init__(self, logger, app_namespace, xapp_name, rmr_port, pltnamespace,
                 keepalive_s=60.0, retry_s=2.0, http=requests):
        self.logger = logger
        # rtmgr accepts a registration only for an endpoint it already routes to,
        # matched on host and port: this xApp's RMR Service, as appmgr registered it.
        self.address = "service-{}-{}-rmr.{}".format(app_namespace, xapp_name, app_namespace)
        self.port = int(rmr_port)
        self.endpoint = "{}:{}".format(self.address, self.port)
        base = Values.GENERAL_PATH.format(pltnamespace, Values.RTMGR_SERVICE, pltnamespace, Values.RTMGR_PORT)
        self.handle_url = base + "/ric/v1/handles/xapp-subscription-handle"
        self.debug_url = base + "/ric/v1/getdebuginfo"
        self.keepalive_s = keepalive_s
        self.retry_s = retry_s
        self._http = http
        # The id rtmgr has accepted, read by the control service on every send;
        # None until the first registration succeeds.
        self.instance_id = None
        self._failures = 0
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        """Register in the background and keep the registration alive."""
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, name="xdevsm-ack-route", daemon=True)
            self._thread.start()

    def stop(self):
        """Stop the keep-alive and remove the registration from rtmgr."""
        self._stop.set()
        rid = self.instance_id
        self.instance_id = None
        if rid is not None:
            self._delete(rid)

    def _run(self):
        while not self._stop.is_set():
            try:
                self._register()
            except Exception as e:  # the keep-alive thread must survive anything
                self._failed("route update failed: {}".format(e))
            self._stop.wait(self.keepalive_s if self.instance_id is not None else self.retry_s)

    def _register(self):
        """Keep the current id, or pick a free one, and POST it.

        Re-posting an id rtmgr already holds is harmless, and needed: rtmgr keeps
        these registrations in memory only and, when it restarts, reloads just
        submgr's subscriptions.
        """
        routes = self._ack_routes()
        rid = self.instance_id
        if rid is not None and routes is not None and self._clashes(rid, routes):
            self.logger.debug("[AckRoute] e2-{} is also routed to another xApp; picking another id".format(rid))
            self._delete(rid)
            self.instance_id = None
            rid = None
        if rid is None:
            rid = self._pick(routes)
        if not self._post(rid):
            return
        if self._stop.is_set():
            # stop() ran while the POST was in flight: leave nothing behind.
            self._delete(rid)
            return
        if rid != self.instance_id:
            self.logger.debug("[AckRoute] e2-{} registered with rtmgr for {}".format(rid, self.endpoint))
        self.instance_id = rid
        self._failures = 0

    def _clashes(self, rid, routes):
        """Whether another xApp holds rid too. Of the two, the one whose endpoint
        sorts later gives the id up, so exactly one of them moves."""
        others = routes.get(rid, set()) - {self.endpoint}
        return bool(others) and min(others) < self.endpoint

    def _pick(self, routes):
        """A random id in ID_MIN..ID_MAX that no route in rtmgr's table uses."""
        taken = routes or {}
        return random.choice([i for i in range(ID_MIN, ID_MAX + 1) if i not in taken])

    def _ack_routes(self):
        """{sub_id: {endpoint, ...}} for every per-id ack/failure route in
        rtmgr's table, or None when the table cannot be read."""
        try:
            r = self._http.get(self.debug_url, timeout=5)
            r.raise_for_status()
            table = r.json()["RouteTable"]
        except Exception as e:
            self.logger.debug("[AckRoute] rtmgr route table unavailable: {}".format(e))
            return None
        routes = {}
        for line in table:
            # mse|<mtype>[,<sender>]|<sub_id>|<endpoint>[,<endpoint>...][;<group>...]
            fields = line.strip().split("|")
            if len(fields) != 4 or fields[0] != "mse":
                continue
            mtype = fields[1].split(",")[0]
            sub_id = fields[2]
            if mtype not in _ACK_MTYPES or sub_id == "-1":
                continue
            endpoints = [ep for ep in fields[3].replace(";", ",").split(",") if ep]
            routes.setdefault(int(sub_id), set()).update(endpoints)
        return routes

    def _body(self, rid):
        return {"address": self.address, "port": self.port, "subscription_id": rid}

    def _post(self, rid):
        try:
            r = self._http.post(self.handle_url, json=self._body(rid), timeout=5)
        except Exception as e:
            self._failed("rtmgr unreachable: {}".format(e))
            return False
        if 200 <= r.status_code < 300:
            return True
        # 400 until appmgr has registered this xApp with rtmgr.
        self._failed("rtmgr rejected e2-{} (HTTP {}): {}".format(rid, r.status_code, r.text))
        return False

    def _delete(self, rid):
        try:
            r = self._http.delete(self.handle_url, json=self._body(rid), timeout=5)
            self.logger.debug("[AckRoute] e2-{} removed from rtmgr (HTTP {})".format(rid, r.status_code))
        except Exception as e:
            self.logger.debug("[AckRoute] could not remove e2-{} from rtmgr: {}".format(rid, e))

    def _failed(self, why):
        self._failures += 1
        self.logger.debug("[AckRoute] {}".format(why))
        if self._failures == self.ERROR_AFTER:
            self.logger.error(
                "[AckRoute] no control-ack route for {} after {} attempts ({}): its control acks "
                "may be delivered to another xApp".format(self.endpoint, self._failures, why))
