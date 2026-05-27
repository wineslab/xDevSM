"""
E2SM-CCC constants (O-RAN.WG3.TS.E2SM-CCC-R004-v06.00).

Function ID is assigned at runtime by the RIC when registering the RAN
function, but we keep the FlexRIC plugin-side SM identifier here for the
dApp to filter inbound indications.
"""

# Must match flexric/src/sm/ccc_sm/ccc_sm_id.h:SM_CCC_ID.
SM_CCC_ID = 149

SM_CCC_OID = "1.3.6.1.4.1.53148.1.1.2.4"
SM_CCC_NAME = "ORAN-E2SM-CCC"

# RIC Service Styles (§7.4)
REPORT_STYLE_NODE_LEVEL = 1
REPORT_STYLE_CELL_LEVEL = 2

# IE Formats (§7.8)
EVENT_TRIGGER_FORMAT_NODE_CHANGE = 1
EVENT_TRIGGER_FORMAT_CELL_CHANGE = 2
EVENT_TRIGGER_FORMAT_PERIODIC    = 3

ACTION_DEF_FORMAT_NODE_LEVEL = 1
ACTION_DEF_FORMAT_CELL_LEVEL = 2

IND_HDR_FORMAT_1 = 1
IND_MSG_FORMAT_NODE_LEVEL = 1
IND_MSG_FORMAT_CELL_LEVEL = 2

# Indication reasons (§9.2.1.3.1)
IND_REASON_UPON_SUBSCRIPTION = "uponSubscription"
IND_REASON_UPON_CHANGE       = "uponChange"
IND_REASON_PERIODIC          = "periodic"

# Report types (§9.3.9)
REPORT_TYPE_ALL    = "all"
REPORT_TYPE_CHANGE = "change"

# Cell-level RAN Configuration Structure names (§8.2.2).
STRUCT_O_NRCELLDU = "O-NRCellDU"
STRUCT_O_NRCELLCU = "O-NRCellCU"
STRUCT_O_BWP      = "O-BWP"
