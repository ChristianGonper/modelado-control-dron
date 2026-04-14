"""Quaternion and attitude helpers shared by dynamics and control."""

from __future__ import annotations

from math import asin, atan2, copysign, cos, isfinite, pi, sin, sqrt
from typing import Sequence


def normalize_quaternion(quaternion: Sequence[float]) -> tuple[float, float, float, float]:
    if len(quaternion) != 4:
        raise ValueError("quaternion must contain exactly 4 values")
    w, x, y, z = (float(component) for component in quaternion)
    norm = sqrt(w * w + x * x + y * y + z * z)
    if norm == 0.0:
        raise ValueError("quaternion norm must be non-zero")
    return (w / norm, x / norm, y / norm, z / norm)


def quaternion_conjugate(quaternion: Sequence[float]) -> tuple[float, float, float, float]:
    w, x, y, z = normalize_quaternion(quaternion)
    return (w, -x, -y, -z)


def quaternion_multiply(
    left: Sequence[float],
    right: Sequence[float],
) -> tuple[float, float, float, float]:
    if len(left) != 4 or len(right) != 4:
        raise ValueError("both quaternions must contain exactly 4 values")
    lw, lx, ly, lz = (float(component) for component in left)
    rw, rx, ry, rz = (float(component) for component in right)
    return (
        lw * rw - lx * rx - ly * ry - lz * rz,
        lw * rx + lx * rw + ly * rz - lz * ry,
        lw * ry - lx * rz + ly * rw + lz * rx,
        lw * rz + lx * ry - ly * rx + lz * rw,
    )


def quaternion_derivative(
    quaternion: Sequence[float],
    angular_velocity_rad_s: Sequence[float],
) -> tuple[float, float, float, float]:
    if len(angular_velocity_rad_s) != 3:
        raise ValueError("angular_velocity_rad_s must contain exactly 3 values")
    w, x, y, z = normalize_quaternion(quaternion)
    omega_quaternion = (
        0.0,
        float(angular_velocity_rad_s[0]),
        float(angular_velocity_rad_s[1]),
        float(angular_velocity_rad_s[2]),
    )
    q_dot = quaternion_multiply((w, x, y, z), omega_quaternion)
    return tuple(0.5 * component for component in q_dot)


def quaternion_increment_from_angular_velocity(
    angular_velocity_rad_s: Sequence[float],
    dt_s: float,
) -> tuple[float, float, float, float]:
    if len(angular_velocity_rad_s) != 3:
        raise ValueError("angular_velocity_rad_s must contain exactly 3 values")
    dt = float(dt_s)
    if not isfinite(dt):
        raise ValueError("dt_s must be finite")
    omega_x = float(angular_velocity_rad_s[0])
    omega_y = float(angular_velocity_rad_s[1])
    omega_z = float(angular_velocity_rad_s[2])
    omega_norm = sqrt(omega_x * omega_x + omega_y * omega_y + omega_z * omega_z)
    if omega_norm == 0.0 or dt == 0.0:
        return (1.0, 0.0, 0.0, 0.0)
    half_angle = 0.5 * omega_norm * dt
    scale = sin(half_angle) / omega_norm
    return normalize_quaternion(
        (
            cos(half_angle),
            omega_x * scale,
            omega_y * scale,
            omega_z * scale,
        )
    )


def quaternion_from_euler(
    roll_rad: float,
    pitch_rad: float,
    yaw_rad: float,
) -> tuple[float, float, float, float]:
    cr = cos(roll_rad * 0.5)
    sr = sin(roll_rad * 0.5)
    cp = cos(pitch_rad * 0.5)
    sp = sin(pitch_rad * 0.5)
    cy = cos(yaw_rad * 0.5)
    sy = sin(yaw_rad * 0.5)
    return normalize_quaternion(
        (
            cr * cp * cy + sr * sp * sy,
            sr * cp * cy - cr * sp * sy,
            cr * sp * cy + sr * cp * sy,
            cr * cp * sy - sr * sp * cy,
        )
    )


def euler_from_quaternion(quaternion: Sequence[float]) -> tuple[float, float, float]:
    w, x, y, z = normalize_quaternion(quaternion)

    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    roll = atan2(sinr_cosp, cosr_cosp)

    sinp = 2.0 * (w * y - z * x)
    if abs(sinp) >= 1.0:
        pitch = copysign(pi / 2.0, sinp)
    else:
        pitch = asin(sinp)

    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    yaw = atan2(siny_cosp, cosy_cosp)
    return roll, pitch, yaw


def rotate_vector_by_quaternion(
    quaternion: Sequence[float],
    vector: Sequence[float],
) -> tuple[float, float, float]:
    if len(vector) != 3:
        raise ValueError("vector must contain exactly 3 values")
    q = normalize_quaternion(quaternion)
    v_quat = (0.0, float(vector[0]), float(vector[1]), float(vector[2]))
    rotated = quaternion_multiply(quaternion_multiply(q, v_quat), quaternion_conjugate(q))
    return (rotated[1], rotated[2], rotated[3])
