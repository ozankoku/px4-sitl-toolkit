"""Utilities for reproducible PX4 SITL scenario manifests."""

from .scenarios import (
    Scenario,
    ScenarioValidationError,
    Vehicle,
    generate_grid_scenario,
    generate_head_on_scenario,
    scenario_from_dict,
    scenario_to_dict,
    validate_scenario,
)

__all__ = [
    "Scenario",
    "ScenarioValidationError",
    "Vehicle",
    "generate_grid_scenario",
    "generate_head_on_scenario",
    "scenario_from_dict",
    "scenario_to_dict",
    "validate_scenario",
]

__version__ = "0.1.0"
