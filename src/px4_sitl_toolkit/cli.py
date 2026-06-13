from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from .scenarios import (
    ScenarioValidationError,
    generate_grid_scenario,
    generate_head_on_scenario,
    scenario_from_dict,
    scenario_to_dict,
)


def _write_manifest(manifest: dict, output: str | None) -> None:
    rendered = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if output:
        Path(output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="px4-sitl-toolkit",
        description="Generate and validate reproducible PX4 SITL scenario manifests.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    scenario = subcommands.add_parser("scenario", help="Generate scenario manifests")
    scenario_commands = scenario.add_subparsers(dest="scenario_command", required=True)

    head_on = scenario_commands.add_parser(
        "head-on",
        help="Generate a two-UAV head-on scenario",
    )
    head_on.add_argument(
        "--separation",
        type=float,
        default=100.0,
        help="Start separation in metres",
    )
    head_on.add_argument(
        "--altitude",
        type=float,
        default=20.0,
        help="Altitude above origin in metres",
    )
    head_on.add_argument(
        "--speed",
        type=float,
        default=5.0,
        help="Closing speed per vehicle in m/s",
    )
    head_on.add_argument("--output", help="Write JSON manifest to this path instead of stdout")

    grid = scenario_commands.add_parser("grid", help="Generate a stationary swarm grid")
    grid.add_argument("--rows", type=int, required=True, help="Number of grid rows")
    grid.add_argument("--cols", type=int, required=True, help="Number of grid columns")
    grid.add_argument("--spacing", type=float, default=20.0, help="Grid spacing in metres")
    grid.add_argument(
        "--altitude",
        type=float,
        default=20.0,
        help="Altitude above origin in metres",
    )
    grid.add_argument("--output", help="Write JSON manifest to this path instead of stdout")

    validate = subcommands.add_parser("validate", help="Validate a scenario JSON manifest")
    validate.add_argument("manifest", help="Path to a scenario JSON manifest")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "scenario" and args.scenario_command == "head-on":
            scenario = generate_head_on_scenario(
                separation_m=args.separation,
                altitude_m=args.altitude,
                speed_m_s=args.speed,
            )
            _write_manifest(scenario_to_dict(scenario), args.output)
            return 0

        if args.command == "scenario" and args.scenario_command == "grid":
            scenario = generate_grid_scenario(
                rows=args.rows,
                cols=args.cols,
                spacing_m=args.spacing,
                altitude_m=args.altitude,
            )
            _write_manifest(scenario_to_dict(scenario), args.output)
            return 0

        if args.command == "validate":
            manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
            scenario = scenario_from_dict(manifest)
            print(f"valid: {scenario.name} ({len(scenario.vehicles)} vehicle(s))")
            return 0
    except (OSError, json.JSONDecodeError, ValueError, ScenarioValidationError) as exc:
        parser.exit(2, f"error: {exc}\n")

    parser.error("unknown command")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
