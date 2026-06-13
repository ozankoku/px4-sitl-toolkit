# Maintainer Automation Plan

This repository is being prepared for sustainable open-source maintenance around repeatable PX4 SITL scenarios.

## Current automation

- GitHub Actions CI for Python 3.9, 3.10, and 3.11
- Ruff linting
- Pytest regression tests
- Example scenario validation in CI
- Issue templates for beginner tasks and scenario requests
- Pull request template with explicit test plan

## Planned automation

- Scenario-manifest compatibility checks for future schema versions
- Automated release notes from merged pull requests
- Bot-assisted issue triage for scenario requests, docs requests, and bug reports
- PR review support for tests, CLI behavior, and docs consistency
- Security review support for command-generation and manifest-loading changes

## Intended Codex/API use

If accepted into OpenAI's Codex for Open Source program, API credits would be used only for this repository and related open-source maintainer work:

- Drafting first-pass PR reviews
- Summarizing and labeling issues
- Generating regression tests for new scenario types
- Checking docs against CLI behavior
- Producing release notes and migration notes
- Reviewing manifest parsing and command-generation changes for security issues
