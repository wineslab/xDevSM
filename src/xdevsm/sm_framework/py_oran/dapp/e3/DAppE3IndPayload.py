import ctypes
from xdevsm.sm_framework.py_oran.dapp.enums import *

from xdevsm.sm_framework.py_oran.ByteArray import ByteArray
from xdevsm.sm_framework.lib.library_wrapper import dApp_lib, wrap_functions

class spectrum_sm_report_t(ctypes.Structure):
    # Mirrors spectrum_sm_report_t in FlexRIC's
    # src/sm/dapp_sm/e3/service_models/spectrum_sm/ir/spectrum_report.h. Field
    # ORDER and TYPES must match the libdapp_sm.so shipped beside this file --
    # ctypes reads by offset and will not complain about a mismatch, it will just
    # return the wrong number.
    _fields_ = [
        ("prb_count", ctypes.c_long),
        ("prbs", ctypes.POINTER(ctypes.c_uint16)),
        ("timestamp_ns", ctypes.c_int64),
    ]

class DAppE3IndPayload(ctypes.Structure):
    
    class Union(ctypes.Union):
        _fields_ = [
            ("spectrum", spectrum_sm_report_t),
        ]

    _fields_ = [
        ("type", dapp_e3_sm_type_e),
        ("u", Union),
    ]

class DAppE3IndPayloadWrapper():
    def __init__(self, ran_func_id: ctypes.c_uint32, byte_array: ByteArray):
        self.ran_function_id = ran_func_id
        self.byte_array = byte_array
        self.dapp_e3_ind_payload: DAppE3IndPayload = None
        self.free_ind_payload = wrap_functions(dApp_lib, 'free_dapp_e3_ind_payload', None, [ctypes.POINTER(DAppE3IndPayload)])
        self.decode_e3_ind_payload = wrap_functions(dApp_lib, 'dapp_dec_e3_indication', ctypes.c_bool, [ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(DAppE3IndPayload)])


    def decode(self) -> DAppE3IndPayload:
        if self.byte_array is None:
            return None
        
        # print(self.byte_array.len)
        # print(len(self.byte_array))
        payload = DAppE3IndPayload()

        ok = self.decode_e3_ind_payload(self.ran_function_id, self.byte_array.buf, self.byte_array.len, ctypes.byref(payload))
        
        if not ok:
            return None

        self.dapp_e3_ind_payload = payload
        return payload

    def get_spectrum_report(self) -> list:
        if self.dapp_e3_ind_payload is None:
            print("DApp E3 Indication Payload is None, cannot get spectrum report")
            return None
        if self.dapp_e3_ind_payload.type.value != dapp_e3_sm_type_e.DAPP_E3_SM_SPECTRUM:
            print("DApp E3 Indication Payload type is not SPECTRUM, cannot get spectrum report {}".format(self.dapp_e3_ind_payload.type.value))
            return None
        prb_count = self.dapp_e3_ind_payload.u.spectrum.prb_count
        prbs_ptr = self.dapp_e3_ind_payload.u.spectrum.prbs
        prbs = []
        for i in range(prb_count):
            prbs.append(prbs_ptr[i])
        return prbs
    
    def get_timestamp_ns(self):
        """Producer timestamp of the spectrum report, in CLOCK_REALTIME nanoseconds.

        Stamped by the dApp as it encodes the report and relayed by the gNB without
        being decoded, so it survives to the xApp unchanged. Realtime rather than
        monotonic because the two ends are on different hosts -- which also means a
        difference against the receiver's own clock carries their NTP skew and is a
        hop estimate, not an exact transit.

        Do not difference it against the monotonic timestamps the RAN puts on its own
        indications (Spectrum-SensingIndication, L1KPMIndication): those cannot leave
        the host and are on a different clock entirely.

        Returns None when the payload is absent, is not a spectrum report, or carries
        no stamp (0 is the "not set" value on the wire).
        """
        if self.dapp_e3_ind_payload is None:
            return None
        if self.dapp_e3_ind_payload.type.value != dapp_e3_sm_type_e.DAPP_E3_SM_SPECTRUM:
            return None
        ts = int(self.dapp_e3_ind_payload.u.spectrum.timestamp_ns)
        return ts if ts else None

    def __del__(self):
        if self.dapp_e3_ind_payload is not None:
            self.free_ind_payload(self.dapp_e3_ind_payload)