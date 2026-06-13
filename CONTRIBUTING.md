# Contributing

Thanks for helping improve PX4 SITL & MAVLink Toolkit. The project is intentionally small and beginner-friendly: tests, examples, docs, and scenario manifests are all valuable contributions.

## Development setup

```bash
git clone https://github.com/ozankoku/px4-sitl-toolkit.git
cd px4-sitl-toolkit
python -m pip install -e '.[dev]'
python -m pytest
```

## Quality checks

Before opening a pull request, run:

```bash
python -m pytest
ruff check .
```

If `ruff` is not installed, install the dev extras or run:

```bash
python -m pip install ruff
```

## Good first contributions

Good first issues usually fit one of these categories:

- Add a new deterministic scenario generator
- Add or improve an example manifest under `examples/`
- Improve PX4/Gazebo setup documentation
- Add validation for a scenario edge case
- Improve CLI help text or error messages
- Add tests for existing behavior

## Pull request workflow

1. Open or claim an issue when possible.
2. Create a focused branch.
3. Add tests for behavior changes.
4. Run the quality checks.
5. Open a PR with:
   - Summary of the change
   - Test command output
   - Any PX4/Gazebo version assumptions

## Maintainer notes

The core package should stay dependency-light. Optional integrations belong behind extras such as `mavlink` or `viz` so the scenario CLI remains easy to install in CI.
