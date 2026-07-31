"""E2SM-RC REPORT Style 1 "Message Copy" report decorator.

Mirrors ``XappKpmFrame``/``XappCccFrame`` (subscribe -> receive indications ->
decode -> callback), but for E2SM-RC REPORT Service Style 1 "Message Copy": it
subscribes so the gNB copies the UE's UL-DCCH RRC MeasurementReport to the xApp,
decodes the neighbour-cell measurements from it, and hands them to the registered
callback (the data ingestor writes them to ``ue-neighbor-meas``).

The E2SM-RC + NR-RRC decode/encode lives in ``rc_report_codec``, backed by the
``rc_report_*`` ABI of the bundled ``librc_1_03.so``. Against an older library that
does not export it, ``subscribe`` raises RuntimeError -- the data ingestor guards
the call so KPM/dApp/CCC ingestion is unaffected.
"""

from xdevsm.decorators.report import xAppReportService

from ricxappframe.xapp_frame import rmr

from xdevsm.utils.constants import Values

from xdevsm.sm_framework.py_oran.rc.rc_report_codec import (
    RC_REPORT_STYLE_MESSAGE_COPY,
    decode_meas_report,
    encode_report_subscription,
)


class XappRcReportFrame(xAppReportService):
    """RC REPORT "Message Copy" decorator (RAN function id 3)."""

    def __init__(self, xapp_handler, logger, server, xapp_name,
                 rmr_port, http_port, pltnamespace, app_namespace):
        super().__init__(xapp_handler, logger, server, xapp_name,
                         rmr_port, http_port, pltnamespace, app_namespace)
        self.function_id = 3  # E2SM-RC

    # -- indication path -----------------------------------------------------
    def handle(self, xapp, summary, sbuf):
        xapp.logger.debug("[XappRcReportFrame] received: {}".format(summary))
        if summary[rmr.RMR_MS_MSG_TYPE] == Values.RIC_INDICATION:
            self._handle_indication(xapp, summary)
        elif summary[rmr.RMR_MS_MSG_TYPE] == Values.RIC_ERROR_INDICATION:
            xapp.logger.error("[XappRcReportFrame] Error in indication message")
        # delegate down the decorator chain (KPM/dApp/CCC still get their turn)
        self._xapp_handler.handle(xapp, summary, sbuf)

    def decode_message(self, function_id, ba_ind_header, ba_ind_msg, meid, sub_id):
        if function_id != self.function_id:
            self.logger.debug(
                "[XappRcReportFrame] indication for different function id: {}".format(function_id))
            return

        try:
            decoded = decode_meas_report(ba_ind_header, ba_ind_msg)
        except Exception as e:
            self.logger.error("[XappRcReportFrame] failed to decode RC/MeasReport indication: {}".format(e))
            return

        if not decoded.is_meas_report:
            # A copied RRC message that was not a MeasurementReport (or failed the
            # inner decode) -- nothing to store.
            self.logger.debug(
                "[XappRcReportFrame] RC message copy (ev_trigger_id={}) was not a MeasurementReport".format(
                    decoded.ev_trigger_id))
            return

        callback = self.get_indication_msg_callback()
        if callback is None:
            self.logger.info(
                "[XappRcReportFrame] no callback; {} neighbour meas dropped".format(
                    len(decoded.get_neighbor_measurements())))
            return
        # Same callback signature as KPM/CCC: (ind_hdr, ind_msg, meid, sub_id).
        callback(ba_ind_header, decoded, meid, sub_id)

    # -- subscription path ---------------------------------------------------
    def subscribe(self, gnb, ran_period_ms: int = 1000, action_type=Values.ACTION_TYPE):
        """Subscribe to REPORT Style 1 "Message Copy" of the UL-DCCH
        MeasurementReport for ``gnb``. Returns the submgr subscription id."""
        self.logger.info(
            "[XappRcReportFrame] Preparing RC REPORT (Style {}) subscription for gnb: {}".format(
                RC_REPORT_STYLE_MESSAGE_COPY, gnb.inventory_name))

        if self.subscriber.ResponseHandler(self.subs_response_cb, self.server) is not True:
            self.logger.error("Error when trying to set the subscription response callback")

        # Encode the event trigger (Message Event -> MeasurementReport) and the
        # REPORT Style 1 action definition (RAN param 'RRC Message').
        ev_trigger_enc, action_def_enc = encode_report_subscription(ran_period_ms=ran_period_ms)

        action = self.subscriber.ActionToBeSetup(
            action_id=1,
            action_type=action_type,
            action_definition=action_def_enc.byte_array_to_tuple(),
            subsequent_action=self.subscriber.SubsequentAction(
                subsequent_action_type="continue", time_to_wait="w5ms"),
        )

        result = self.send_subscription(gnb, ev_trigger_enc, [action])
        if result is None:
            return None
        _, sub_id = result
        return sub_id

    def terminate(self, signum, frame):
        # base xAppReportService unsubscribes this frame's subscriptions, then
        # delegates termination down the chain.
        super().terminate(signum, frame)
