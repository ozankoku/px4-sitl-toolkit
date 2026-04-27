# PX4 SITL & MAVLink Toolkit

A robust infrastructure toolkit for hybrid Hardware-In-The-Loop (HITL) and Software-In-The-Loop (SITL) simulations in the PX4/Pixhawk ecosystem. 

This repository provides the "plumbing" necessary to route MAVLink telemetry between physical serial ports (UART) and virtual UDP streams, allowing researchers to seamlessly test multi-drone or swarm logic.

## Features
- **Hardware-to-SITL Bridging:** Read MAVLink data from physical flight controllers (e.g., Pixhawk 6C) and broadcast it to virtual simulated environments.
- **UDP Relays:** Clean utilities for routing high-frequency telemetry.
- **Visualization:** Tools to generate coordinate mapping and GIFs from SITL test data.
- **Hybrid Setup Guides:** Comprehensive documentation on configuring complex UART/SITL hybrid testing environments.

## License
This project is licensed under the GPLv3 License.