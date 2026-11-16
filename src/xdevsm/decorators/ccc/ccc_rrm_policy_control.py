from typing import Sequence, Union

from xdevsm.decorators.ccc.ccc_control import decode_ccc_control_ack
from xdevsm.decorators.control import xAppControlService
from xdevsm.sm_framework.py_oran.ccc.constants import RESOURCE_TYPE_PRB_DL
from xdevsm.sm_framework.py_oran.ccc.ccc_encoder import (
    RrmPolicySlice,
    encode_control_header,
    encode_rrm_policy_ratio_control,
    validate_slices,
)
from xdevsm._latrec.writer import tls_ring, seq_next, ctx_set
from xdevsm._latrec import stages
from xdevsm._latrec.stages import LATREC_ROLE as _LATREC_ROLE


class CccRrmPolicyRatioControl(xAppControlService):
    """
    E2SM-CCC RIC Control (style 2, cell level) for the O-RRMPolicyRatio structure.
    Call `send_policies()`, not `send()`. Take `function_id` from
    `ccc_decoder.find_ccc_function_id()`: the gNB assigns it at E2 Setup.
    The acknowledge callbacks receive a `CccControlAck` with the JSON outcome.
    """

    def __init__(self,
                 xapp_handler,
                 logger,
                 server,
                 xapp_name,
                 rmr_port,
                 http_port,
                 mrc,
                 pltnamespace,
                 app_namespace,
                 mcc,
                 mnc,
                 nci,
                 function_id):
        super().__init__(xapp_handler, logger, server, xapp_name, rmr_port, http_port, mrc, pltnamespace, app_namespace)
        self.service_style_name = "Cell Configuration and Control"
        self.function_id = function_id
        self.mcc = mcc
        self.mnc = mnc
        self.nci = nci

    def _decode_ack(self, pdu):
        return decode_ccc_control_ack(pdu)

    def send_policies(self,
                      e2_node_id,
                      slices: Sequence[Union[RrmPolicySlice, dict]],
                      resource_type=RESOURCE_TYPE_PRB_DL):
        """Send all slices in one control, so the cell applies them together and never holds half a policy.
        Raises before sending if any slice is invalid."""
        parsed = validate_slices(slices)
        header = encode_control_header().to_bytes()
        lr = tls_ring(_LATREC_ROLE)
        seq = seq_next()
        ctx_set(seq)
        lr.stamp(seq, stages.ENCODE_E2SM_BEGIN)
        message = encode_rrm_policy_ratio_control(self.mcc, self.mnc, self.nci, parsed, resource_type).to_bytes()
        lr.stamp(seq, stages.ENCODE_E2SM_DONE, aux=len(header) + len(message))
        self.logger.debug("[CccRrmPolicyRatioControl] control message: {}".format(message))
        self.send_control_request_rmr(e2_node_id=e2_node_id,
                                      control_header=header,
                                      control_message=message,
                                      seq=seq)
