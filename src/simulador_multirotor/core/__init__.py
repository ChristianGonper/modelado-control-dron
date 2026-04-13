"""Core contracts shared across the simulator."""

from .attitude import (
    euler_from_quaternion,
    normalize_quaternion,
    quaternion_conjugate,
    quaternion_from_euler,
    quaternion_multiply,
    rotate_vector_by_quaternion,
)
from .contracts import TrajectoryReference, VehicleCommand, VehicleObservation, VehicleState

__all__ = [
    "TrajectoryReference",
    "VehicleCommand",
    "VehicleObservation",
    "VehicleState",
    "euler_from_quaternion",
    "normalize_quaternion",
    "quaternion_conjugate",
    "quaternion_from_euler",
    "quaternion_multiply",
    "rotate_vector_by_quaternion",
]
