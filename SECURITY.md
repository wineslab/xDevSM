# Security Policy

## Reporting a vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Email the maintainer directly at **aferaudo34@gmail.com** with the subject prefix `[SECURITY]`. Include:

- A description of the vulnerability and its impact.
- Steps to reproduce (commands, configuration, sample inputs).
- The version / commit you tested against.
- Any suggested mitigation, if you have one.

You may use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) on the public mirror (`wineslab/xDevSM`) as an alternative.

## Supported versions

This is a research library. Only the latest minor release on `main` is actively supported with security fixes.

| Version | Supported |
| ------- | --------- |
| Latest `main` | Yes |
| Older releases | No (please upgrade) |

## Response expectations

- We aim to acknowledge reports within **7 calendar days**.
- Critical issues are targeted for a fix within **30 days** of acknowledgement; lower-severity issues are scheduled with the reporter.
- Disclosure is coordinated with the reporter. Reporters are credited in release notes unless they request otherwise.

## Scope

In scope: code under this repository, its build/release pipeline, the bundled `sm_framework` encoders, and its packaging on PyPI (`xdevsm`).

Out of scope: third-party dependencies (please report to the upstream project, e.g. `ricxappframe` or the O-RAN SC Near-RT RIC), infrastructure outside this repo, and issues that require attacker-controlled access to a host already running the xApp.
