import json
import math

import pytest

from px4_sitl_toolkit.scenarios import (
    Scenario,
    ScenarioValidationError,
    Vehicle,
    generate_crossing_scenario,
    generate_grid_scenario,
    generate_head_on_scenario,
    scenario_to_dict,
    validate_scenario,
)


def test_head_on_scenario_places_two_vehicles_symmetrically():
    scenario = generate_head_on_scenario(separation_m=80, altitude_m=25, speed_m_s=6)

    assert scenario.name == "head-on-2uav"
    assert len(scenario.vehicles) == 2
    assert scenario.vehicles[0].start_ned_m == (-40.0, 0.0, -25.0)
    assert scenario.vehicles[1].start_ned_m == (40.0, 0.0, -25.0)
    assert scenario.vehicles[0].velocity_ned_m_s == (6.0, 0.0, 0.0)
    assert scenario.vehicles[1].velocity_ned_m_s == (-6.0, 0.0, 0.0)


def test_grid_scenario_uses_unique_system_ids_and_spacing():
    scenario = generate_grid_scenario(rows=2, cols=3, spacing_m=15, altitude_m=12)

    assert len(scenario.vehicles) == 6
    assert [v.system_id for v in scenario.vehicles] == [1, 2, 3, 4, 5, 6]
    assert scenario.vehicles[0].start_ned_m == (0.0, 0.0, -12.0)
    assert scenario.vehicles[-1].start_ned_m == (15.0, 30.0, -12.0)


def test_crossing_scenario_places_two_vehicles_on_perpendicular_paths():
    scenario = generate_crossing_scenario(separation_m=80, altitude_m=30, speed_m_s=4)

    assert scenario.name == "crossing-2uav"
    assert len(scenario.vehicles) == 2
    assert scenario.vehicles[0].start_ned_m == (-40.0, 0.0, -30.0)
    assert scenario.vehicles[1].start_ned_m == (0.0, -40.0, -30.0)
    assert scenario.vehicles[0].velocity_ned_m_s == (4.0, 0.0, 0.0)
    assert scenario.vehicles[1].velocity_ned_m_s == (0.0, 4.0, 0.0)
    assert "crossing" in scenario.tags


def test_validate_scenario_rejects_duplicate_system_ids():
    scenario = generate_head_on_scenario()
    scenario.vehicles[1].system_id = scenario.vehicles[0].system_id

    with pytest.raises(ScenarioValidationError, match="duplicate system_id"):
        validate_scenario(scenario)


def test_scenario_dict_is_json_serializable_manifest():
    scenario = generate_head_on_scenario(separation_m=50, altitude_m=10, speed_m_s=3)
    manifest = scenario_to_dict(scenario)

    encoded = json.dumps(manifest, sort_keys=True)
    decoded = json.loads(encoded)

    assert decoded["schema"] == "px4-sitl-toolkit.scenario/v1"
    assert decoded["vehicles"][0]["px4_instance"] == 0
    assert decoded["vehicles"][1]["start_ned_m"] == [25.0, 0.0, -10.0]


def test_invalid_head_on_parameters_fail_fast():
    with pytest.raises(ValueError, match="separation_m"):
        generate_head_on_scenario(separation_m=0)
    with pytest.raises(ValueError, match="altitude_m"):
        generate_head_on_scenario(altitude_m=-1)
    with pytest.raises(ValueError, match="speed_m_s"):
        generate_head_on_scenario(speed_m_s=math.nan)


def test_scenario_from_dict_rejects_malformed_manifest_without_traceback():
    from px4_sitl_toolkit.scenarios import scenario_from_dict

    with pytest.raises(ScenarioValidationError, match="manifest must be an object"):
        scenario_from_dict([])  # type: ignore[arg-type]

    with pytest.raises(ScenarioValidationError, match="vehicles must be a list"):
        scenario_from_dict(
            {
                "schema": "px4-sitl-toolkit.scenario/v1",
                "name": "bad",
                "description": "bad",
                "vehicles": None,
            }
        )

    with pytest.raises(ScenarioValidationError, match="missing required field: name"):
        scenario_from_dict(
            {
                "schema": "px4-sitl-toolkit.scenario/v1",
                "name": "bad",
                "description": "bad",
                "vehicles": [
                    {
                        "system_id": 1,
                        "px4_instance": 0,
                        "start_ned_m": [0, 0, -10],
                    }
                ],
            }
        )


def test_scenario_from_dict_rejects_string_vectors_and_mavlink_id_overflow():
    from px4_sitl_toolkit.scenarios import scenario_from_dict

    base_manifest = scenario_to_dict(generate_head_on_scenario())
    base_manifest["vehicles"][0]["start_ned_m"] = "123"

    with pytest.raises(ScenarioValidationError, match="start_ned_m must be a list"):
        scenario_from_dict(base_manifest)

    overflow_manifest = scenario_to_dict(generate_head_on_scenario())
    overflow_manifest["vehicles"][0]["system_id"] = 256

    with pytest.raises(ScenarioValidationError, match="system_id must be between 1 and 255"):
        scenario_from_dict(overflow_manifest)


def test_validate_scenario_rejects_string_vectors_directly():
    scenario = Scenario(
        name="bad-vector",
        description="invalid direct construction",
        vehicles=[
            Vehicle(
                name="uav-1",
                system_id=1,
                px4_instance=0,
                start_ned_m="123",  # type: ignore[arg-type]
            )
        ],
    )

    with pytest.raises(ScenarioValidationError, match="start_ned_m must be a list"):
        validate_scenario(scenario)


def test_scenario_from_dict_rejects_non_list_tags():
    from px4_sitl_toolkit.scenarios import scenario_from_dict

    manifest = scenario_to_dict(generate_head_on_scenario())
    manifest["tags"] = None

    with pytest.raises(ScenarioValidationError, match="tags must be a list"):
        scenario_from_dict(manifest)
