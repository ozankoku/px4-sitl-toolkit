# Changelog

All notable changes to this project will be documented in this file.

The format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses semantic version tags.

## [0.1.0] - 2026-06-13

### Added

- Installable Python package under `src/px4_sitl_toolkit`.
- `px4-sitl-toolkit` CLI for generating and validating scenario manifests.
- Deterministic two-UAV head-on scenario generator.
- Deterministic grid/swarm scenario generator.
- JSON scenario manifest schema marker: `px4-sitl-toolkit.scenario/v1`.
- Example manifests under `examples/`.
- Pytest suite for generator, validation, and CLI behavior.
- Ruff linting configuration.
- GitHub Actions CI for Python 3.9, 3.10, and 3.11.
- Contributor guide, code of conduct, security policy, issue templates, and PR template.
- Maintainer automation plan and public roadmap.

### Validation

- Rejects duplicate MAVLink system IDs and PX4 instance IDs.
- Enforces MAVLink-compatible system IDs from 1 to 255.
- Rejects malformed manifests without CLI tracebacks.
- Rejects string vectors and non-list tag fields.
