# xDevSM

## Overview

The xDevSM API framework provides xApp developers with a SDK exposing simple APIs to streamline the procedures defined by different E2SM protocols, facilitating interactions between the xApp, the near-RT RIC, and the E2 termination on the RAN.
It wraps and orchestrates message encoding/decoding, RMR-based communication, and SM-specific behavior. Internally, it delegates encoding and decoding tasks to the `sm_framework`, which defines the core logic for each Service Model (KPM and RC).

xDevSM is built on top of [ricxappframe](https://pypi.org/project/ricxappframe/) python framework.

The architecture separates three main layers:

1. **xApp API Layer** — developer-facing classes (`BasexDevSMXapp`, `xDevSMRMRXapp`, wrappers).
2. **Service Model Wrappers** — expose KPM and RC functionalities.
3. **sm_framework** — performs actual encoding/decoding (internal).

> ⚠️ The xDevSM framework is designed to operate exclusively with the O-RAN Software Community (OSC) Near-RT RIC. </br> ℹ️ The current version has been tested with the OSC RIC Release J.

### Supported Service Model Actions
| **Service Model** | **Action Type** | **Supported Actions** |
|-----------------------|--------------------|---------------------------|
| **KPM (Key Performance Measurement)** | Measurement Actions | • Common Condition-based Measurement, UE-level Measurement |
| **RC (RAN Control)** | Control Actions | • QoS Flow Mapping Configuration<br>• Slice-level PRB Quota Action<br>• Connected Mode Mobility Control |
---

## Class Hierarchy

```

BasexDevSMXapp
    └── xDevSMRMRXapp
    └── BaseXDevSMWrapper
        ├── XappKpmFrame
        └── RCControlBase
                ├── RadioBearerControl
                ├── RadioResourceAllocationControl
                └── ConnectedModeMobilityControl
```

> ℹ️ A detailed diagram is available [here](xDevSMClassDiagram.png).

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
This class is not used directly but extended by SM-specific wrappers like `XappKpmFrame` and `RCControlBase` providing the actual APIs.

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
## 6. RCControlBase

**Purpose:**
Provides the base class for the **Radio Control (RC)** Service Model. Defines shared functionality across different RC control operations.

**Common Responsibilities:**

* Initialize and validate RC messages.
* Interface with `sm_framework` for encoding and decoding.
* Offer helper methods for constructing Control Requests.

**Specializations:**

| Subclass - Style                   | Description                                               | Control Action Id Support                                |
| ---------------------------------- | --------------------------------------------------------- |--------------------------------------------------------- |
| `RadioBearerControl` - 1           | Handles bearer-level control (QoS, bearer setup/release). | (2) QoS flow mapping configuration                       |
| `RadioResourceAllocationControl`- 2| Manages resource allocation (e.g., PRB or scheduling).    | (6) Slice-level PRB quota                                |
| `ConnectedModeMobilityControl` - 3 | Manages handover and mobility-related control procedures. | (1) Handover control  ⚠️                                 |

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
                                mrc=xapp_gen._mrc,
                                http_port=xapp_gen.http_port,
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
                                        mrc=xapp_gen._mrc,
                                        http_port=xapp_gen.http_port,
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

**Example: Connected Mode Mobility Control - ⚠️needs to be tested**
```python
xapp_gen = xDevSMRMRXapp("0.0.0.0")
rc_xapp = ConnectedModeMobilityControl(xapp_gen,
                                        logger=logger,
                                        server=xapp_gen.server,
                                        xapp_name=xapp_gen.get_xapp_name(),
                                        rmr_port=xapp_gen.rmr_port,
                                        mrc=xapp_gen._mrc,
                                        http_port=xapp_gen.http_port,
                                        pltnamespace=xapp_gen.get_pltnamespace(),
                                        app_namespace=xapp_gen.get_app_namespace(),
                                        # control parameters
                                        plmn_identity="00F110",
                                        nr_cell_id="00000000000000000000111000000001"
                                        )
```


---

## 7. Service Model Encoder/Decoder

The `sm_framework` provides the internal logic for encoding and decoding messages according to the KPM and RC Service Models. The external APIs (`XappKpmFrame`, `RCControlBase`, etc.) rely on these internal classes to translate between Python objects and binary payloads.

```
[ xApp code ] → [ xDevSM API ] → [ sm_framework (encode/decode) ] → [ E2AP + RMR ]
```

Developers using `xDevSM` do not directly call `sm_framework`; it is fully managed by the wrapper classes.

---

## 8. Example xApps

For end-to-end examples of KPM and RC xApps built on top of this API, see:

**[xDevSM-xapps-examples](https://github.com/wineslab/xDevSM-xapps-examples/tree/code_refactoring)**

This repository contains working implementations that demonstrate:

* How to set-up an xApp based on xDevSM.
* Registration of handlers.
* Sending and receiving encoded Service Model messages.

---

## 9. Extending the API

To support a new Service Model (E2SM):

1. Implement the encoder/decoder in `sm_framework/<new_sm>/`.
2. Create a new wrapper subclass (e.g., `XappNewSMFrame`) extending `BaseXDevSMWrapper`.
3. Implement SM-specific methods (e.g., `send_<msg>()`, `handle_<msg>()`).
4. Register handlers for the new message types in your xApp.

---

## 10. Other Sources

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
