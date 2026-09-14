# ricxappframe patches

`ricxappframe` is a runtime dependency of xDevSM, not a vendored one. Anything
xDevSM needs from it that upstream does not provide has to be applied to the
**installed** copy, at image-build time.

These live here, rather than in an xApp's Dockerfile, for three reasons: they
version with the code that depends on them, they ship in the wheel so every
image builder gets the same set, and the dependency becomes visible from
xDevSM's side instead of being an undeclared assumption about how the image was
built.

## Applying

```sh
python -m xdevsm.ricxappframe_patches            # apply
python -m xdevsm.ricxappframe_patches --check    # dry run
```

Requires the `patch` binary. Idempotent — an already-applied patch is detected
and skipped. Any patch that does not apply is fatal: it means the installed
`ricxappframe` is not the version these were generated against, and continuing
would build an image whose behaviour silently differs from what the framework
expects.

Pinned to `ricxappframe == 3.2.2` (`RICXAPPFRAME_VERSION` in `__init__.py`).

## The patches

### 001-enable-indication-msg-free.patch

Upstream ships `_asn1_free_indicationMsg(indication)` commented out in
`IndicationMsg.decode()`, so the C-side decoded PDU is never released — a leak
on every received indication. The line is re-enabled.

Previously applied by a `sed` in the xApp Dockerfile. Moved here so it is not
lost by an image built from a different Dockerfile, and so it fails loudly
rather than silently matching nothing if upstream reformats.

### 002-add-control-ack-decode.patch

Adds `ControlAckMsg` to `ricxappframe.e2ap.asn1` and `control_ack_msg_t` to
`ricxappframe.e2ap.asn1clib.types`, binding two symbols that
`libriclibe2ap.so` already exports but upstream never wraps:

- `e2ap_decode_ric_control_acknowledge_message`
- `e2ap_free_decoded_ric_control_ack`

Upstream already wraps the *request* encoder
(`e2ap_encode_ric_control_request_message`, `ControlRequestMsg`); this is the
missing other half, so an xApp that sets `control_ack_request=1` can read the
answer. The E2AP layer only carries the Service Model's octets, so
`control_outcome` is opaque here and is decoded by whichever Service Model
issued the request.

No new shared library is involved: `libriclibe2ap.so` is the same object
`ricxappframe` already loads in `asn1clib.py`, and these symbols resolve
through its existing handle.

## Regenerating a patch

```sh
pip download --no-deps --no-binary :all: ricxappframe==3.2.2
# unpack to orig/, copy to new/, edit new/, then:
diff -ur orig new > NNN-name.patch
```

Paths in the patch are relative to the site-packages root (`-p1` strips the
leading `a/` and `b/`), i.e. they start `ricxappframe/...`.
