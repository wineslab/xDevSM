# Contributing

Thank you for considering contributing to xDevSM! Please follow these guidelines to help us maintain a welcoming and productive environment.
When contributing to this repository, please first discuss the change you wish to make via issue,
email, or any other method with the maintainers of this work.

Please note we have a code of conduct, please follow it in all your interactions with the project.

## Pull Request Process

1. Update `README.md` with details of changes to the interface — new public classes/methods,
   configuration, imports, or usage.
2. Increase the version number in the `VERSION` file to the new version that this Pull Request
   would represent. The versioning scheme we use is [SemVer](https://semver.org/).
   This library is consumed by the example/xApp repositories
   ([`xDevSM-xapps-examples`](https://github.com/wineslab/xDevSM-xapps-examples) and the
   internal `spectranet-xapps`); **we do not accept patches that break the public API those
   consumers rely on.**
3. Submitted code must have been tested and should work with the O-RAN SC Near-RT RIC
   configurations the framework supports.
4. Your branch must fast-forward onto `main`. Keep it a linear descendant of `main` (rebase onto
   the latest `main` whenever `main` moves) with no merge commits, so the exact commits reviewed
   in the Pull Request are the ones that land. Merges without prior approval are not allowed.
5. Every commit should stand on its own, installing and passing tests independently so
   `git bisect` stays usable. This is a review expectation, not a machine-enforced gate: CI
   installs and tests the Pull Request head, since a series that introduces or repairs the test
   suite partway through has earlier commits that legitimately cannot pass it. Fold
   "WIP"/"fixup" commits into coherent commits (`git rebase -i`) before review, and give each a
   descriptive message: an imperative subject line and, for non-trivial changes, a body
   explaining the *what* and *why*.

## Development Workflow

Active development happens on a **private internal repository** (`wineslab/xDevSM-dApp`). The
**public** repository **`wineslab/xDevSM`** is a 1:1 mirror of that internal repo, updated
automatically by `.github/workflows/mirror.yml` on every push to `main`, and it is what is
published to PyPI as [`xdevsm`](https://pypi.org/project/xdevsm/). **Do not open pull requests
against the public mirror — they will not be merged.**

### For maintainers and existing collaborators

Branch from the internal repository, open the PR there, follow the templates in `.github/`, and let CI run.

### For external contributors

External contributors must request access to the internal repository before opening a PR. Two channels are accepted:

1. **Preferred:** open an issue on the public mirror at https://github.com/wineslab/xDevSM/issues using the *"Request access to the internal development repository"* contact link (or any template with the `access-request` label). Tell us briefly what you want to work on.
2. **Fallback:** email **aferaudo34@gmail.com** with the same information.

Once access is granted, you will be invited to the internal repository; fork it from there, push your branch, and open the PR against the internal repo.

### Merging (maintainers)

Merges into `main` are fast-forward only, performed by a maintainer from the command line:

```
git fetch origin && git checkout main && git merge --ff-only <approved-branch> && git push origin main
```

Do not merge through the GitHub merge button: it would rewrite or add commits and would not preserve the exact reviewed commits. The `Commit policy` workflow posts the ready-to-run merge command when the PR is approved.

## Mandatory checks

The following are **mandatory** for every contribution. PRs that do not meet them will not be reviewed.

### Issues

- All issues must use one of the templates in `.github/ISSUE_TEMPLATE/` (`bug_report`, `feature_request`, `question`, `documentation`, or `new_sm`). Blank issues are disabled.
- Required fields in the templates must be completed; placeholder text is not acceptable.

### Pull requests

- All PRs must use `.github/PULL_REQUEST_TEMPLATE.md` and complete every checklist item.
- The following CI workflows must be green on the latest commit before review:
  - **`Unit Tests`** (`.github/workflows/tests.yml`) — installs the package via
    `pip install -e ".[dev]"` and runs `pytest tests/ -v` on the Python 3.11 / 3.12 matrix.
  - **`Commit policy`** (`.github/workflows/commit-trailers.yml`) — validates the AI-assistant
    trailer policy on every commit (see [AI assistants](#ai-assistants)), that the branch is a
    linear, fast-forward-able descendant of `main` (no merge commits), and that every commit
    installs and passes tests on its own.
- Build and test workflows do not run on documentation- or CI-only PRs; a `Detect code changes` job gates them (the trailer and linear-history checks still run on every PR).
- The following local checks must be reported in the PR description as run by the contributor (mirroring CI):
  - The branch is rebased on the latest `main`, `git log --merges origin/main..HEAD` is empty, and each commit installs and passes tests independently.
  - `pytest tests/ -v` passes (after `pip install -e ".[dev]"`).
  - `python -m build` succeeds (verifies packaging metadata and that the bundled `.so` encoders ship in the sdist).
  - `VERSION` bumped per [SemVer](https://semver.org/) when the public API changes.
  - `README.md` and/or `CONTRIBUTING.md` updated when contributor- or user-facing behavior changes.

### AI assistants

Contributions developed with the help of AI tools (LLM coding assistants, agents, and similar) are welcome, subject to the following **mandatory** rules, adapted from the Linux kernel and OpenAirInterface contribution guidelines.

- **AI agents must not add `Signed-off-by` or `Co-authored-by` trailers.** Those trailers certify human authorship and origin, which only a human contributor can provide; `Co-authored-by` is reserved for human collaborators.
- When an AI tool materially assisted a commit, disclose it with one `Assisted-by` trailer per tool. The value is free-form (any non-empty descriptor); both the compact `AGENT_NAME:MODEL_VERSION` form and the Linux-kernel `Name <email>` form are accepted, for example:

  ```
  Assisted-by: Claude:claude-opus-4-8
  Assisted-by: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
  ```
- The human submitter bears full responsibility for reviewing AI-generated code, for its correctness, and for its compatibility with this project's Apache-2.0 license.

These rules are enforced by the `Commit policy` workflow (`.github/workflows/commit-trailers.yml`), which fails any commit that attributes an AI agent through `Co-authored-by`/`Signed-off-by` or that carries an empty `Assisted-by` trailer. You can run the same check locally with `python3 scripts/check_commit_trailers.py --base origin/main --head HEAD`.

### Service Models and consumer coordination

xDevSM is consumed as a library by the example/xApp repositories
[`xDevSM-xapps-examples`](https://github.com/wineslab/xDevSM-xapps-examples) and the internal
`spectranet-xapps`. **We do not accept patches that break the public API or Service Model
behavior those consumers rely on.** PRs that change the public API or add a new Service Model
should come with a paired PR in the affected consumer repo when needed, linked from the PR
description.

## Code of Conduct

### Our Pledge

In the interest of fostering an open and welcoming environment, we as
contributors and maintainers pledge to making participation in our project and
our community a harassment-free experience for everyone, regardless of age, body
size, disability, ethnicity, gender identity and expression, level of experience,
nationality, personal appearance, race, religion, or sexual identity and
orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment
include:

* Using welcoming and inclusive language
* Being respectful of differing viewpoints and experiences
* Gracefully accepting constructive criticism
* Focusing on what is best for the community
* Showing empathy towards other community members

Examples of unacceptable behavior by participants include:

* The use of sexualized language or imagery and unwelcome sexual attention or
advances
* Trolling, insulting/derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information, such as a physical or electronic
  address, without explicit permission
* Other conduct which could reasonably be considered inappropriate in a
  professional setting

### Our Responsibilities

Project maintainers are responsible for clarifying the standards of acceptable
behavior and are expected to take appropriate and fair corrective action in
response to any instances of unacceptable behavior.

Project maintainers have the right and responsibility to remove, edit, or
reject comments, commits, code, wiki edits, issues, and other contributions
that are not aligned to this Code of Conduct, or to ban temporarily or
permanently any contributor for other behaviors that they deem inappropriate,
threatening, offensive, or harmful.

### Scope

This Code of Conduct applies both within project spaces and in public spaces
when an individual is representing the project or its community. Examples of
representing a project or community include using an official project e-mail
address, posting via an official social media account, or acting as an appointed
representative at an online or offline event. Representation of a project may be
further defined and clarified by project maintainers.

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported by contacting the project team. All
complaints will be reviewed and investigated and will result in a response that
is deemed necessary and appropriate to the circumstances. The project team is
obligated to maintain confidentiality with regard to the reporter of an incident.
Further details of specific enforcement policies may be posted separately.

Project maintainers who do not follow or enforce the Code of Conduct in good
faith may face temporary or permanent repercussions as determined by other
members of the project's leadership.

### Attribution

This Code of Conduct is adapted from the [Contributor Covenant][homepage], version 1.4,
available at [http://contributor-covenant.org/version/1/4][version]

[homepage]: http://contributor-covenant.org
[version]: http://contributor-covenant.org/version/1/4/
