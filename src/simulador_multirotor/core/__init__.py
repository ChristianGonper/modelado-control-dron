"""Core contracts shared across the simulator."""

from .attitude import (
    euler_from_quaternion,
    quaternion_derivative,
    quaternion_increment_from_angular_velocity,
    normalize_quaternion,
    quaternion_conjugate,
    quaternion_from_euler,
    quaternion_multiply,
    rotate_vector_by_quaternion,
)
from .contracts import (
    RotorCommand,
    RotorGeometry,
    TrajectoryReference,
    VehicleCommand,
    VehicleIntent,
    VehicleObservation,
    VehicleState,
)

__all__ = [
    "TrajectoryReference",
    "RotorCommand",
    "RotorGeometry",
    "VehicleCommand",
    "VehicleIntent",
    "VehicleObservation",
    "VehicleState",
    "euler_from_quaternion",
    "normalize_quaternion",
    "quaternion_conjugate",
    "quaternion_derivative",
    "quaternion_from_euler",
    "quaternion_increment_from_angular_velocity",
    "quaternion_multiply",
    "rotate_vector_by_quaternion",
]
