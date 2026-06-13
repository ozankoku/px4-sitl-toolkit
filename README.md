# PX4 SITL & MAVLink Toolkit

[![CI](https://github.com/ozankoku/px4-sitl-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/ozankoku/px4-sitl-toolkit/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/ozankoku/px4-sitl-toolkit)](LICENSE)
[![Release](https://img.shields.io/github/v/tag/ozankoku/px4-sitl-toolkit?label=release)](https://github.com/ozankoku/px4-sitl-toolkit/releases/tag/v0.1.0)

Python tools for creating reproducible PX4 Software-In-The-Loop (SITL) and MAVLink experiment scenarios.

The project is aimed at students, robotics researchers, and maintainers who need small, repeatable scenario manifests for UAV simulation, swarm setup checks, communication experiments, and collision-avoidance regression tests.

> Status: early alpha. The scenario-manifest CLI is stable enough for examples and CI; the legacy `simulation/` helpers remain available for MAVLink/UART bridge experiments.

## Why this exists

PX4 SITL experiments are often described in notebooks, shell history, or one-off scripts. That makes it hard to reproduce a scenario, compare results, or onboard contributors. This toolkit defines scenario manifests that can be generated, committed, validated in CI, and shared with collaborators.

## Features

- Generate deterministic PX4 scenario manifests as JSON
- Validate scenario manifests before using them in simulations or CI
- Built-in head-on two-UAV regression scenario
- Built-in perpendicular crossing two-UAV scenario
- Built-in grid/swarm setup scenario
- Zero runtime dependencies for the core CLI
- Optional legacy helpers for MAVLink hardware/SITL bridging and visualization

## Installation

From a local checkout:

```bash
python -m pip install -e .
```

For development:

```bash
python -m pip install -e '.[dev]'
python -m pytest
```

Optional extras:

```bash
python -m pip install -e '.[mavlink]'  # pymavlink helpers
python -m pip install -e '.[viz]'      # plotting/GIF helpers
```

## Quick start

Generate a two-UAV head-on scenario:

```bash
px4-sitl-toolkit scenario head-on --separation 80 --altitude 25 --speed 6
```

Generate a perpendicular crossing scenario:

```bash
px4-sitl-toolkit scenario crossing --separation 80 --altitude 25 --speed 5
```

For `crossing`, `--separation` is the axis span: each vehicle starts half that distance from the crossing point.

Write a grid scenario to disk:

```bash
px4-sitl-toolkit scenario grid --rows 2 --cols 3 --spacing 15 --altitude 12 --output examples/grid-2x3.json
```

Validate a manifest:

```bash
px4-sitl-toolkit validate examples/head-on-2uav.json
```

## Manifest example

```json
{
  "schema": "px4-sitl-toolkit.scenario/v1",
  "name": "head-on-2uav",
  "description": "Two PX4 vehicles start symmetrically and fly toward each other.",
  "tags": ["px4", "sitl", "collision-avoidance", "regression"],
  "vehicles": [
    {
      "name": "uav-1",
      "system_id": 1,
      "px4_instance": 0,
      "model": "x500",
      "start_ned_m": [-40.0, 0.0, -25.0],
      "velocity_ned_m_s": [6.0, 0.0, 0.0]
    },
    {
      "name": "uav-2",
      "system_id": 2,
      "px4_instance": 1,
      "model": "x500",
      "start_ned_m": [40.0, 0.0, -25.0],
      "velocity_ned_m_s": [-6.0, 0.0, 0.0]
    }
  ]
}
```

## Python API

```python
from px4_sitl_toolkit import generate_head_on_scenario, scenario_to_dict

scenario = generate_head_on_scenario(separation_m=80, altitude_m=25, speed_m_s=6)
manifest = scenario_to_dict(scenario)
```

## Repository layout

- `src/px4_sitl_toolkit/` — installable Python package and CLI
- `tests/` — pytest suite for scenario generation and validation
- `examples/` — generated scenario manifests
- `simulation/` — legacy MAVLink/UART and visualization helper scripts
- `docs/` — notes for PX4 SITL and hybrid simulation workflows

## Roadmap

- PX4 launch-command generation from manifests
- Gazebo world/model templates for generated scenarios
- MAVLink log ingestion for scenario replay
- GitHub Action examples for scenario validation in CI
- Contributor-friendly issues for docs, examples, and test scenarios

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, test commands, issue labels, and contribution workflow.

## License

Apache-2.0. See [LICENSE](LICENSE).
