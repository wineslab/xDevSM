<!--
Thank you for contributing to xDevSM. Please fill in every section.
PRs that leave the mandatory boxes unchecked will not be reviewed.
-->

## Summary

<!-- 1–3 bullets describing what this PR changes and *why*. -->

-
-

## Type of change

- [ ] Bug fix
- [ ] New feature / enhancement
- [ ] New Service Model (E2SM wrapper)
- [ ] Refactor (no behavior change)
- [ ] Documentation
- [ ] Test / CI / packaging
- [ ] Other (explain):

## Linked issue

<!-- Required. Use "Closes #N" so the issue is auto-closed on merge. -->

Closes #

## Mandatory test checklist

These mirror what CI (`.github/workflows/tests.yml`) enforces. **All boxes must be ticked before review.**

- [ ] `pytest tests/ -v` passes locally (after `pip install -e ".[dev]"`)
- [ ] `python -m build` succeeds (verifies packaging metadata and that the bundled `.so` encoders ship)
- [ ] `VERSION` file bumped per [SemVer](https://semver.org/) if the public API changed
- [ ] `README.md` updated if the interface, imports, or workflow changed
- [ ] `CONTRIBUTING.md` updated if contributor-facing rules changed
- [ ] If new dependencies were added, they appear in `pyproject.toml`

## CI checklist

- [ ] `Unit Tests` workflow is green (Python 3.11 / 3.12 matrix on `ubuntu-latest`)
- [ ] `Commit policy` workflow is green (trailers + linear history + each commit installs/tests independently)

## Consumer coordination

xDevSM is consumed as a library by the example/xApp repositories
[`xDevSM-xapps-examples`](https://github.com/wineslab/xDevSM-xapps-examples) and the internal
`spectranet-xapps`. **We do not accept patches that break the public API relied on by those consumers.**

- [ ] This PR does not change the public API / Service Model behavior, OR a paired PR exists in the affected consumer repo (link below).

Paired PR(s):

## Workflow confirmation

- [ ] This PR was opened against the **internal** repository (private `wineslab/xDevSM-dApp`). The public mirror `wineslab/xDevSM` is updated automatically by `.github/workflows/mirror.yml`.
- [ ] My branch is a linear, fast-forward-able descendant of `main` (rebased if `main` moved), with no merge commits. (See `CONTRIBUTING.md` § Pull Request Process.)
- [ ] Every commit installs and passes tests on its own (atomic, `git bisect`-safe) with a descriptive message.
- [ ] I have read and followed `CONTRIBUTING.md`.
