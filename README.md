# xDevSM

[![PyPI](https://img.shields.io/pypi/v/xdevsm.svg)](https://pypi.org/project/xdevsm/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

## Overview

The xDevSM API framework provides xApp developers with a SDK exposing simple APIs to streamline the procedures defined by different E2SM protocols, facilitating interactions between the xApp, the near-RT RIC, and the E2 termination on the RAN.
It wraps and orchestrates message encoding/decoding, RMR-based communication, and SM-specific behavior. Internally, it delegates encoding and decoding tasks to the `sm_framework`, which defines the core logic for each Service Model (KPM, RC, and CCC).

xDevSM is built on top of [ricxappframe](https://pypi.org/project/ricxappframe/) python framework.

The architecture separates three main layers:

1. **xApp API Layer** — developer-facing classes (`BasexDevSMXapp`, `xDevSMRMRXapp`, wrappers).
2. **Service Model Wrappers** — expose KPM, RC, and CCC functionalities.
3. **sm_framework** — performs actual encoding/decoding (internal).

> ⚠️ The xDevSM framework is designed to operate exclusively with the O-RAN Software Community (OSC) Near-RT RIC. </br> ℹ️ The current version has been tested with the OSC RIC Release J.

### Supported Service Model Actions
| **Service Model** | **Action Type** | **Supported Actions** |
|-----------------------|--------------------|---------------------------|
| **KPM (Key Performance Measurement)** | Measurement Actions | • Common Condition-based Measurement, UE-level Measurement |
| **RC (RAN Control)** | Control Actions | • QoS Flow Mapping Configuration<br>• Slice-level PRB Quota Action (only monolithic gNBs)<br>• Connected Mode Mobility Control |
| **CCC (Cell Configuration and Control)** | Report Actions | • Cell-level RAN Configuration Reporting (REPORT Style 2, periodic event trigger) — e.g. `O-NRCellDU` attributes |
---

## Installation

xDevSM is distributed as the [`xdevsm`](https://pypi.org/project/xdevsm/) package on PyPI:

```bash
pip install xdevsm
```

> ℹ️ The package bundles the prebuilt `sm_framework` encoders (`.so`) as package data and is
> published as a source distribution, so a **linux-x86_64** environment and **Python 3.11**
> are required (matching the O-RAN SC Near-RT RIC deployment target). Python 3.12+ is not
> supported: `ricxappframe` depends on `ricsdl`, which pins `hiredis==2.0.0`, and that
> version cannot be built on 3.12 or later.
>
> No `LD_LIBRARY_PATH` setup is needed — the bundled encoders are loaded relative to the
> installed package. A **C compiler is required**, though: `hiredis==2.0.0` ships no wheel for
> 3.11, so pip builds it from source. Slim base images therefore need `gcc` installed (the
> full `python:3.11-bullseye` image already has it).

For local development (tests, editable install):

```bash
git clone https://github.com/wineslab/xDevSM.git
cd xDevSM
pip install -e ".[dev]"
pytest tests/ -v
```

### Importing

Everything lives under the top-level `xdevsm` package. The developer-facing classes are also
re-exported from the package root for convenience:

```python
# Convenience (recommended)
from xdevsm import xDevSMRMRXapp, XappKpmFrame, XappCccFrame, RadioBearerControl

# Or import from the fully-qualified submodules
from xdevsm.handlers.xDevSM_rmr_xapp import xDevSMRMRXapp
from xdevsm.decorators.kpm.kpm_frame import XappKpmFrame
from xdevsm.decorators.ccc.ccc_frame import XappCccFrame
```

---

## Class Hierarchy

```

BasexDevSMXapp
    └── xDevSMRMRXapp
    └── BaseXDevSMWrapper
        ├── xAppReportService
        │   ├── XappKpmFrame
        │   └── XappCccFrame
        └── xAppControlService
                ├── RadioBearerControl
                ├── RadioResourceAllocationControl
                └── ConnectedModeMobilityControl
```

> ℹ️ A detailed diagram is available [here](xdevsmclassdiagram.pdf).

---

## 1. BasexDevSMXapp
Defines the core xApp interface that integrates xDevSM functionality with RMR. Provides the fundamental methods used by all xDevSM-based xApps.

Base class implementing the RMR communication layer. It provides generic `send()`, `receive()`, and `terminate()` methods for message passing between xApps and the Near-RT RIC.

| Method                           | Description                                                                       |
| -------------------------------- | --------------------------------------------------------------------------------- |
| `handle(xapp, summary, sbuf)`                       | Method called by the `ricxappframe`. Entry point for processing received messages (`Indication` and `RIC CONTROL ` Messages`). Should be overridden by subclasses. |
| `send(self, *args, **kwargs)`  | Sends a message via RMR after encoding. Input depends on the underlying E2SM.                                           |
| `terminate()`                    | Gracefully stops the xApp.                                 |
| `get_ran_function_description(json_ran_info)` | Uses the `sm_framework` to decode the RAN function description depending on the SM.                    |

---

## 3. xDevSMRMRXapp

**Purpose:**
Extends `BasexDevSMXapp` to provide additional functionality specific to the xDevSM architecture.

**Key Methods:**

| Method                                | Description                                                                    |
| ------------------------------------- | ------------------------------------------------------------------------------ |
| `register_handler(handler)` | Registers callback handlers.                        |
| `register_shutdown(handler)`          | Registers a shutdown handler for cleanup tasks.                                |
| `get_ran_info()`                      | Returns E2 node-related encoded information. |

This class is used as the base class for wrapper components.

---

## 4. BaseXDevSMWrapper

**Purpose:**
Provides a composition interface that connects Service Model–specific APIs (KPM, RC, etc.) with an instance of `xDevSMRMRXapp`. This allows to decorate the xApp with Service Model realted behavior.

**Attributes:**

* `xapp_handler` — instance of `BasexDevSMXapp`.

**Usage:**
This class is not used directly but extended by RIC service bases (`xAppReportService`, `xAppControlService`) and then by Service Model–specific decorators (e.g. `XappKpmFrame`, `RadioResourceAllocationControl`) that expose the actual APIs.

---

## 5. XappKpmFrame

**Purpose:**
Implements the external API for the **Key Performance Measurement (KPM)** Service Model.

Internally, it uses encoding and decoding classes from the `sm_framework` to handle message serialization before E2AP wrapping and RMR transmission.

**Common Operations:**

* Encode KPM Subscription Requests.
* Decode and Parse received KPM Indications.

**Example:**

```python
xapp_gen = xDevSMRMRXapp(...)
kpm_api = XappKpmFrame(xapp_handler)
kpm_api.subscribe(gnb=self.selected_gnb, 
                ev_trigger=ev_trigger_tuple, 
                func_def=func_def_sub_dict, 
                ran_period_ms=1000, 
                sst=self.sst, sd=
                self.sd)
```


---

## 6. XappCccFrame

**Purpose:**
Implements the external API for the **Cell Configuration and Control (CCC)** Service Model (`ORAN-E2SM-CCC`, RAN Function OID `1.3.6.1.4.1.53148.1.1.2.4`, SM ID `149`). Like `XappKpmFrame`, it is a **REPORT**-type decorator and extends `xAppReportService`, mirroring the KPM lifecycle (subscribe → indication decode → callback).

Unlike KPM and RC, E2SM-CCC uses a **JSON** wire encoding rather than ASN.1, so the CCC encoders/decoders in `sm_framework/py_oran/ccc/` are pure-Python and never cross into the native `.so` libraries.

**Common Operations:**

* Encode CCC Subscription Requests — periodic Event Trigger (Format 3) + cell-level Action Definition (Format 2, REPORT Style 2).
* Decode and parse received CCC Indications via `CccIndicationHeader` / `CccIndicationMessage`.

**Supported REPORT style:**

| Style | Description |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| REPORT Style 2 — Cell Level  | Reports RAN Configuration Structures (e.g. `O-NRCellDU`) and a selected set of attributes (`arfcnDL`, `bSChannelBwDL`, `bWPList`, …) per cell. |

**Example:**

```python
xapp_gen = xDevSMRMRXapp("0.0.0.0", route_file=args.route_file)

ccc_xapp = XappCccFrame(xapp_gen,
                        logger=xapp_gen.logger,
                        server=xapp_gen.server,
                        xapp_name=xapp_gen.get_xapp_name(),
                        rmr_port=xapp_gen.rmr_port,
                        http_port=xapp_gen.http_port,
                        pltnamespace=xapp_gen.get_pltnamespace(),
                        app_namespace=xapp_gen.get_app_namespace())

# Wire callbacks
xapp_gen.register_handler(ccc_xapp.handle)
ccc_xapp.register_ind_msg_callback(handler=indication_callback)   # (hdr, msg, meid, sub_id)
ccc_xapp.register_sub_fail_callback(handler=sub_failed_callback)

# Subscribe to a periodic cell-level REPORT on O-NRCellDU
ccc_xapp.subscribe(gnb=selected_gnb,
                   ran_period_ms=1000,
                   ran_cfg_structure_name="O-NRCellDU",
                   attributes=["arfcnDL", "bSChannelBwDL", "bWPList"])

# or the one-call helper for those three target attributes:
ccc_xapp.subscribe_arfcn_bw_bwps(gnb=selected_gnb, ran_period_ms=1000)
```

> ℹ️ The indication callback signature is `handler(ind_hdr, ind_msg, meid, sub_id)`. Iterate the reported cells/structures with `ind_msg.cells()` / `ind_msg.iter_structures()`.

---
## 7. xAppReportService

**Purpose:**
Provides the base class for **Report-type** Service Models. Handles subscription management, indication message routing, and decoding.

**Common Responsibilities:**

* Build and send E2 subscription requests.
* Route incoming indication messages to registered callbacks.
* Interface with `sm_framework` for decoding RAN function descriptions.

**Specializations:**

| Subclass        | Description                                         |
| --------------- | --------------------------------------------------- |
| `XappKpmFrame`  | Implements KPM-specific subscription and indication handling. |
| `XappCccFrame`  | Implements CCC-specific (Cell Configuration and Control) subscription and indication handling over a JSON encoding. |

---

## 8. xAppControlService

**Purpose:**
Provides the base class for the **Radio Control (RC)** Service Model. Defines shared functionality across different RC control operations.

**Common Responsibilities:**

* Initialize and validate RC messages.
* Interface with `sm_framework` for encoding and decoding.
* Offer helper methods for constructing Control Requests.
* Handle RIC Control Acknowledge and Failure messages.

**Specializations:**

| Subclass - Style                    | Description                                               | Control Action Id Support              |
| ----------------------------------- | --------------------------------------------------------- | -------------------------------------- |
| `RadioBearerControl` - 1            | Handles bearer-level control (QoS, bearer setup/release). | (2) QoS flow mapping configuration     |
| `RadioResourceAllocationControl` - 2| Manages resource allocation (e.g., PRB or scheduling).    | (6) Slice-level PRB quota              |
| `ConnectedModeMobilityControl` - 3  | Manages handover and mobility-related control procedures. | (1) Handover control                   |

Each subclass defines Service Model–specific operations and message structures, invoking the appropriate encoder/decoder from `sm_framework.rc`.

> ℹ️ Control parameters can be modified using getter and setter methods.

**Example: Radio Bearer Control Initialization**

```python
xapp_gen = xDevSMRMRXapp("0.0.0.0", route_file=args.route_file)

rc_xapp = RadioBearerControl(xapp_gen,
                                logger=logger,
                                server=xapp_gen.server,
                                xapp_name=xapp_gen.get_xapp_name(),
                                rmr_port=xapp_gen.rmr_port,
                                http_port=xapp_gen.http_port,
                                mrc=xapp_gen._mrc,
                                pltnamespace=xapp_gen.get_pltnamespace(),
                                app_namespace=xapp_gen.get_app_namespace(),
                                # control parameters
                                drb_id=args.drb_id,
                                qos_flow_id=args.qos_flow_id,
                                qos_flow_mapping_indication=args.qos_flow_mapping_indication
                                )
```

**Example: Radio Resource Allocation Control**
```python
xapp_gen = xDevSMRMRXapp("0.0.0.0")
rc_xapp = RadioResourceAllocationControl(xapp_gen,
                                        logger=logger,
                                        server=xapp_gen.server,
                                        xapp_name=xapp_gen.get_xapp_name(),
                                        rmr_port=xapp_gen.rmr_port,
                                        http_port=xapp_gen.http_port,
                                        mrc=xapp_gen._mrc,
                                        pltnamespace=xapp_gen.get_pltnamespace(),
                                        app_namespace=xapp_gen.get_app_namespace(),
                                        # control parameters
                                        plmn_identity="00F110",
                                        sst=1,
                                        sd=1,
                                        min_prb_policy_ratio=10,
                                        max_prb_policy_ratio=70,
                                        dedicated_prb_policy_ratio=5
                                        )
```

**Example: Connected Mode Mobility Control**
```python
xapp_gen = xDevSMRMRXapp("0.0.0.0")
rc_xapp = ConnectedModeMobilityControl(xapp_gen,
                                        logger=logger,
                                        server=xapp_gen.server,
                                        xapp_name=xapp_gen.get_xapp_name(),
                                        rmr_port=xapp_gen.rmr_port,
                                        http_port=xapp_gen.http_port,
                                        mrc=xapp_gen._mrc,
                                        pltnamespace=xapp_gen.get_pltnamespace(),
                                        app_namespace=xapp_gen.get_app_namespace(),
                                        # control parameters
                                        plmn_identity="00F110",
                                        nr_cell_id="00000000000000000000111000000001"
                                        )
```


---

## 9. Service Model Encoder/Decoder

The `sm_framework` provides the internal logic for encoding and decoding messages according to the KPM, RC, and CCC Service Models. The xDevSM decorators are organized by RIC service direction: `xAppReportService` and `xAppControlService` are the generic bases for report- and control-style services, and any service model (KPM, RC, CCC, ...) plugs in by extending the appropriate base — for example `XappKpmFrame` and `XappCccFrame` extend `xAppReportService`, and `RadioResourceAllocationControl` extends `xAppControlService`.

> ℹ️ KPM and RC serialize through ctypes bindings to the native `.so` libraries, whereas CCC (E2SM-CCC) uses a pure-Python **JSON** codec in `sm_framework/py_oran/ccc/`.

```
[ xApp code ] → [ xDevSM API ] → [ sm_framework (encode/decode) ] → [ E2AP + RMR ]
```

Developers using `xDevSM` do not directly call `sm_framework`; it is fully managed by the wrapper classes.

---

## 10. Example xApps

For end-to-end examples of KPM, RC, and CCC xApps built on top of this API, see:

**[xDevSM-xapps-examples](https://github.com/wineslab/xDevSM-xapps-examples/tree/code_refactoring)**

This repository contains working implementations that demonstrate:

* How to set-up an xApp based on xDevSM.
* Registration of handlers.
* Sending and receiving encoded Service Model messages.

The **CCC basic xApp** (`ccc_xapp.py`) is a minimal reference: it subscribes to a periodic O-NRCellDU REPORT (Style 2 / Event Trigger Format 3) and pretty-prints every incoming indication (cell identity, frequencies, SSB, BWP list, …).

---

## 11. Extending the API

To support a new Service Model (E2SM):

1. Implement the encoder/decoder in `sm_framework/<new_sm>/`.
2. Create a new wrapper subclass (e.g., `XappNewSMFrame`) extending `BaseXDevSMWrapper`.
3. Implement SM-specific methods (e.g., `send_<msg>()`, `handle_<msg>()`).
4. Register handlers for the new message types in your xApp.

---

## 12. Other Sources

A detailed step-by-step tutorial for setting up a deployment to begin working with xDevSM is available [here](https://openrangym.com/tutorials/xdevsm-tutorial).

## How To Cite
If you use xDevSM, please reference the following paper:
> A.Feraudo, S. Maxenti, A. Lacava, P. Bellavista, M. Polese, and T. Melodia, <i>"xDevSM: Streamlining xApp Development With a Flexible Framework for O-RAN E2 Service Models,"
> </i> Proceedings of the 18th ACM Workshop on Wireless Network Testbeds, Experimental evaluation & Characterization (WiNTECH), November, 2024.
> </a> <a href="https://ece.northeastern.edu/wineslab/wines_bibtex/feraudo2024xDevSM.txt" target="_blank">[bibtex]</a>

## License
This project is licensed under Apache License Version 2.0 - see [License File](LICENSE) for more details.

## Organizations
| <img src="https://github.com/wineslab.png?s=100" width="60" height="60"> | [**Wireless Networks and Embedded Systems Lab**](https://github.com/wineslab) |
| :--: | :--: |
| <img src="https://github.com/MMw-Unibo.png?s=100" width="60" height="60"> | [**Mobile Middleware Research Group**](https://github.com/MMw-Unibo) |
