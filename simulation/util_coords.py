#!/usr/bin/env python
"""util_coords.py — Coordinate conversion utilities for SkyBeacon.

Provides flat-Earth approximation helpers for converting GPS coordinates to
local North-East-Down (NED) offsets relative to an own-drone reference point.
"""

import numpy as np


EARTH_RADIUS_M = 6371000.0


def latlon_to_ned(
    own_lat: float, own_lon: float,
    nbr_lat: float, nbr_lon: float,
    nbr_alt_m: float, own_alt_m: float
) -> np.ndarray:
    """Convert a neighbour's GPS position to NED offset relative to own drone.

    Uses a flat-Earth (equirectangular) approximation, valid for separations
    up to a few kilometres.

    Args:
        own_lat:   Own drone latitude  in decimal degrees.
        own_lon:   Own drone longitude in decimal degrees.
        nbr_lat:   Neighbour latitude  in decimal degrees.
        nbr_lon:   Neighbour longitude in decimal degrees.
        nbr_alt_m: Neighbour altitude  in metres (above reference datum).
        own_alt_m: Own drone altitude  in metres (above reference datum).

    Returns:
        np.ndarray of shape (3,) containing [north_m, east_m, down_m].
    """
    d_lat = np.radians(nbr_lat - own_lat)
    d_lon = np.radians(nbr_lon - own_lon)
    lat_ref = np.radians(own_lat)

    north_m = d_lat * EARTH_RADIUS_M
    east_m  = d_lon * EARTH_RADIUS_M * np.cos(lat_ref)
    down_m  = -(nbr_alt_m - own_alt_m)   # NED: positive down

    return np.array([north_m, east_m, down_m])
