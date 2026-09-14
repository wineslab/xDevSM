"""Apply this package's patches to the installed ricxappframe.

Run once at image build time, after ricxappframe is installed::

    python -m xdevsm.ricxappframe_patches

Idempotent: a patch already applied is reported and skipped, so re-running
during an incremental build is harmless. Everything else is fatal -- a patch
that does not apply means the installed ricxappframe is not the one these were
generated against, and continuing would produce an image whose behaviour
silently differs from what the framework expects.
"""
import argparse
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

from xdevsm.ricxappframe_patches import RICXAPPFRAME_VERSION

PATCH_DIR = Path(__file__).resolve().parent


def _installed_version():
    try:
        from importlib.metadata import version
        return version("ricxappframe")
    except Exception:
        return None


def _run(patch, target, extra):
    return subprocess.run(
        ["patch", "-p1", "-d", str(target), *extra, "-i", str(patch)],
        capture_output=True, text=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--target", default=sysconfig.get_paths()["purelib"],
                    help="site-packages directory holding ricxappframe "
                         "(default: this interpreter's purelib)")
    ap.add_argument("--check", action="store_true",
                    help="dry run: report what would be applied, change nothing")
    ap.add_argument("--allow-version-mismatch", action="store_true",
                    help="patch even if the installed ricxappframe is not the "
                         "pinned version (for testing a bump)")
    args = ap.parse_args(argv)

    if shutil.which("patch") is None:
        print("the `patch` binary is not installed; add it to the image "
              "(apt-get install patch)", file=sys.stderr)
        return 1

    target = Path(args.target)
    if not (target / "ricxappframe").is_dir():
        print("ricxappframe not found under {}".format(target), file=sys.stderr)
        return 1

    found = _installed_version()
    if found != RICXAPPFRAME_VERSION:
        msg = ("ricxappframe is {}, these patches were generated against {}"
               .format(found, RICXAPPFRAME_VERSION))
        if not args.allow_version_mismatch:
            print(msg + "; refusing. Regenerate the patches, then bump "
                        "RICXAPPFRAME_VERSION.", file=sys.stderr)
            return 1
        print("warning: " + msg, file=sys.stderr)

    patches = sorted(PATCH_DIR.glob("*.patch"))
    if not patches:
        print("no patches found in {}".format(PATCH_DIR), file=sys.stderr)
        return 1

    failed = 0
    for patch in patches:
        # --reverse --dry-run succeeds exactly when the patch is already in.
        if _run(patch, target, ["--reverse", "--dry-run", "--force"]).returncode == 0:
            print("already applied: {}".format(patch.name))
            continue
        probe = _run(patch, target, ["--dry-run", "--forward"])
        if probe.returncode != 0:
            print("WOULD FAIL: {}\n{}".format(patch.name, probe.stdout or probe.stderr),
                  file=sys.stderr)
            failed += 1
            continue
        if args.check:
            print("would apply: {}".format(patch.name))
            continue
        applied = _run(patch, target, ["--forward", "--silent"])
        if applied.returncode != 0:
            print("FAILED: {}\n{}".format(patch.name, applied.stdout or applied.stderr),
                  file=sys.stderr)
            failed += 1
            continue
        print("applied: {}".format(patch.name))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
