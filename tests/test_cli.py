import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(PROJECT_ROOT / "src")


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = SRC_PATH + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "px4_sitl_toolkit.cli", *args],
        check=False,
        text=True,
        capture_output=True,
        env=env,
    )


def test_cli_generates_head_on_manifest_to_stdout():
    result = run_cli(
        "scenario",
        "head-on",
        "--separation",
        "60",
        "--altitude",
        "18",
        "--speed",
        "4",
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads(result.stdout)
    assert manifest["name"] == "head-on-2uav"
    assert manifest["vehicles"][0]["velocity_ned_m_s"] == [4.0, 0.0, 0.0]
    assert manifest["vehicles"][1]["velocity_ned_m_s"] == [-4.0, 0.0, 0.0]


def test_cli_writes_grid_manifest_to_file(tmp_path: Path):
    output = tmp_path / "grid.json"

    result = run_cli(
        "scenario",
        "grid",
        "--rows",
        "2",
        "--cols",
        "2",
        "--spacing",
        "20",
        "--altitude",
        "15",
        "--output",
        str(output),
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads(output.read_text())
    assert manifest["name"] == "grid-2x2"
    assert len(manifest["vehicles"]) == 4


def test_cli_generates_crossing_manifest_to_stdout():
    result = run_cli(
        "scenario",
        "crossing",
        "--separation",
        "70",
        "--altitude",
        "22",
        "--speed",
        "3.5",
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads(result.stdout)
    assert manifest["name"] == "crossing-2uav"
    assert manifest["vehicles"][0]["start_ned_m"] == [-35.0, 0.0, -22.0]
    assert manifest["vehicles"][1]["velocity_ned_m_s"] == [0.0, 3.5, 0.0]


def test_cli_validate_accepts_generated_manifest(tmp_path: Path):
    output = tmp_path / "scenario.json"
    generate = run_cli("scenario", "head-on", "--output", str(output))
    assert generate.returncode == 0, generate.stderr

    validate = run_cli("validate", str(output))

    assert validate.returncode == 0, validate.stderr
    assert "valid" in validate.stdout.lower()


def test_cli_validate_reports_malformed_manifest_without_traceback(tmp_path: Path):
    manifest = tmp_path / "bad.json"
    manifest.write_text("[]", encoding="utf-8")

    result = run_cli("validate", str(manifest))

    assert result.returncode == 2
    assert "manifest must be an object" in result.stderr
    assert "Traceback" not in result.stderr
