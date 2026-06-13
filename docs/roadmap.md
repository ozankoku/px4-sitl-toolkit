# Roadmap

## v0.1.x — Scenario manifest foundation

- [x] Installable Python package
- [x] `px4-sitl-toolkit` CLI
- [x] Head-on two-UAV manifest generator
- [x] Grid/swarm manifest generator
- [x] JSON manifest validation
- [x] CI for tests, linting, and example validation

## v0.2.x — PX4 launch integration

- [ ] Generate PX4 instance environment variables from manifests
- [ ] Generate shell snippets for multi-vehicle SITL startup
- [ ] Document Gazebo model assumptions
- [ ] Add examples for four-vehicle crossing scenarios

## v0.3.x — Replay and evaluation

- [ ] Import MAVLink logs into scenario summaries
- [ ] Compare expected vs observed NED tracks
- [ ] Generate simple report artifacts for CI

## Contribution priorities

The best first contributions are deterministic scenarios with clear acceptance criteria and tests. See `CONTRIBUTING.md` for setup details.
