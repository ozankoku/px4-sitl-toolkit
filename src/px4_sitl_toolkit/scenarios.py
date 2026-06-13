from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

SCENARIO_SCHEMA = "px4-sitl-toolkit.scenario/v1"


class ScenarioValidationError(ValueError):
    """Raised when a scenario manifest is internally inconsistent."""


Vector3 = tuple[float, float, float]


@dataclass
class Vehicle:
    """A single PX4 vehicle instance in a reproducible SITL scenario."""

    name: str
    system_id: int
    px4_instance: int
    start_ned_m: Vector3
    velocity_ned_m_s: Vector3 = (0.0, 0.0, 0.0)
    model: str = "x500"


@dataclass
class Scenario:
    """A PX4 SITL scenario manifest with enough metadata for repeatable tests."""

    name: str
    description: str
    vehicles: list[Vehicle]
    tags: list[str] = field(default_factory=list)


def _require_positive_finite(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive finite number")
    return value


def _vector_to_list(vector: Vector3) -> list[float]:
    return [float(vector[0]), float(vector[1]), float(vector[2])]


def _require_vector(name: str, value: Any) -> Vector3:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ScenarioValidationError(f"{name} must be a list of three numbers")
    if len(value) != 3:
        raise ScenarioValidationError(f"{name} must contain exactly three values")
    try:
        vector = (float(value[0]), float(value[1]), float(value[2]))
    except (TypeError, ValueError) as exc:
        raise ScenarioValidationError(f"{name} must contain numeric values") from exc
    if not all(math.isfinite(component) for component in vector):
        raise ScenarioValidationError(f"{name} must contain finite values")
    return vector


def generate_head_on_scenario(
    separation_m: float = 100.0,
    altitude_m: float = 20.0,
    speed_m_s: float = 5.0,
) -> Scenario:
    """Generate a deterministic two-UAV head-on encounter scenario.

    The vehicles start on opposite sides of the local NED origin and fly toward
    each other along the north axis. This is useful as a minimal regression case
    for collision-avoidance, communication, and swarm-deconfliction logic.
    """

    separation_m = _require_positive_finite("separation_m", separation_m)
    altitude_m = _require_positive_finite("altitude_m", altitude_m)
    speed_m_s = _require_positive_finite("speed_m_s", speed_m_s)
    half = separation_m / 2.0

    scenario = Scenario(
        name="head-on-2uav",
        description="Two PX4 vehicles start symmetrically and fly toward each other.",
        tags=["px4", "sitl", "collision-avoidance", "regression"],
        vehicles=[
            Vehicle(
                name="uav-1",
                system_id=1,
                px4_instance=0,
                start_ned_m=(-half, 0.0, -altitude_m),
                velocity_ned_m_s=(speed_m_s, 0.0, 0.0),
            ),
            Vehicle(
                name="uav-2",
                system_id=2,
                px4_instance=1,
                start_ned_m=(half, 0.0, -altitude_m),
                velocity_ned_m_s=(-speed_m_s, 0.0, 0.0),
            ),
        ],
    )
    validate_scenario(scenario)
    return scenario


def generate_grid_scenario(
    rows: int,
    cols: int,
    spacing_m: float = 20.0,
    altitude_m: float = 20.0,
) -> Scenario:
    """Generate a grid of stationary PX4 vehicles for swarm setup tests."""

    if rows <= 0:
        raise ValueError("rows must be greater than zero")
    if cols <= 0:
        raise ValueError("cols must be greater than zero")
    spacing_m = _require_positive_finite("spacing_m", spacing_m)
    altitude_m = _require_positive_finite("altitude_m", altitude_m)

    vehicles: list[Vehicle] = []
    for row in range(rows):
        for col in range(cols):
            instance = row * cols + col
            vehicles.append(
                Vehicle(
                    name=f"uav-{instance + 1}",
                    system_id=instance + 1,
                    px4_instance=instance,
                    start_ned_m=(row * spacing_m, col * spacing_m, -altitude_m),
                )
            )

    scenario = Scenario(
        name=f"grid-{rows}x{cols}",
        description=f"{rows} by {cols} PX4 vehicle grid for repeatable swarm setup tests.",
        tags=["px4", "sitl", "swarm", "grid"],
        vehicles=vehicles,
    )
    validate_scenario(scenario)
    return scenario


def validate_scenario(scenario: Scenario) -> None:
    """Validate a scenario before writing it to disk or using it in CI."""

    if not scenario.name.strip():
        raise ScenarioValidationError("scenario name is required")
    if not scenario.vehicles:
        raise ScenarioValidationError("scenario must include at least one vehicle")

    seen_system_ids: set[int] = set()
    seen_instances: set[int] = set()
    for vehicle in scenario.vehicles:
        if vehicle.system_id in seen_system_ids:
            raise ScenarioValidationError(f"duplicate system_id: {vehicle.system_id}")
        if vehicle.px4_instance in seen_instances:
            raise ScenarioValidationError(f"duplicate px4_instance: {vehicle.px4_instance}")
        if not 1 <= vehicle.system_id <= 255:
            raise ScenarioValidationError("system_id must be between 1 and 255")
        if vehicle.px4_instance < 0:
            raise ScenarioValidationError("px4_instance must be zero or greater")
        for field_name, vector in {
            "start_ned_m": vehicle.start_ned_m,
            "velocity_ned_m_s": vehicle.velocity_ned_m_s,
        }.items():
            _require_vector(field_name, vector)
        seen_system_ids.add(vehicle.system_id)
        seen_instances.add(vehicle.px4_instance)


def scenario_to_dict(scenario: Scenario) -> dict[str, Any]:
    """Convert a scenario to a stable JSON/YAML-compatible manifest."""

    validate_scenario(scenario)
    return {
        "schema": SCENARIO_SCHEMA,
        "name": scenario.name,
        "description": scenario.description,
        "tags": list(scenario.tags),
        "vehicles": [
            {
                "name": vehicle.name,
                "system_id": vehicle.system_id,
                "px4_instance": vehicle.px4_instance,
                "model": vehicle.model,
                "start_ned_m": _vector_to_list(vehicle.start_ned_m),
                "velocity_ned_m_s": _vector_to_list(vehicle.velocity_ned_m_s),
            }
            for vehicle in scenario.vehicles
        ],
    }


def scenario_from_dict(manifest: dict[str, Any]) -> Scenario:
    """Load a scenario from a manifest dictionary and validate it."""

    if not isinstance(manifest, Mapping):
        raise ScenarioValidationError("manifest must be an object")
    if manifest.get("schema") != SCENARIO_SCHEMA:
        raise ScenarioValidationError(f"unsupported schema: {manifest.get('schema')!r}")

    vehicle_items = manifest.get("vehicles")
    if not isinstance(vehicle_items, list):
        raise ScenarioValidationError("vehicles must be a list")

    vehicles: list[Vehicle] = []
    for index, item in enumerate(vehicle_items):
        if not isinstance(item, Mapping):
            raise ScenarioValidationError(f"vehicle {index} must be an object")
        for field_name in ("name", "system_id", "px4_instance", "start_ned_m"):
            if field_name not in item:
                raise ScenarioValidationError(
                    f"vehicle {index} missing required field: {field_name}"
                )
        try:
            system_id = int(item["system_id"])
            px4_instance = int(item["px4_instance"])
        except (TypeError, ValueError) as exc:
            raise ScenarioValidationError(
                f"vehicle {index} system_id and px4_instance must be integers"
            ) from exc

        vehicles.append(
            Vehicle(
                name=str(item["name"]),
                system_id=system_id,
                px4_instance=px4_instance,
                model=str(item.get("model", "x500")),
                start_ned_m=_require_vector("start_ned_m", item["start_ned_m"]),
                velocity_ned_m_s=_require_vector(
                    "velocity_ned_m_s",
                    item.get("velocity_ned_m_s", [0, 0, 0]),
                ),
            )
        )

    tags = manifest.get("tags", [])
    if not isinstance(tags, list):
        raise ScenarioValidationError("tags must be a list")

    scenario = Scenario(
        name=str(manifest.get("name", "")),
        description=str(manifest.get("description", "")),
        tags=[str(tag) for tag in tags],
        vehicles=vehicles,
    )
    validate_scenario(scenario)
    return scenario
