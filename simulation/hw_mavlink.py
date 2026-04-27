#!/usr/bin/env python
"""hw_mavlink.py — MAVLink hardware interface helpers.

Provides connection setup, message-interval configuration, and velocity
command helpers extracted from sim_main.py.

Constants:
  MAVLINK_CONNECTION_SITL      — UDP endpoint for ArduPilot SITL (default port).
  MAVLINK_CONNECTION_HARDWARE  — Serial endpoint for hardware flight controller.
  SIM_LOOP_FREQUENCY           — Simulation / control loop rate in Hz.
"""

import time

from pymavlink import mavutil


MAVLINK_CONNECTION_SITL     = "udpin:127.0.0.1:14551"
MAVLINK_CONNECTION_HARDWARE = "/dev/ttyUSB0:921600"
SIM_LOOP_FREQUENCY          = 10  # Hz


def connect(connection_string: str, source_system: int = 254):
    """Connect to a MAVLink endpoint and wait for the first heartbeat.

    Asserts MAVLink 2.0, then requests LOCAL_POSITION_NED at
    SIM_LOOP_FREQUENCY before returning.

    Args:
        connection_string: MAVLink connection string, e.g.
            'udpin:127.0.0.1:14551' or '/dev/ttyUSB0:921600'.
        source_system: MAVLink source system ID (default 254 = GCS).

    Returns:
        An open mavutil connection object with target_system set.
    """
    print(f"Connecting to MAVLink endpoint: {connection_string}")
    the_connection = mavutil.mavlink_connection(
        connection_string, autoreconnect=True, source_system=source_system
    )
    the_connection.wait_heartbeat()
    print(
        f"Heartbeat received from system {the_connection.target_system}, "
        f"component {the_connection.target_component}"
    )
    assert the_connection.WIRE_PROTOCOL_VERSION == '2.0', (
        "MAVLink 2.0 required but connection is using "
        f"{the_connection.WIRE_PROTOCOL_VERSION}"
    )
    print("--- Connection Established ---")
    request_message_interval(
        the_connection, mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED,
        SIM_LOOP_FREQUENCY
    )
    return the_connection


def request_message_interval(connection, message_id: int, frequency_hz: float):
    """Request a MAVLink message to be streamed at a given frequency.

    Sends MAV_CMD_SET_MESSAGE_INTERVAL to the connected flight controller.

    Args:
        connection: Open mavutil connection object.
        message_id: MAVLink message ID to stream (e.g.
            mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED).
        frequency_hz: Desired stream rate in Hz.
    """
    if connection and connection.target_system != 0:
        connection.mav.command_long_send(
            connection.target_system, connection.target_component,
            mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
            message_id, int(1e6 / frequency_hz),
            0, 0, 0, 0, 0
        )


def send_local_velocity_target(connection, vx: float, vy: float, vz: float):
    """Send a SET_POSITION_TARGET_LOCAL_NED velocity command.

    All position and acceleration fields are ignored; only the velocity
    components are used by the flight controller.

    Args:
        connection: Open mavutil connection object.
        vx: Velocity North in m/s (NED frame).
        vy: Velocity East  in m/s (NED frame).
        vz: Velocity Down  in m/s (NED frame, positive = downward).
    """
    ignore_all_except_velocity = 3527
    if connection and connection.target_system != 0:
        connection.mav.set_position_target_local_ned_send(
            0, connection.target_system, connection.target_component,
            mavutil.mavlink.MAV_FRAME_LOCAL_NED, ignore_all_except_velocity,
            0, 0, 0, vx, vy, vz, 0, 0, 0, 0, 0
        )


def send_hover(connection):
    """Command the drone to hover by sending three consecutive zero-velocity targets.

    Sends the hover command three times with short delays to ensure the
    flight controller receives and acts on the stop command.

    Args:
        connection: Open mavutil connection object.
    """
    for _ in range(3):
        send_local_velocity_target(connection, 0, 0, 0)
        time.sleep(0.05)
