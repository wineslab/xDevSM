#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Enforce libe3's AI-assistant commit-trailer policy (see CONTRIBUTING.md).

For every commit in the checked range, this fails if:
  * a `Co-authored-by` or `Signed-off-by` trailer attributes an AI agent
    (only humans may certify authorship/origin), or
  * an `Assisted-by` trailer is empty.

The `Assisted-by` value is free-form: any non-empty descriptor is accepted,
e.g. `Assisted-by: Claude:claude-opus-4-8` or
`Assisted-by: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

Usage:
  check_commit_trailers.py --base <base-sha> --head <head-sha>
  check_commit_trailers.py <sha> [<sha> ...]
"""
import argparse
import re
import subprocess
import sys

# Substrings that identify an AI agent when they appear in an attribution
# trailer's value. Matched case-insensitively against Co-authored-by /
# Signed-off-by values only, so the false-positive risk is minimal.
AI_KEYWORDS = (
    "claude", "anthropic", "copilot", "gpt", "chatgpt", "openai", "gemini",
    "bard", "llama", "mistral", "cursor", "codeium", "aider", "swe-agent",
    "ai assistant", "language model",
)

ATTRIBUTION = re.compile(r"^\s*(co-authored-by|signed-off-by)\s*:\s*(.+?)\s*$", re.IGNORECASE)
ASSISTED = re.compile(r"^\s*assisted-by\s*:\s*(.+?)\s*$", re.IGNORECASE)


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def commit_message(sha: str) -> str:
    return _git("log", "-1", "--format=%B", sha)


def resolve_range(base: str, head: str) -> list[str]:
    """Commits in base..head, falling back to just head for new/force-pushed refs."""
    if base and set(base) != {"0"}:
        try:
            out = _git("rev-list", f"{base}..{head}")
            return [line for line in out.split() if line]
        except subprocess.CalledProcessError:
            pass
    return [_git("rev-parse", head).strip()]


def check_commit(sha: str) -> list[str]:
    problems: list[str] = []
    for line in commit_message(sha).splitlines():
        attr = ATTRIBUTION.match(line)
        if attr:
            trailer, value = attr.group(1), attr.group(2)
            if any(k in value.lower() for k in AI_KEYWORDS):
                problems.append(
                    f"AI agent attributed via '{trailer}': {line.strip()!r}. "
                    f"Use an 'Assisted-by:' trailer instead."
                )
        assisted = ASSISTED.match(line)
        if assisted:
            # Free-form value; only reject an empty one. Both
            # `AGENT_NAME:MODEL_VERSION` and the kernel `Name <email>` form pass.
            if not assisted.group(1).strip():
                problems.append(
                    f"Empty Assisted-by trailer: {line.strip()!r}. "
                    f"Provide a non-empty agent descriptor."
                )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="base commit (exclusive)")
    parser.add_argument("--head", help="head commit (inclusive)")
    parser.add_argument("shas", nargs="*", help="explicit commits to check")
    args = parser.parse_args()

    if args.shas:
        shas = args.shas
    elif args.head:
        shas = resolve_range(args.base or "", args.head)
    else:
        parser.error("provide either commit SHAs or --head [--base]")

    failed = False
    for sha in shas:
        subject = (commit_message(sha).splitlines() or [""])[0]
        problems = check_commit(sha)
        if problems:
            failed = True
            print(f"::error::commit {sha[:12]} ({subject}) violates the AI-trailer policy:")
            for problem in problems:
                print(f"  - {problem}")
        else:
            print(f"ok: {sha[:12]} ({subject})")

    if failed:
        print("\nSee the 'AI assistants' section of CONTRIBUTING.md.")
        return 1
    print(f"\nAll {len(shas)} checked commit(s) comply with the AI-trailer policy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
