"""xDevSM's mirror of the subset of libe3's shared stage catalog this
framework stamps: the E2AP and E2SM-DAPP codec boxes on the Path-B loop
(B3/B5/B6 in libe3's docs/path-b-e2-e3-loop.md).

Source of truth: libe3/include/libe3/latrec.h (branch feat/latency-tracing).
These are shared, cross-repo identifiers -- do not renumber locally. A value
that drifts from libe3's header breaks the join with every other
component's rings silently (no runtime check catches it on this side).

XAPP_PROCESS_DONE (0x62, B4's exit) is deliberately not stamped by this
package: B4 is the researcher's own xApp callback, not the framework.
"""

DECODE_E2AP_BEGIN = 0x5A
DECODE_E2AP_DONE = 0x5B
DECODE_E2SM_BEGIN = 0x60
DECODE_E2SM_DONE = 0x61
ENCODE_E2SM_BEGIN = 0x63
ENCODE_E2SM_DONE = 0x64
ENCODE_E2AP_BEGIN = 0x58
ENCODE_E2AP_DONE = 0x59
