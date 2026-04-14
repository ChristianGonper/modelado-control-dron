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


def _vector_norm(vector: Sequence[float]) -> float:
    return sqrt(sum(float(component) * float(component) for component in vector))


def _vector_normalize(vector: Sequence[float]) -> tuple[float, float, float]:
    if len(vector) != 3:
        raise ValueError("vector must contain exactly 3 values")
    norm = _vector_norm(vector)
    if norm == 0.0:
        raise ValueError("vector norm must be non-zero")
    return (float(vector[0]) / norm, float(vector[1]) / norm, float(vector[2]) / norm)


def _vector_cross(left: Sequence[float], right: Sequence[float]) -> tuple[float, float, float]:
    if len(left) != 3 or len(right) != 3:
        raise ValueError("both vectors must contain exactly 3 values")
    lx, ly, lz = (float(component) for component in left)
    rx, ry, rz = (float(component) for component in right)
    return (
        ly * rz - lz * ry,
        lz * rx - lx * rz,
        lx * ry - ly * rx,
    )


def quaternion_shortest_error(
    desired_quaternion: Sequence[float],
    current_quaternion: Sequence[float],
) -> tuple[float, float, float, float]:
    """Return the shortest-arc quaternion error from current to desired."""

    error = normalize_quaternion(
        quaternion_multiply(desired_quaternion, quaternion_conjugate(current_quaternion))
    )
    if error[0] < 0.0:
        return tuple(-component for component in error)
    return error


def quaternion_error_vector(quaternion: Sequence[float]) -> tuple[float, float, float]:
    """Map a unit quaternion error to a rotation vector in body axes."""

    if len(quaternion) != 4:
        raise ValueError("quaternion must contain exactly 4 values")
    w, x, y, z = normalize_quaternion(quaternion)
    if w < 0.0:
        w, x, y, z = -w, -x, -y, -z
    vector_norm = sqrt(x * x + y * y + z * z)
    if vector_norm == 0.0:
        return (0.0, 0.0, 0.0)
    angle = 2.0 * atan2(vector_norm, w)
    scale = angle / vector_norm
    return (x * scale, y * scale, z * scale)


def quaternion_from_rotation_matrix(matrix: Sequence[Sequence[float]]) -> tuple[float, float, float, float]:
    """Convert a 3x3 rotation matrix to a unit quaternion."""

    if len(matrix) != 3 or any(len(row) != 3 for row in matrix):
        raise ValueError("matrix must be 3x3")
    m00 = float(matrix[0][0])
    m01 = float(matrix[0][1])
    m02 = float(matrix[0][2])
    m10 = float(matrix[1][0])
    m11 = float(matrix[1][1])
    m12 = float(matrix[1][2])
    m20 = float(matrix[2][0])
    m21 = float(matrix[2][1])
    m22 = float(matrix[2][2])
    trace = m00 + m11 + m22
    if trace > 0.0:
        scale = sqrt(trace + 1.0) * 2.0
        return normalize_quaternion(
            (
                0.25 * scale,
                (m21 - m12) / scale,
                (m02 - m20) / scale,
                (m10 - m01) / scale,
            )
        )
    if m00 >= m11 and m00 >= m22:
        scale = sqrt(1.0 + m00 - m11 - m22) * 2.0
        return normalize_quaternion(
            (
                (m21 - m12) / scale,
                0.25 * scale,
                (m01 + m10) / scale,
                (m02 + m20) / scale,
            )
        )
    if m11 > m22:
        scale = sqrt(1.0 + m11 - m00 - m22) * 2.0
        return normalize_quaternion(
            (
                (m02 - m20) / scale,
                (m01 + m10) / scale,
                0.25 * scale,
                (m12 + m21) / scale,
            )
        )
    scale = sqrt(1.0 + m22 - m00 - m11) * 2.0
    return normalize_quaternion(
        (
            (m10 - m01) / scale,
            (m02 + m20) / scale,
            (m12 + m21) / scale,
            0.25 * scale,
        )
    )


def quaternion_from_thrust_direction_and_yaw(
    thrust_direction_world: Sequence[float],
    yaw_rad: float,
) -> tuple[float, float, float, float]:
    """Build a desired attitude from a thrust axis and a world yaw heading."""

    z_axis = _vector_normalize(thrust_direction_world)
    yaw_heading = (cos(yaw_rad), sin(yaw_rad), 0.0)
    y_axis = _vector_cross(z_axis, yaw_heading)
    if _vector_norm(y_axis) < 1e-9:
        yaw_heading = (0.0, 1.0, 0.0)
        y_axis = _vector_cross(z_axis, yaw_heading)
    y_axis = _vector_normalize(y_axis)
    x_axis = _vector_cross(y_axis, z_axis)
    return quaternion_from_rotation_matrix(
        (
            (x_axis[0], y_axis[0], z_axis[0]),
            (x_axis[1], y_axis[1], z_axis[1]),
            (x_axis[2], y_axis[2], z_axis[2]),
        )
    )


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
