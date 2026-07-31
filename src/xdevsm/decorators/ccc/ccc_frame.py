from typing import List, Optional, Tuple

from ricxappframe.xapp_frame import rmr

from xdevsm.decorators.report import xAppReportService

from xdevsm.utils.constants import Values

from xdevsm.sm_framework.py_oran.ccc.constants import (
    SM_CCC_ID,
    STRUCT_O_NRCELLDU,
    REPORT_TYPE_ALL,
    REPORT_STYLE_CELL_LEVEL,
)
from xdevsm.sm_framework.py_oran.ccc.ccc_encoder import (
    encode_event_trigger_periodic,
    encode_action_definition_cell_level,
)
from xdevsm.sm_framework.py_oran.ccc.ccc_decoder import (
    CccIndicationHeader,
    CccIndicationMessage,
)


class XappCccFrame(xAppReportService):
    """
    CCC REPORT decorator. Mirrors XappKpmFrame's lifecycle but speaks
    JSON instead of the ASN.1-backed flexric helpers.
    """

    def __init__(
        self,
        xapp_handler,
        logger,
        server,
        xapp_name,
        rmr_port,
        http_port,
        pltnamespace,
        app_namespace,
    ):
        super().__init__(
            xapp_handler, logger, server, xapp_name, rmr_port, http_port, pltnamespace, app_namespace
        )
        # FlexRIC SM identifier — used to filter the incoming indication
        # messages that come back over RMR. The RIC will assign a runtime
        # RAN Function ID matching this plugin.
        self.function_id = SM_CCC_ID

    # ------------------------------------------------------------------
    # Inbound: indication dispatch
    # ------------------------------------------------------------------

    def handle(self, xapp, summary, sbuf):
        xapp.logger.debug("[XappCccFrame] received: {}".format(summary))
        if summary[rmr.RMR_MS_MSG_TYPE] == Values.RIC_INDICATION:
            self._handle_indication(xapp, summary)
        elif summary[rmr.RMR_MS_MSG_TYPE] == Values.RIC_ERROR_INDICATION:
            xapp.logger.error("[XappCccFrame] Error indication received")
        else:
            xapp.logger.debug(
                "[XappCccFrame] unhandled message type: {}".format(summary[rmr.RMR_MS_MSG_TYPE])
            )
        self._xapp_handler.handle(xapp, summary, sbuf)

    def decode_message(self, function_id, ba_ind_header, ba_ind_msg, meid, sub_id):
        self.logger.info("[XappCccFrame] E2AP function id: {}".format(function_id))
        if function_id != self.function_id:
            self.logger.info(
                "[XappCccFrame] indication for different function id: {}".format(function_id)
            )
            return

        # The base xAppReportService calls get_c_byte_array_from_py_byte_string
        # which returns a ctypes uint8 array (or None). Convert it to a Python
        # bytes object so the pure-Python CCC JSON decoders can consume it.
        hdr_bytes = bytes(ba_ind_header) if ba_ind_header is not None else b""
        msg_bytes = bytes(ba_ind_msg) if ba_ind_msg is not None else b""

        hdr = CccIndicationHeader(hdr_bytes)
        msg = CccIndicationMessage(msg_bytes)

        self.logger.info(
            "[XappCccFrame] decoded header: reason={} eventTime={}".format(
                hdr.indication_reason, hdr.event_time
            )
        )

        cb = self.get_indication_msg_callback()
        if cb is None:
            self._log_default(hdr, msg)
        else:
            cb(hdr, msg, meid, sub_id)

    def _log_default(self, hdr: CccIndicationHeader, msg: CccIndicationMessage) -> None:
        for cell, struct in msg.iter_structures():
            cgi = cell.get("cellGlobalId", {})
            name = struct.get("ranConfigurationStructureName")
            vs = (struct.get("valuesOfAttributes") or {}).get("ranConfigurationStructure") or {}
            arfcn_dl = vs.get("arfcnDL")
            bw_dl = vs.get("bSChannelBwDL")
            bwps = vs.get("bWPList") or []
            self.logger.info(
                "[XappCccFrame] cell={} struct={} arfcnDL={} bSChannelBwDL={} bWPs={}".format(
                    cgi, name, arfcn_dl, bw_dl, len(bwps)
                )
            )
            for i, b in enumerate(bwps):
                self.logger.info(
                    "[XappCccFrame]   BWP[{}] scs={} numberOfRBs={} startRB={} ctx={}".format(
                        i,
                        b.get("subCarrierSpacing"),
                        b.get("numberOfRBs"),
                        b.get("startRB"),
                        b.get("bwpContext"),
                    )
                )

    # ------------------------------------------------------------------
    # Outbound: subscription
    # ------------------------------------------------------------------

    def subscribe(
        self,
        gnb,
        ran_period_ms: int = 1000,
        ran_cfg_structure_name: str = STRUCT_O_NRCELLDU,
        attributes: Optional[List[str]] = None,
        report_type: str = REPORT_TYPE_ALL,
        cell_global_id: Optional[dict] = None,
        action_type: str = Values.ACTION_TYPE,
    ):
        """Subscribe the dApp to a periodic CCC REPORT.

        Defaults to REPORT Style 2 (cell-level) on O-NRCellDU with the
        three attributes targeted by this implementation iteration:
        arfcnDL, bSChannelBwDL, bWPList.
      
        """
        if attributes is None:
            attributes = ["arfcnDL", "bSChannelBwDL", "bWPList"]

        self.logger.info(
            "[XappCccFrame] preparing subscription for gnb={} ran_period_ms={} attrs={}".format(
                getattr(gnb, "inventory_name", "?"), ran_period_ms, attributes
            )
        )

        if self.subscriber.ResponseHandler(self.subs_response_cb, self.server) is not True:
            self.logger.error("Error when trying to set the subscription response callback")

        ev_trig = encode_event_trigger_periodic(ran_period_ms)
        act_def = encode_action_definition_cell_level(
            ran_cfg_structure_name=ran_cfg_structure_name,
            attribute_names=attributes,
            cell_global_id=cell_global_id,
            report_type=report_type,
            ric_style_type=REPORT_STYLE_CELL_LEVEL,
        )

        action = self.subscriber.ActionToBeSetup(
            action_id=1,
            action_type=action_type,
            action_definition=act_def.byte_array_to_tuple(),
            subsequent_action=self.subscriber.SubsequentAction(
                subsequent_action_type="continue", time_to_wait="w5ms"
            ),
        )

        _, sub_id = self.send_subscription(gnb, ev_trig, [action])
        return sub_id
    # ------------------------------------------------------------------
    # Convenience: ad-hoc subscription helper
    # ------------------------------------------------------------------

    def subscribe_arfcn_bw_bwps(self, gnb, ran_period_ms: int = 1000):
        """One-call helper for the three target metrics of this iteration."""
        return self.subscribe(
            gnb=gnb,
            ran_period_ms=ran_period_ms,
            ran_cfg_structure_name=STRUCT_O_NRCELLDU,
            attributes=["arfcnDL", "bSChannelBwDL", "bWPList"],
        )

    def terminate(self, signum, frame):
        # Per-service-model teardown hook. The base xAppReportService already
        # unsubscribes this frame's subscriptions and delegates termination down
        # the chain; override here if CCC ever needs extra cleanup.
        super().terminate(signum, frame)

