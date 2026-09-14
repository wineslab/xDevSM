"""Patches xDevSM needs applied to its installed ricxappframe.

ricxappframe is a runtime dependency, not a vendored one, so anything xDevSM
needs from it that upstream does not provide has to be applied to the installed
copy at image-build time. Keeping the patches here rather than in an xApp's
Dockerfile means they version with the code that depends on them, and ship in
the wheel, so every image builder gets the same set.

Apply with::

    python -m xdevsm.ricxappframe_patches

See README.md for what each patch does and how to regenerate one.
"""

RICXAPPFRAME_VERSION = "3.2.2"
