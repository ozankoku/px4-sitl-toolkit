# Contributor Issue Backlog

These are small, contributor-friendly issues planned for GitHub after the repository is published.

## Good first issues

1. **Add a crossing-path two-UAV scenario**
   - Add `generate_crossing_scenario()`
   - Add CLI command `px4-sitl-toolkit scenario crossing`
   - Add tests and an example manifest

2. **Add manifest schema documentation**
   - Document every field in `scenario/v1`
   - Include valid and invalid examples
   - Link from the README

3. **Improve CLI error messages**
   - Include the manifest path in validation failures
   - Add tests for unreadable files and invalid JSON

4. **Add PX4 instance environment export**
   - Generate a shell-friendly summary from a manifest
   - Keep this dependency-free and covered by tests

5. **Add a four-vehicle convergence scenario**
   - Generate vehicles approaching a common center point from four directions
   - Add safe default altitude, speed, and spacing parameters

## Help wanted issues

1. **PX4 Gazebo launch notes**
   - Map manifest fields to PX4 multi-vehicle SITL startup concepts
   - Document assumptions and tested PX4 versions

2. **MAVLink log summary prototype**
   - Read a log export and summarize observed vehicle tracks
   - Keep optional dependencies behind an extra

3. **Release workflow**
   - Add tag-based release notes
   - Validate package build artifacts in CI

## Review labels

Suggested labels when opened on GitHub:

- `good first issue`
- `help wanted`
- `documentation`
- `scenario`
- `testing`
- `maintenance`
