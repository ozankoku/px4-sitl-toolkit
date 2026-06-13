# Security Policy

## Supported versions

This project is in early alpha. Security fixes are accepted on the `main` branch and will be included in the next tagged release.

## Reporting a vulnerability

Please do not publish exploit details in a public issue before the maintainer has had time to review. Open a GitHub security advisory if available, or contact the repository maintainer through GitHub.

## Scope

In scope:

- Unsafe command generation
- Manifest parsing bugs that could lead to unsafe file access
- CI or release workflow issues
- Dependency vulnerabilities in optional extras

Out of scope:

- Vulnerabilities in PX4, Gazebo, MAVLink, or pymavlink themselves unless this toolkit directly introduces the risk
- Attacks requiring access to a developer's local machine or flight controller credentials
